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
            if (tab.dataset.tab === 'nap') populateNapSelect();
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
    submitted: 'Υποβλήθηκε', success: 'Υποβλήθηκε', complete: 'Υποβλήθηκε',
    already_listed: 'Υπάρχει ήδη', error: 'Σφάλμα',
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
    showmelocal: 'https://www.showmelocal.com/start-submission.aspx',
    globalcatalog: 'https://www.globalcatalog.com/add-business.html',
    twofindlocal: 'https://www.2findlocal.com/Modules/Biz/bizPhoneLookup.php',
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
        const statusMap = { running: 'running', waiting_human: 'waiting', success: 'submitted', error: 'error', complete: 'submitted', already_listed: 'already_listed' };
        badge.className = `badge badge-${statusMap[data.status] || 'pending'}`;
        badge.textContent = statusLabel(data.status);
    }
    if (msgEl) msgEl.textContent = data.message || '';
    if (card && (data.status === 'success' || data.status === 'complete' || data.status === 'already_listed')) {
        card.classList.add('done');
        const actionsDiv = card.querySelector('.dir-card-actions');
        // Add listing link if URL available
        if (data.url && actionsDiv && !actionsDiv.querySelector('.listing-link')) {
            const link = document.createElement('a');
            link.href = data.url;
            link.target = '_blank';
            link.className = 'btn btn-sm btn-success listing-link';
            link.innerHTML = 'Καταχώριση &rarr;';
            actionsDiv.prepend(link);
        }
        // Add screenshot link if available
        if (data.screenshot && actionsDiv && !actionsDiv.querySelector('.screenshot-link')) {
            const slink = document.createElement('a');
            slink.href = `${AUTOMATION_API}/api/screenshots/${data.screenshot}`;
            slink.target = '_blank';
            slink.className = 'btn btn-sm btn-outline screenshot-link';
            slink.textContent = 'Screenshot';
            actionsDiv.prepend(slink);
        }
    }

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
                    ${isDone && sub.url ? `<a href="${esc(sub.url)}" target="_blank" class="btn btn-sm btn-success listing-link">Καταχώριση &rarr;</a>` : ''}
                    ${isDone ? `<button class="btn btn-sm btn-outline" onclick="resubmitDir(${biz.id}, '${dirId}')">Επανυποβολή</button>` : ''}
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

