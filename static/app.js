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
    checkLocalServer();
});

// --- Check if local automation server is running ---
let localServerAvailable = false;
let eventSource = null;

async function checkLocalServer() {
    try {
        const res = await fetch('http://localhost:8000/api/directories', { signal: AbortSignal.timeout(2000) });
        if (res.ok) {
            localServerAvailable = true;
            document.getElementById('connectionStatus').textContent = 'Automation: Online';
            document.getElementById('connectionStatus').style.color = '#86efac';
            connectSSE();
        }
    } catch {
        localServerAvailable = false;
        document.getElementById('connectionStatus').textContent = 'Automation: Offline (μόνο διαχείριση)';
        document.getElementById('connectionStatus').style.color = '#fcd34d';
    }
}

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
        await supabase('citations_businesses', {
            method: 'PATCH',
            filters: `id=eq.${id}`,
            body: data,
        });
    } else {
        await supabase('citations_businesses', { method: 'POST', body: data });
    }
    hideBusinessForm();
    await loadBusinesses();
}

function editBusiness(id) {
    showBusinessForm(id);
}

async function deleteBusiness(id) {
    if (!confirm('Διαγραφή αυτής της επιχείρησης και όλων των καταχωρήσεών της;')) return;
    // Delete submissions first, then business
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
        city: 'city', poli: 'city',
        city_en: 'city_en',
        postal_code: 'postal_code', zip: 'postal_code', tk: 'postal_code',
        region: 'region', nomos: 'region',
        phone: 'phone', tilefono: 'phone', tel: 'phone',
        mobile: 'mobile', kinito: 'mobile',
        email: 'email',
        website: 'website', url: 'website',
        category: 'category', kategoria: 'category',
        category_en: 'category_en',
        description_gr: 'description_gr', perigrafi: 'description_gr',
        description_en: 'description_en',
        hours: 'hours', ores: 'hours',
        facebook: 'facebook', instagram: 'instagram', linkedin: 'linkedin',
        tax_id: 'tax_id', afm: 'tax_id',
        contact_person: 'contact_person',
    };

    const validFields = ['name','name_en','address','city','city_en','postal_code','region',
        'phone','mobile','email','website','category','category_en','contact_person',
        'tax_id','hours','facebook','instagram','linkedin','description_gr','description_en'];

    let imported = 0;
    for (let i = 1; i < lines.length; i++) {
        const line = lines[i].trim();
        if (!line) continue;

        // Simple CSV parsing (handles basic quoted fields)
        const values = parseCSVLine(line);
        const row = {};
        headers.forEach((h, idx) => {
            const field = fieldMap[h] || h;
            if (validFields.includes(field)) {
                row[field] = (values[idx] || '').trim();
            }
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
    const result = [];
    let current = '';
    let inQuotes = false;
    for (let i = 0; i < line.length; i++) {
        const ch = line[i];
        if (ch === '"') { inQuotes = !inQuotes; }
        else if (ch === ',' && !inQuotes) { result.push(current); current = ''; }
        else { current += ch; }
    }
    result.push(current);
    return result;
}

function exportCSV() {
    if (!businesses.length) { alert('Δεν υπάρχουν επιχειρήσεις'); return; }
    const fields = ['name','name_en','address','city','city_en','postal_code','region',
        'phone','mobile','email','website','category','category_en',
        'description_gr','description_en','hours','facebook','instagram',
        'linkedin','tax_id','contact_person'];
    let csv = fields.join(',') + '\n';
    businesses.forEach(b => {
        csv += fields.map(f => `"${(b[f] || '').replace(/"/g, '""')}"`).join(',') + '\n';
    });
    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'businesses.csv';
    a.click();
    URL.revokeObjectURL(url);
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

function selectAllDirs() {
    document.querySelectorAll('#directoryGrid input[type="checkbox"]').forEach(cb => cb.checked = true);
}
function deselectAllDirs() {
    document.querySelectorAll('#directoryGrid input[type="checkbox"]').forEach(cb => cb.checked = false);
}

function getSelectedDirs() {
    return [...document.querySelectorAll('#directoryGrid input[type="checkbox"]:checked')].map(cb => cb.value);
}

// --- Submit tab ---
function populateBusinessSelect() {
    const sel = document.getElementById('submitBusinessSelect');
    const val = sel.value;
    sel.innerHTML = '<option value="">-- Επιλέξτε επιχείρηση --</option>' +
        businesses.map(b => `<option value="${b.id}">${esc(b.name)} - ${esc(b.city || '')}</option>`).join('');
    sel.value = val;
}

function onBusinessSelected() {}

// Status label translations
const STATUS_LABELS = {
    'pending': 'Εκκρεμεί',
    'running': 'Σε εξέλιξη',
    'waiting_human': 'Αναμονή',
    'submitted': 'Υποβλήθηκε',
    'success': 'Υποβλήθηκε',
    'complete': 'Υποβλήθηκε',
    'error': 'Σφάλμα',
};

function statusLabel(status) {
    return STATUS_LABELS[status] || status;
}

async function startAutomation() {
    if (!localServerAvailable) {
        alert('Ο local automation server δεν τρέχει.\n\nΓια να τρέξετε automation, ανοίξτε terminal και εκτελέστε:\ncd ~/Desktop/citations && python3 run.py');
        return;
    }

    const businessId = document.getElementById('submitBusinessSelect').value;
    if (!businessId) { alert('Επιλέξτε πρώτα μια επιχείρηση'); return; }

    const dirs = getSelectedDirs();
    if (!dirs.length) { alert('Επιλέξτε τουλάχιστον έναν κατάλογο'); return; }

    document.getElementById('startBtn').disabled = true;
    document.getElementById('startBtn').textContent = 'Εκτελείται...';
    document.getElementById('progressCard').style.display = 'block';

    const progressList = document.getElementById('progressList');
    progressList.innerHTML = dirs.map(d => {
        const dir = directories.find(x => x.id === d);
        return `<div class="progress-item" id="progress-${d}">
            <div class="dir-label">${dir ? dir.name : d}</div>
            <div class="badge badge-pending">Εκκρεμεί</div>
            <div class="message">Αναμονή...</div>
        </div>`;
    }).join('');

    // Call local automation server
    try {
        await fetch('http://localhost:8000/api/automate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ business_id: parseInt(businessId), directories: dirs }),
        });
    } catch (e) {
        alert('Σφάλμα σύνδεσης με τον local server: ' + e.message);
        document.getElementById('startBtn').disabled = false;
        document.getElementById('startBtn').textContent = 'Εκκίνηση Αυτοματισμού';
    }
}

async function continueAutomation() {
    try {
        await fetch('http://localhost:8000/api/automate/continue', { method: 'POST' });
        document.getElementById('continueBar').classList.remove('visible');
    } catch (e) {
        alert('Σφάλμα: ' + e.message);
    }
}

// --- SSE (from local server) ---
function connectSSE() {
    eventSource = new EventSource('http://localhost:8000/api/events');
    eventSource.onmessage = (e) => {
        const data = JSON.parse(e.data);
        if (data.status === 'connected') return;

        const item = document.getElementById('progress-' + data.directory_id);
        if (item) {
            const cssClass = data.status === 'waiting_human' ? 'waiting' : data.status === 'error' ? 'error' : (data.status === 'success' || data.status === 'submitted') ? 'success' : 'running';
            item.className = 'progress-item ' + cssClass;

            const badge = item.querySelector('.badge');
            const badgeClass = data.status === 'waiting_human' ? 'waiting' : data.status === 'error' ? 'error' : (data.status === 'success' || data.status === 'submitted' || data.status === 'complete') ? 'submitted' : 'running';
            badge.className = 'badge badge-' + badgeClass;
            badge.textContent = statusLabel(data.status);
            item.querySelector('.message').textContent = data.message;
        }

        if (data.status === 'waiting_human') {
            document.getElementById('continueMessage').textContent = data.message;
            document.getElementById('continueBar').classList.add('visible');
        }

        if (data.directory_id === 'all' && data.step === 'done') {
            document.getElementById('startBtn').disabled = false;
            document.getElementById('startBtn').textContent = 'Εκκίνηση Αυτοματισμού';
            document.getElementById('continueBar').classList.remove('visible');
            loadSubmissions();
        }
    };
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

// --- Helpers ---
function esc(str) {
    const div = document.createElement('div');
    div.textContent = str || '';
    return div.innerHTML;
}
