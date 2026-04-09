// State
let businesses = [];
let directories = DIRECTORIES;
let submissions = [];

// --- Init ---
document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    renderDirectoryGrid();
    loadBusinesses();
    loadSubmissions();
    document.getElementById('connectionStatus').textContent = 'Online';
    document.getElementById('connectionStatus').style.color = '#86efac';
    checkServerStatus();
    loadSettings();
});

// --- Tabs ---
function initTabs() {
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            tab.classList.add('active');
            document.getElementById('tab-' + tab.dataset.tab).classList.add('active');

            if (tab.dataset.tab === 'status') loadStatusMatrix();
            if (tab.dataset.tab === 'submit') populateBusinessSelect();
        });
    });
}

// --- Businesses (Supabase) ---
async function loadBusinesses() {
    businesses = await supabase('citations_businesses', { filters: 'order=created_at.desc' });
    if (!Array.isArray(businesses)) businesses = [];
    renderBusinessList();
    populateBusinessSelect();
}

function renderBusinessList() {
    const tbody = document.getElementById('businessList');
    const empty = document.getElementById('emptyBusinesses');

    if (!businesses.length) {
        tbody.innerHTML = '';
        empty.style.display = 'block';
        return;
    }
    empty.style.display = 'none';

    tbody.innerHTML = businesses.map(b => {
        const subs = submissions.filter(s => s.business_id === b.id);
        const submitted = subs.filter(s => s.status === 'submitted').length;
        return `<tr>
            <td><strong>${esc(b.name)}</strong></td>
            <td>${esc(b.city || '')}</td>
            <td>${esc(b.phone || '')}</td>
            <td>${esc(b.category || '')}</td>
            <td><span class="badge badge-${submitted > 0 ? 'submitted' : 'pending'}">${submitted}/${directories.length}</span></td>
            <td>
                <button class="btn btn-sm btn-outline" onclick="editBusiness(${b.id})">Επεξεργασία</button>
                <button class="btn btn-sm btn-danger" onclick="deleteBusiness(${b.id})">Διαγραφή</button>
            </td>
        </tr>`;
    }).join('');
}

function showBusinessForm(id = null) {
    document.getElementById('businessForm').style.display = 'block';
    document.getElementById('formTitle').textContent = id ? 'Επεξεργασία Επιχείρησης' : 'Νέα Επιχείρηση';
    document.getElementById('editBusinessId').value = id || '';

    if (id) {
        const b = businesses.find(x => x.id === id);
        if (b) {
            const fields = ['name','name_en','address','city','city_en','postal_code','region',
                'phone','mobile','email','website','category','category_en','contact_person',
                'tax_id','hours','facebook','instagram','linkedin','description_gr','description_en'];
            fields.forEach(f => {
                const el = document.getElementById('f_' + f);
                if (el) el.value = b[f] || '';
            });
        }
    } else {
        document.querySelectorAll('#businessForm input, #businessForm textarea').forEach(el => {
            if (el.type !== 'hidden') el.value = '';
        });
    }
    document.getElementById('businessForm').scrollIntoView({ behavior: 'smooth' });
}

function hideBusinessForm() {
    document.getElementById('businessForm').style.display = 'none';
}

async function saveBusiness() {
    const fields = ['name','name_en','address','city','city_en','postal_code','region',
        'phone','mobile','email','website','category','category_en','contact_person',
        'tax_id','hours','facebook','instagram','linkedin','description_gr','description_en'];
    const data = {};
    fields.forEach(f => { data[f] = document.getElementById('f_' + f).value; });

    if (!data.name) { alert('Η επωνυμία είναι υποχρεωτική'); return; }

    const id = document.getElementById('editBusinessId').value;
    if (id) {
        await supabase('citations_businesses', { method: 'PATCH', filters: `id=eq.${id}`, body: data });
    } else {
        await supabase('citations_businesses', { method: 'POST', body: data });
    }
    hideBusinessForm();
    await loadBusinesses();
}

function editBusiness(id) { showBusinessForm(id); }

async function deleteBusiness(id) {
    if (!confirm('Διαγραφή αυτής της επιχείρησης και όλων των καταχωρήσεών της;')) return;
    await supabase('citations_submissions', { method: 'DELETE', filters: `business_id=eq.${id}` });
    await supabase('citations_businesses', { method: 'DELETE', filters: `id=eq.${id}` });
    await loadBusinesses();
    await loadSubmissions();
}