async function resubmitDir(businessId, dirId) {
    if (!confirm(`Επανυποβολή ${dirId}; Θα γίνει εκ νέου καταχώριση.`)) return;

    // Reset status to pending
    await supabase('citations_submissions', {
        method: 'PATCH',
        filters: `business_id=eq.${businessId}&directory_id=eq.${dirId}`,
        body: { status: 'pending', notes: '', url: '' },
    });
    await loadSubmissions();

    // Run auto-submit for just this directory
    try {
        const res = await fetch(`${AUTOMATION_API}/api/automate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ business_id: businessId, directories: [dirId] }),
        });
        if (res.ok) {
            // Re-render to show running state
            renderSubmitCards();
        }
    } catch (e) {
        alert('Σφάλμα σύνδεσης με τον server');
    }
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
            const url = sub && sub.url ? sub.url : '';
            if (url && status === 'submitted') {
                return `<td><a href="${esc(url)}" target="_blank" class="badge badge-${status}" style="text-decoration:none;cursor:pointer" title="Άνοιγμα καταχώρισης">${statusLabel(status)} ↗</a></td>`;
            }
            return `<td><span class="badge badge-${status}">${statusLabel(status)}</span></td>`;
        }).join('');
        return `<tr><td><strong>${esc(b.name)}</strong></td>${cells}</tr>`;
    }).join('');
}

// --- Settings ---
async function saveSetting(key, elementId, statusId) {
    const val = document.getElementById(elementId).value.trim();
    try {
        const res = await fetch(`${AUTOMATION_API}/api/settings`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ key, value: val }),
        });
        if (res.ok && statusId) {
            const el = document.getElementById(statusId);
            el.textContent = 'Αποθηκεύτηκε!';
            el.style.color = 'var(--success)';
            setTimeout(() => el.textContent = '', 3000);
        }
    } catch (e) {
        if (statusId) {
            const el = document.getElementById(statusId);
            el.textContent = 'Σφάλμα σύνδεσης';
            el.style.color = 'var(--danger)';
        }
    }
}

async function saveCaptchaKey() {
    await saveSetting('twocaptcha_api_key', 'setting_twocaptcha', 'captchaStatus');
}

async function saveProxyList() {
    await saveSetting('proxy_list', 'setting_proxies', 'proxyStatus');
}

async function saveEmailSettings() {
    const fields = ['smtp_host', 'smtp_port', 'smtp_user', 'smtp_password', 'notify_email'];
    for (const f of fields) {
        const val = document.getElementById('setting_' + f).value.trim();
        await fetch(`${AUTOMATION_API}/api/settings`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ key: f, value: val }),
        });
    }
    const el = document.getElementById('emailStatus');
    el.textContent = 'Ρυθμίσεις email αποθηκεύτηκαν!';
    el.style.color = 'var(--success)';
    setTimeout(() => el.textContent = '', 3000);
}

async function loadSettings() {
    const keys = ['twocaptcha_api_key', 'proxy_list', 'smtp_host', 'smtp_port', 'smtp_user', 'smtp_password', 'notify_email', 'google_client_id', 'google_client_secret'];
    for (const key of keys) {
        try {
            const res = await fetch(`${AUTOMATION_API}/api/settings/${key}`);
            if (res.ok) {
                const data = await res.json();
                const elId = key === 'twocaptcha_api_key' ? 'setting_twocaptcha' : 'setting_' + key;
                const el = document.getElementById(elId);
                if (el && data.value) el.value = data.value;
            }
        } catch (e) {}
    }
}

function exportReport() {
    const businessId = document.getElementById('submitBusinessSelect').value;
    if (!businessId) { alert('Επιλέξτε πρώτα μια επιχείρηση'); return; }
    window.open(`${AUTOMATION_API}/api/report/${businessId}`, '_blank');
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

// --- NAP Checker ---
function populateNapSelect() {
    const sel = document.getElementById('napBusinessSelect');
    const val = sel.value;
    sel.innerHTML = '<option value="">-- Επιλέξτε επιχείρηση --</option>' +
        businesses.map(b => `<option value="${b.id}">${esc(b.name)} - ${esc(b.city || '')}</option>`).join('');
    sel.value = val;
}

async function startNapCheck() {
    const businessId = document.getElementById('napBusinessSelect').value;
    if (!businessId) { alert('Επιλέξτε πρώτα μια επιχείρηση'); return; }

    document.getElementById('napResults').style.display = 'block';
    document.getElementById('napTableBody').innerHTML = '<tr><td colspan="6" style="text-align:center;padding:20px">Ελέγχος σε εξέλιξη...</td></tr>';
    document.getElementById('napScore').textContent = 'Αναζήτηση...';
    document.getElementById('napScore').style.background = '#f3f4f6';
    document.getElementById('napProgress').textContent = '';

    // Connect SSE
    if (sseSource) sseSource.close();
    sseSource = new EventSource(`${AUTOMATION_API}/api/events`);
    sseSource.onmessage = (e) => {
        const data = JSON.parse(e.data);
        if (data.status === 'connected') return;

        if (data.step === 'nap_check') {
            document.getElementById('napProgress').textContent = data.message || '';
        }

        if (data.directory_id === 'nap' && data.step === 'done' && data.results) {
            renderNapResults(data.results);
            sseSource.close();
            sseSource = null;
        }
    };

    try {
        const res = await fetch(`${AUTOMATION_API}/api/nap-check`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ business_id: parseInt(businessId) }),
        });
        const data = await res.json();
        if (data.error) {
            alert(data.error);
            document.getElementById('napResults').style.display = 'none';
        }
    } catch (e) {
        alert('Σφάλμα σύνδεσης με τον server');
    }
}

function renderNapResults(results) {
    const tbody = document.getElementById('napTableBody');
    let totalChecked = 0;
    let totalMatch = 0;

    const napStatusIcon = (field) => {
        if (!field) return '<span style="color:var(--gray-300)">—</span>';
        const icons = {
            match: '<span style="color:var(--success)" title="Σωστό">✓</span>',
            partial: '<span style="color:var(--warning)" title="Μερική αντιστοιχία">~</span>',
            mismatch: '<span style="color:var(--danger)" title="Λάθος">✗</span>',
            not_found: '<span style="color:var(--gray-300)" title="Δεν βρέθηκε">—</span>',
            empty: '<span style="color:var(--gray-300)">—</span>',
            not_checked: '<span style="color:var(--gray-300)">—</span>',
            not_supported: '<span style="color:var(--gray-300)">N/A</span>',
        };
        return icons[field.status] || '—';
    };

    const napDetail = (field) => {
        if (!field || !field.found) return '';
        if (field.status === 'match') return '';
        if (field.status === 'mismatch' || field.status === 'partial') {
            return `<div style="font-size:11px;color:var(--gray-500);margin-top:2px">Βρέθηκε: ${esc(field.found || '')}</div>`;
        }
        return '';
    };

    tbody.innerHTML = results.map(r => {
        const dirName = directories.find(d => d.id === r.directory_id)?.name || r.directory_id;

        if (r.found) {
            ['name', 'address', 'phone'].forEach(f => {
                if (r[f] && r[f].status !== 'not_supported' && r[f].status !== 'not_checked' && r[f].status !== 'empty') {
                    totalChecked++;
                    if (r[f].match) totalMatch++;
                }
            });
        }

        return `<tr>
            <td><strong>${esc(dirName)}</strong></td>
            <td>${r.found ? '<span style="color:var(--success)">Ναι</span>' : '<span style="color:var(--gray-300)">Όχι</span>'}</td>
            <td>${napStatusIcon(r.name)}${napDetail(r.name)}</td>
            <td>${napStatusIcon(r.address)}${napDetail(r.address)}</td>
            <td>${napStatusIcon(r.phone)}${napDetail(r.phone)}</td>
            <td>${r.listing_url ? `<a href="${esc(r.listing_url)}" target="_blank" class="btn btn-sm btn-outline">Άνοιγμα ↗</a>` : '—'}</td>
        </tr>`;
    }).join('');

    // Score
    const scoreEl = document.getElementById('napScore');
    if (totalChecked > 0) {
        const pct = Math.round((totalMatch / totalChecked) * 100);
        scoreEl.textContent = `NAP Score: ${pct}% (${totalMatch}/${totalChecked} σωστά)`;
        if (pct >= 80) {
            scoreEl.style.background = '#dcfce7'; scoreEl.style.color = 'var(--success)';
        } else if (pct >= 50) {
            scoreEl.style.background = '#fef3c7'; scoreEl.style.color = 'var(--warning)';
        } else {
            scoreEl.style.background = '#fee2e2'; scoreEl.style.color = 'var(--danger)';
        }
    } else {
        scoreEl.textContent = 'Δεν βρέθηκαν καταχωρίσεις για έλεγχο';
        scoreEl.style.background = '#f3f4f6'; scoreEl.style.color = 'var(--gray-500)';
    }

    document.getElementById('napProgress').textContent = 'Ολοκληρώθηκε';
}

// --- Google Business Profile Import ---
let googleAccessToken = null;
let googleBusinesses = [];

async function startGoogleImport() {
    // Load client_id from settings
    try {
        const res = await fetch(`${AUTOMATION_API}/api/settings/google_client_id`);
        const data = await res.json();
        if (!data.value) {
            alert('Ρυθμίστε πρώτα το Google Client ID στις Ρυθμίσεις');
            return;
        }
        const clientId = data.value;
        const redirectUri = window.location.origin + '/google-callback.html';
        const scope = 'https://www.googleapis.com/auth/business.manage';
        const authUrl = 'https://accounts.google.com/o/oauth2/v2/auth' +
            '?client_id=' + encodeURIComponent(clientId) +
            '&redirect_uri=' + encodeURIComponent(redirectUri) +
            '&response_type=code' +
            '&scope=' + encodeURIComponent(scope) +
            '&access_type=offline' +
            '&prompt=consent';

        // Open popup
        const popup = window.open(authUrl, 'googleAuth', 'width=600,height=700');

        // Listen for message from callback page
        window.addEventListener('message', async function handler(e) {
            if (e.data && e.data.type === 'google_auth_code') {
                window.removeEventListener('message', handler);
                if (popup) popup.close();
                await handleGoogleCallback(e.data.code);
            }
        });
    } catch (e) {
        alert('Σφάλμα: Δεν ήταν δυνατή η σύνδεση με τον server');
    }
}

async function handleGoogleCallback(code) {
    const modal = document.getElementById('googleImportModal');
    modal.style.display = 'flex';
    document.getElementById('googleImportStatus').textContent = 'Ανταλλαγή κωδικού με Google...';
    document.getElementById('googleBusinessList').innerHTML = '';
    document.getElementById('googleImportActions').style.display = 'none';

    try {
        const redirectUri = window.location.origin + '/google-callback.html';
        const res = await fetch(`${AUTOMATION_API}/api/google/callback`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code, redirect_uri: redirectUri }),
        });
        const data = await res.json();

        if (data.error) {
            document.getElementById('googleImportStatus').textContent = 'Σφάλμα: ' + data.error;
            return;
        }

        googleAccessToken = data.access_token;
        googleBusinesses = data.businesses || [];
        showGoogleBusinesses(googleBusinesses);
    } catch (e) {
        document.getElementById('googleImportStatus').textContent = 'Σφάλμα σύνδεσης: ' + e.message;
    }
}

function showGoogleBusinesses(businesses) {
    const container = document.getElementById('googleBusinessList');

    if (!businesses.length) {
        document.getElementById('googleImportStatus').textContent = 'Δεν βρέθηκαν επιχειρήσεις στο Google Business Profile.';
        container.innerHTML = '';
        return;
    }

    document.getElementById('googleImportStatus').textContent = `Βρέθηκαν ${businesses.length} επιχειρήσεις. Επιλέξτε αυτές που θέλετε να εισάγετε:`;
    document.getElementById('googleImportActions').style.display = 'block';

    container.innerHTML = businesses.map((b, i) => `
        <label style="display:flex;align-items:flex-start;gap:10px;padding:10px;border:1px solid var(--gray-200);border-radius:6px;margin-bottom:8px;cursor:pointer">
            <input type="checkbox" checked value="${i}" style="margin-top:3px">
            <div>
                <strong>${esc(b.title || b.name || 'Χωρίς όνομα')}</strong>
                <div style="font-size:13px;color:var(--gray-500)">
                    ${esc(b.address || '')}${b.city ? ', ' + esc(b.city) : ''}
                    ${b.phone ? ' &bull; ' + esc(b.phone) : ''}
                    ${b.category ? ' &bull; ' + esc(b.category) : ''}
                </div>
            </div>
        </label>
    `).join('');
}

async function importSelectedGoogle() {
    const checkboxes = document.querySelectorAll('#googleBusinessList input[type="checkbox"]:checked');
    const selectedIds = [...checkboxes].map(cb => googleBusinesses[parseInt(cb.value)].location_id).filter(Boolean);

    if (!selectedIds.length) {
        alert('Επιλέξτε τουλάχιστον μία επιχείρηση');
        return;
    }

    document.getElementById('googleImportStatus').textContent = 'Εισαγωγή επιλεγμένων...';

    try {
        const res = await fetch(`${AUTOMATION_API}/api/google/import`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ access_token: googleAccessToken, locations: selectedIds }),
        });
        const data = await res.json();

        if (data.error) {
            document.getElementById('googleImportStatus').textContent = 'Σφάλμα: ' + data.error;
            return;
        }

        alert(`Εισαγωγή ${data.imported} επιχειρήσεων ολοκληρώθηκε!`);
        closeGoogleImport();
        await loadBusinesses();
    } catch (e) {
        document.getElementById('googleImportStatus').textContent = 'Σφάλμα: ' + e.message;
    }
}

function closeGoogleImport() {
    document.getElementById('googleImportModal').style.display = 'none';
    googleAccessToken = null;
    googleBusinesses = [];
}

async function saveGoogleSettings() {
    const fields = ['google_client_id', 'google_client_secret'];
    for (const f of fields) {
        const val = document.getElementById('setting_' + f).value.trim();
        await fetch(`${AUTOMATION_API}/api/settings`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ key: f, value: val }),
        });
    }
    const el = document.getElementById('googleSettingsStatus');
    el.textContent = 'Ρυθμίσεις Google αποθηκεύτηκαν!';
    el.style.color = 'var(--success)';
    setTimeout(() => el.textContent = '', 3000);
}

// --- Helpers ---
function esc(str) {
    const div = document.createElement('div');
    div.textContent = str || '';
    return div.innerHTML;
}