// --- CSV ---
async function importCSV(input) {
    if (!input.files.length) return;
    const text = await input.files[0].text();
    const lines = text.split('\n');
    if (lines.length < 2) { alert('Το CSV είναι κενό'); return; }

    const headers = lines[0].split(',').map(h => h.trim().toLowerCase().replace(/['"]/g, '').replace(/ /g, '_'));
    const fieldMap = {
        business_name: 'name', company_name: 'name', eponymia: 'name', name: 'name',
        name_en: 'name_en', english_name: 'name_en',
        address: 'address', dieuthinsi: 'address', street: 'address',
        city: 'city', poli: 'city', city_en: 'city_en',
        postal_code: 'postal_code', zip: 'postal_code', tk: 'postal_code',
        region: 'region', nomos: 'region',
        phone: 'phone', tilefono: 'phone', tel: 'phone',
        mobile: 'mobile', kinito: 'mobile', email: 'email',
        website: 'website', url: 'website',
        category: 'category', kategoria: 'category', category_en: 'category_en',
        description_gr: 'description_gr', perigrafi: 'description_gr',
        description_en: 'description_en',
        hours: 'hours', ores: 'hours',
        facebook: 'facebook', instagram: 'instagram', linkedin: 'linkedin',
        tax_id: 'tax_id', afm: 'tax_id', contact_person: 'contact_person',
    };
    const validFields = ['name','name_en','address','city','city_en','postal_code','region',
        'phone','mobile','email','website','category','category_en','contact_person',
        'tax_id','hours','facebook','instagram','linkedin','description_gr','description_en'];

    let imported = 0;
    for (let i = 1; i < lines.length; i++) {
        const line = lines[i].trim();
        if (!line) continue;
        const values = parseCSVLine(line);
        const row = {};
        headers.forEach((h, idx) => {
            const field = fieldMap[h] || h;
            if (validFields.includes(field)) row[field] = (values[idx] || '').trim();
        });
        if (row.name) {
            await supabase('citations_businesses', { method: 'POST', body: row });
            imported++;
        }
    }
    alert(`Εισαγωγή ${imported} επιχειρήσεων ολοκληρώθηκε`);
    input.value = '';
    await loadBusinesses();
}

function parseCSVLine(line) {
    const result = []; let current = ''; let inQuotes = false;
    for (let i = 0; i < line.length; i++) {
        const ch = line[i];
        if (ch === '"') inQuotes = !inQuotes;
        else if (ch === ',' && !inQuotes) { result.push(current); current = ''; }
        else current += ch;
    }
    result.push(current); return result;
}

function exportCSV() {
    if (!businesses.length) { alert('Δεν υπάρχουν επιχειρήσεις'); return; }
    const fields = ['name','name_en','address','city','city_en','postal_code','region',
        'phone','mobile','email','website','category','category_en',
        'description_gr','description_en','hours','facebook','instagram','linkedin','tax_id','contact_person'];
    let csv = fields.join(',') + '\n';
    businesses.forEach(b => {
        csv += fields.map(f => `"${(b[f] || '').replace(/"/g, '""')}"`).join(',') + '\n';
    });
    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' });
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob);
    a.download = 'businesses.csv'; a.click();
}

// --- Directories ---
function renderDirectoryGrid() {
    const grid = document.getElementById('directoryGrid');
    grid.innerHTML = directories.map(d => `
        <label class="dir-item" data-dir="${d.id}">
            <input type="checkbox" value="${d.id}" checked>
            <div class="dir-info">
                <div class="dir-name">${esc(d.name)}</div>
                <div class="dir-type">${esc(d.type)} &bull; ${esc(d.url)}</div>
            </div>
        </label>
    `).join('');
}

function selectAllDirs() { document.querySelectorAll('#directoryGrid input[type="checkbox"]').forEach(cb => cb.checked = true); }
function deselectAllDirs() { document.querySelectorAll('#directoryGrid input[type="checkbox"]').forEach(cb => cb.checked = false); }
function getSelectedDirs() { return [...document.querySelectorAll('#directoryGrid input[type="checkbox"]:checked')].map(cb => cb.value); }

// --- Submit tab ---
function populateBusinessSelect() {
    const sel = document.getElementById('submitBusinessSelect');
    const val = sel.value;
    sel.innerHTML = '<option value="">-- Επιλέξτε επιχείρηση --</option>' +
        businesses.map(b => `<option value="${b.id}">${esc(b.name)} - ${esc(b.city || '')}</option>`).join('');
    sel.value = val;
}

function onBusinessSelected() {}

// Status labels
const STATUS_LABELS = {
    pending: 'Εκκρεμεί', running: 'Σε εξέλιξη', waiting_human: 'Αναμονή',
    submitted: 'Υποβλήθηκε', success: 'Υποβλήθηκε', complete: 'Υποβλήθηκε', error: 'Σφάλμα',
};
function statusLabel(s) { return STATUS_LABELS[s] || s; }

// --- Directory registration URLs & field mappings ---
const DIR_REG_URLS = {
    xo_gr: 'https://www.xo.gr/dorean-katachorisi/',
    vrisko: 'https://vriskodigital.vrisko.gr/dorean-kataxorisi/',
    vres: 'https://www.vres.gr/',
    findhere: 'https://www.findhere.gr/add-business/',
    stigmap: 'https://www.stigmap.gr/',
    waze: 'https://www.waze.com/editor',
    tomtom: 'https://www.tomtom.com/mapshare/tools/',
    here: 'https://mapcreator.here.com/',
    openstreetmap: 'https://www.openstreetmap.org/',
    foursquare: 'https://foursquare.com/add-place',
    tupalo: 'https://www.tupalo.co/spot/new',
    europages: 'https://www.europages.co.uk/en/supplier-registration',
    cybo: 'https://www.cybo.com/add-business',
    infobel: 'https://www.infobelpro.com/en/promote-products/list-my-business',
    brownbook: 'https://www.brownbook.net/add-business/',
    storeboard: 'https://www.storeboard.com/register',
    yellowplace: 'https://yellow.place/en/add-place',
    showmelocal: 'https://www.showmelocal.com/CreateBusiness.aspx',
    globalcatalog: 'https://www.globalcatalog.com/add-business.html',
    twofindlocal: 'https://www.2findlocal.com/add-business',
    trustpilot: 'https://business.trustpilot.com/signup',
    citymaps: 'https://citymaps.gr/',
};

// Which fields each directory needs (for the copy panel)
const DIR_FIELDS = {
    xo_gr: [
        { label: 'Επωνυμία', key: 'name' },
        { label: 'Τηλέφωνο', key: 'phone' },
        { label: 'Κινητό', key: 'mobile' },
        { label: 'Email', key: 'email' },
        { label: 'Διεύθυνση', key: 'address' },
        { label: 'Πόλη', key: 'city' },
        { label: 'Τ.Κ.', key: 'postal_code' },
        { label: 'Website', key: 'website' },
        { label: 'Κατηγορία', key: 'category' },
        { label: 'Υπεύθυνος', key: 'contact_person' },
    ],
    vrisko: [
        { label: 'Επωνυμία', key: 'name' },
        { label: 'Τηλέφωνο', key: 'phone' },
        { label: 'Email', key: 'email' },
        { label: 'Διεύθυνση', key: 'address' },
        { label: 'Πόλη', key: 'city' },
        { label: 'Τ.Κ.', key: 'postal_code' },
        { label: 'Website', key: 'website' },
        { label: 'Κατηγορία', key: 'category' },
    ],
    europages: [
        { label: 'Company Name', key: 'name_en', fallback: 'name' },
        { label: 'Phone', key: 'phone' },
        { label: 'Email', key: 'email' },
        { label: 'Address', key: 'address' },
        { label: 'City', key: 'city_en', fallback: 'city' },
        { label: 'Zip Code', key: 'postal_code' },
        { label: 'Website', key: 'website' },
        { label: 'Description', key: 'description_en', fallback: 'description_gr' },
        { label: 'Country', key: '_static', value: 'Greece' },
    ],
    findhere: [
        { label: 'Επωνυμία', key: 'name' },
        { label: 'Τηλέφωνο', key: 'phone' },
        { label: 'Email', key: 'email' },
        { label: 'Διεύθυνση', key: 'address' },
        { label: 'Πόλη', key: 'city' },
        { label: 'Τ.Κ.', key: 'postal_code' },
        { label: 'Website', key: 'website' },
        { label: 'Κατηγορία', key: 'category' },
        { label: 'Περιγραφή', key: 'description_gr' },
    ],
    stigmap: [
        { label: 'Επωνυμία', key: 'name' },
        { label: 'Τηλέφωνο', key: 'phone' },
        { label: 'Email', key: 'email' },
        { label: 'Διεύθυνση', key: 'address' },
        { label: 'Πόλη', key: 'city' },
        { label: 'Website', key: 'website' },
        { label: 'Κατηγορία', key: 'category' },
    ],
    foursquare: [
        { label: 'Venue Name', key: 'name_en', fallback: 'name' },
        { label: 'Address', key: 'address' },
        { label: 'City', key: 'city_en', fallback: 'city' },
        { label: 'Zip', key: 'postal_code' },
        { label: 'Phone', key: 'phone' },
        { label: 'Website', key: 'website' },
        { label: 'Category', key: 'category_en', fallback: 'category' },
    ],
    tupalo: [
        { label: 'Business Name', key: 'name_en', fallback: 'name' },
        { label: 'Address', key: 'address' },
        { label: 'City', key: 'city_en', fallback: 'city' },
        { label: 'Zip', key: 'postal_code' },
        { label: 'Phone', key: 'phone' },
        { label: 'Website', key: 'website' },
        { label: 'Description', key: 'description_en', fallback: 'description_gr' },
        { label: 'Country', key: '_static', value: 'Greece' },
    ],
    cybo: [
        { label: 'Business Name', key: 'name_en', fallback: 'name' },
        { label: 'Phone', key: 'phone' },
        { label: 'Email', key: 'email' },
        { label: 'Address', key: 'address' },
        { label: 'City', key: 'city_en', fallback: 'city' },
        { label: 'Zip', key: 'postal_code' },
        { label: 'Website', key: 'website' },
        { label: 'Description', key: 'description_en', fallback: 'description_gr' },
        { label: 'Country', key: '_static', value: 'Greece' },
    ],
    infobel: [
        { label: 'Business Name', key: 'name_en', fallback: 'name' },
        { label: 'City', key: 'city_en', fallback: 'city' },
        { label: 'Phone', key: 'phone' },
    ],
    vres: [
        { label: 'Επωνυμία', key: 'name' },
        { label: 'Τηλέφωνο', key: 'phone' },
        { label: 'Email', key: 'email' },
        { label: 'Διεύθυνση', key: 'address' },
        { label: 'Πόλη', key: 'city' },
        { label: 'Website', key: 'website' },
        { label: 'Κατηγορία', key: 'category' },
    ],
    waze: [
        { label: 'Business Name', key: 'name_en', fallback: 'name' },
        { label: 'Address', key: 'address' },
        { label: 'City', key: 'city_en', fallback: 'city' },
        { label: 'Category', key: 'category_en', fallback: 'category' },
        { label: 'Country', key: '_static', value: 'Greece' },
    ],
    tomtom: [
        { label: 'Business Name', key: 'name_en', fallback: 'name' },
        { label: 'Address', key: 'address' },
        { label: 'City', key: 'city_en', fallback: 'city' },
        { label: 'Phone', key: 'phone' },
        { label: 'Website', key: 'website' },
        { label: 'Country', key: '_static', value: 'Greece' },
    ],
    here: [
        { label: 'Business Name', key: 'name_en', fallback: 'name' },
        { label: 'Address', key: 'address' },
        { label: 'City', key: 'city_en', fallback: 'city' },
        { label: 'Postal Code', key: 'postal_code' },
        { label: 'Phone', key: 'phone' },
        { label: 'Website', key: 'website' },
        { label: 'Country', key: '_static', value: 'Greece' },
    ],
    openstreetmap: [
        { label: 'Name', key: 'name_en', fallback: 'name' },
        { label: 'Address', key: 'address' },
        { label: 'City', key: 'city_en', fallback: 'city' },
        { label: 'Phone', key: 'phone' },
        { label: 'Website', key: 'website' },
        { label: 'Category', key: 'category_en', fallback: 'category' },
    ],
    brownbook: [
        { label: 'Business Name', key: 'name_en', fallback: 'name' },
        { label: 'Phone', key: 'phone' },
        { label: 'Address', key: 'address' },
        { label: 'City', key: 'city_en', fallback: 'city' },
        { label: 'Zip', key: 'postal_code' },
        { label: 'Website', key: 'website' },
        { label: 'Email', key: 'email' },
        { label: 'Description', key: 'description_en', fallback: 'description_gr' },
        { label: 'Country', key: '_static', value: 'Greece' },
    ],
    storeboard: [
        { label: 'Business Name', key: 'name_en', fallback: 'name' },
        { label: 'Phone', key: 'phone' },
        { label: 'Email', key: 'email' },
        { label: 'Address', key: 'address' },
        { label: 'City', key: 'city_en', fallback: 'city' },
        { label: 'Zip', key: 'postal_code' },
        { label: 'Website', key: 'website' },
        { label: 'Description', key: 'description_en', fallback: 'description_gr' },
        { label: 'Country', key: '_static', value: 'Greece' },
    ],
    yellowplace: [
        { label: 'Business Name', key: 'name_en', fallback: 'name' },
        { label: 'Phone', key: 'phone' },
        { label: 'Address', key: 'address' },
        { label: 'City', key: 'city_en', fallback: 'city' },
        { label: 'Zip', key: 'postal_code' },
        { label: 'Website', key: 'website' },
        { label: 'Description', key: 'description_en', fallback: 'description_gr' },
        { label: 'Country', key: '_static', value: 'Greece' },
    ],
    showmelocal: [
        { label: 'Business Name', key: 'name_en', fallback: 'name' },
        { label: 'Phone', key: 'phone' },
        { label: 'Address', key: 'address' },
        { label: 'City', key: 'city_en', fallback: 'city' },
        { label: 'Zip', key: 'postal_code' },
        { label: 'Website', key: 'website' },
        { label: 'Category', key: 'category_en', fallback: 'category' },
        { label: 'Country', key: '_static', value: 'Greece' },
    ],
    globalcatalog: [
        { label: 'Business Name', key: 'name_en', fallback: 'name' },
        { label: 'Phone', key: 'phone' },
        { label: 'Email', key: 'email' },
        { label: 'Address', key: 'address' },
        { label: 'City', key: 'city_en', fallback: 'city' },
        { label: 'Website', key: 'website' },
        { label: 'Description', key: 'description_en', fallback: 'description_gr' },
        { label: 'Country', key: '_static', value: 'Greece' },
    ],
    twofindlocal: [
        { label: 'Business Name', key: 'name_en', fallback: 'name' },
        { label: 'Phone', key: 'phone' },
        { label: 'Address', key: 'address' },
        { label: 'City', key: 'city_en', fallback: 'city' },
        { label: 'Zip', key: 'postal_code' },
        { label: 'Website', key: 'website' },
        { label: 'Category', key: 'category_en', fallback: 'category' },
        { label: 'Country', key: '_static', value: 'Greece' },
    ],
    trustpilot: [
        { label: 'Company Name', key: 'name_en', fallback: 'name' },
        { label: 'Website', key: 'website' },
        { label: 'Email', key: 'email' },
        { label: 'Phone', key: 'phone' },
    ],
    citymaps: [
        { label: 'Επωνυμία', key: 'name' },
        { label: 'Τηλέφωνο', key: 'phone' },
        { label: 'Email', key: 'email' },
        { label: 'Διεύθυνση', key: 'address' },
        { label: 'Πόλη', key: 'city' },
        { label: 'Website', key: 'website' },
        { label: 'Κατηγορία', key: 'category' },
        { label: 'Περιγραφή', key: 'description_gr' },
    ],
};

// --- Start submission workflow ---
let automationMode = 'manual'; // 'manual' or 'auto'
let sseSource = null;

function startAutomation() {
    automationMode = 'manual';
    renderSubmitCards();
}

function startAutoSubmit() {
    automationMode = 'auto';
    const businessId = document.getElementById('submitBusinessSelect').value;
    if (!businessId) { alert('Επιλέξτε πρώτα μια επιχείρηση'); return; }
    const dirs = getSelectedDirs();
    if (!dirs.length) { alert('Επιλέξτε τουλάχιστον έναν κατάλογο'); return; }

    renderSubmitCards();

    // Connect SSE for live progress
    if (sseSource) sseSource.close();
    sseSource = new EventSource(`${AUTOMATION_API}/api/events`);
    sseSource.onmessage = (e) => {
        const data = JSON.parse(e.data);
        if (data.status === 'connected') return;
        updateProgressCard(data);
    };
    sseSource.onerror = () => {
        console.warn('SSE disconnected');
    };

    // Start automation on VPS
    fetch(`${AUTOMATION_API}/api/automate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ business_id: parseInt(businessId), directories: dirs }),
    }).then(r => r.json()).then(data => {
        if (data.error) alert('Σφάλμα: ' + data.error);
    }).catch(err => {
        alert('Δεν ήταν δυνατή η σύνδεση με τον automation server.\n\nΣφάλμα: ' + err.message);
    });
}

function continueAutomation() {
    fetch(`${AUTOMATION_API}/api/automate/continue`, { method: 'POST' }).catch(() => {});
}

function updateProgressCard(data) {
    const dirId = data.directory_id;
    const badge = document.getElementById('badge-' + dirId);
    const card = document.getElementById('dircard-' + dirId);
    const msgEl = document.getElementById('msg-' + dirId);

    if (badge) {
        const statusMap = { running: 'running', waiting_human: 'waiting', success: 'submitted', error: 'error', complete: 'submitted' };
        badge.className = `badge badge-${statusMap[data.status] || 'pending'}`;
        badge.textContent = statusLabel(data.status);
    }
    if (msgEl) msgEl.textContent = data.message || '';
    if (card && (data.status === 'success' || data.status === 'complete')) card.classList.add('done');

    if (data.status === 'waiting_human' && card) {
        const actionsDiv = card.querySelector('.dir-card-actions');
        if (actionsDiv && !actionsDiv.querySelector('.continue-btn')) {
            const btn = document.createElement('button');
            btn.className = 'btn btn-sm btn-primary continue-btn';
            btn.textContent = 'Συνέχεια';
            btn.onclick = continueAutomation;
            actionsDiv.prepend(btn);
        }
    }

    if (dirId === 'all' && data.step === 'done') {
        if (sseSource) { sseSource.close(); sseSource = null; }
        loadSubmissions();
    }
}

function renderSubmitCards() {
    const businessId = document.getElementById('submitBusinessSelect').value;
    if (!businessId) { alert('Επιλέξτε πρώτα μια επιχείρηση'); return; }

    const dirs = getSelectedDirs();
    if (!dirs.length) { alert('Επιλέξτε τουλάχιστον έναν κατάλογο'); return; }

    const biz = businesses.find(b => b.id === parseInt(businessId));
    if (!biz) return;

    document.getElementById('progressCard').style.display = 'block';
    const progressList = document.getElementById('progressList');

    progressList.innerHTML = dirs.map(dirId => {
        const dir = directories.find(x => x.id === dirId);
        const dirName = dir ? dir.name : dirId;
        const regUrl = DIR_REG_URLS[dirId] || '#';
        const fields = DIR_FIELDS[dirId] || [];
        const sub = submissions.find(s => s.business_id === biz.id && s.directory_id === dirId);
        const isDone = sub && sub.status === 'submitted';

        const fieldRows = fields.map(f => {
            let val = '';
            if (f.key === '_static') {
                val = f.value;
            } else {
                val = biz[f.key] || (f.fallback ? biz[f.fallback] : '') || '';
            }
            if (!val) return '';
            return `<div class="copy-row">
                <span class="copy-label">${f.label}</span>
                <span class="copy-value" title="${esc(val)}">${esc(val)}</span>
                <button class="btn btn-sm btn-outline copy-btn" onclick="copyText('${esc(val).replace(/'/g, "\\'")}', this)">Copy</button>
            </div>`;
        }).filter(Boolean).join('');

        const autoMsg = automationMode === 'auto' ? `<div class="auto-status" id="msg-${dirId}" style="padding:8px 16px;font-size:13px;color:var(--gray-500);"></div>` : '';

        return `<div class="dir-card ${isDone ? 'done' : ''}" id="dircard-${dirId}">
            <div class="dir-card-header">
                <div>
                    <strong>${esc(dirName)}</strong>
                    <span class="badge badge-${isDone ? 'submitted' : 'pending'}" id="badge-${dirId}">${isDone ? 'Υποβλήθηκε' : 'Εκκρεμεί'}</span>
                </div>
                <div class="dir-card-actions">
                    <a href="${regUrl}" target="_blank" class="btn btn-sm btn-primary" onclick="trackOpen('${dirId}')">Άνοιγμα σελίδας &rarr;</a>
                    <button class="btn btn-sm btn-success" onclick="markSubmitted(${biz.id}, '${dirId}')">Ολοκληρώθηκε</button>
                </div>
            </div>
            ${autoMsg}
            <div class="copy-fields">${fieldRows}</div>
        </div>`;
    }).join('');

    document.getElementById('progressCard').scrollIntoView({ behavior: 'smooth' });
}

function copyText(text, btn) {
    navigator.clipboard.writeText(text).then(() => {
        const orig = btn.textContent;
        btn.textContent = 'Copied!';
        btn.classList.add('copied');
        setTimeout(() => { btn.textContent = orig; btn.classList.remove('copied'); }, 1200);
    });
}

function trackOpen(dirId) {
    const card = document.getElementById('dircard-' + dirId);
    if (card) card.classList.add('opened');
}

async function markSubmitted(businessId, dirId) {
    // Upsert submission in Supabase
    const existing = await supabase('citations_submissions', {
        filters: `business_id=eq.${businessId}&directory_id=eq.${dirId}`
    });

    if (existing && existing.length) {
        await supabase('citations_submissions', {
            method: 'PATCH',
            filters: `business_id=eq.${businessId}&directory_id=eq.${dirId}`,
            body: { status: 'submitted', notes: 'Manually submitted', submitted_at: new Date().toISOString() },
        });
    } else {
        await supabase('citations_submissions', {
            method: 'POST',
            body: { business_id: businessId, directory_id: dirId, status: 'submitted', notes: 'Manually submitted', submitted_at: new Date().toISOString() },
        });
    }

    // Update UI
    const badge = document.getElementById('badge-' + dirId);
    if (badge) { badge.className = 'badge badge-submitted'; badge.textContent = 'Υποβλήθηκε'; }
    const card = document.getElementById('dircard-' + dirId);
    if (card) card.classList.add('done');

    await loadSubmissions();
}

// --- Submissions (Supabase) ---
async function loadSubmissions() {
    submissions = await supabase('citations_submissions', { filters: 'order=business_id' });
    if (!Array.isArray(submissions)) submissions = [];
    renderBusinessList();
}

async function loadStatusMatrix() {
    await loadSubmissions();
    const table = document.getElementById('statusMatrix');
    const empty = document.getElementById('emptyStatus');

    if (!businesses.length || !submissions.length) {
        table.style.display = 'none';
        empty.style.display = 'block';
        return;
    }
    table.style.display = 'table';
    empty.style.display = 'none';

    const thead = table.querySelector('thead tr');
    thead.innerHTML = '<th>Επιχείρηση</th>' + directories.map(d => `<th title="${d.name}">${d.id.replace('_', ' ')}</th>`).join('');

    const tbody = table.querySelector('tbody');
    tbody.innerHTML = businesses.map(b => {
        const cells = directories.map(d => {
            const sub = submissions.find(s => s.business_id === b.id && s.directory_id === d.id);
            const status = sub ? sub.status : 'pending';
            return `<td><span class="badge badge-${status}">${statusLabel(status)}</span></td>`;
        }).join('');
        return `<tr><td><strong>${esc(b.name)}</strong></td>${cells}</tr>`;
    }).join('');
}

// --- Settings ---
async function saveCaptchaKey() {
    const key = document.getElementById('setting_twocaptcha').value.trim();
    if (!key) { alert('Εισάγετε το API key'); return; }
    try {
        const res = await fetch(`${AUTOMATION_API}/api/settings`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ key: 'twocaptcha_api_key', value: key }),
        });
        if (res.ok) {
            document.getElementById('captchaStatus').textContent = 'API key αποθηκεύτηκε!';
            document.getElementById('captchaStatus').style.color = 'var(--success)';
        }
    } catch (e) {
        document.getElementById('captchaStatus').textContent = 'Σφάλμα σύνδεσης με τον server';
        document.getElementById('captchaStatus').style.color = 'var(--danger)';
    }
}

async function loadSettings() {
    try {
        const res = await fetch(`${AUTOMATION_API}/api/settings/twocaptcha_api_key`);
        if (res.ok) {
            const data = await res.json();
            if (data.value) document.getElementById('setting_twocaptcha').value = data.value;
        }
    } catch (e) {}
}

async function checkServerStatus() {
    try {
        const res = await fetch(`${AUTOMATION_API}/api/directories`, { signal: AbortSignal.timeout(5000) });
        if (res.ok) {
            document.getElementById('serverStatus').className = 'badge badge-submitted';
            document.getElementById('serverStatus').textContent = 'Online';
        }
    } catch (e) {
        document.getElementById('serverStatus').className = 'badge badge-error';
        document.getElementById('serverStatus').textContent = 'Offline';
    }
}

// --- Helpers ---
function esc(str) {
    const div = document.createElement('div');
    div.textContent = str || '';
    return div.innerHTML;
}
