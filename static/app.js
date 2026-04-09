// State
let businesses = [];
let directories = [];
let submissions = [];
let eventSource = null;

// --- Init ---
document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    loadDirectories();
    loadBusinesses();
    loadSubmissions();
    connectSSE();
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

// --- API helpers ---
async function api(path, options = {}) {
    const res = await fetch('/api' + path, {
        headers: { 'Content-Type': 'application/json' },
        ...options,
    });
    return res.json();
}

// --- Businesses ---
async function loadBusinesses() {
    businesses = await api('/businesses');
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
        await api('/businesses/' + id, { method: 'PUT', body: JSON.stringify(data) });
    } else {
        await api('/businesses', { method: 'POST', body: JSON.stringify(data) });
    }
    hideBusinessForm();
    await loadBusinesses();
}

function editBusiness(id) {
    showBusinessForm(id);
}

async function deleteBusiness(id) {
    if (!confirm('Διαγραφή αυτής της επιχείρησης και όλων των καταχωρήσεών της;')) return;
    await api('/businesses/' + id, { method: 'DELETE' });
    await loadBusinesses();
    await loadSubmissions();
}

// --- CSV ---
async function importCSV(input) {
    if (!input.files.length) return;
    const formData = new FormData();
    formData.append('file', input.files[0]);
    const res = await fetch('/api/businesses/import-csv', { method: 'POST', body: formData });
    const result = await res.json();
    alert(result.message || 'Η εισαγωγή ολοκληρώθηκε');
    input.value = '';
    await loadBusinesses();
}

function exportCSV() {
    window.location.href = '/api/businesses/export-csv';
}

// --- Directories ---
async function loadDirectories() {
    directories = await api('/directories');
    renderDirectoryGrid();
}

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

function onBusinessSelected() {
    // Could show preview of business info
}

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
    const businessId = document.getElementById('submitBusinessSelect').value;
    if (!businessId) { alert('Επιλέξτε πρώτα μια επιχείρηση'); return; }

    const dirs = getSelectedDirs();
    if (!dirs.length) { alert('Επιλέξτε τουλάχιστον έναν κατάλογο'); return; }

    document.getElementById('startBtn').disabled = true;
    document.getElementById('startBtn').textContent = 'Εκτελείται...';
    document.getElementById('progressCard').style.display = 'block';

    // Init progress items
    const progressList = document.getElementById('progressList');
    progressList.innerHTML = dirs.map(d => {
        const dir = directories.find(x => x.id === d);
        return `<div class="progress-item" id="progress-${d}">
            <div class="dir-label">${dir ? dir.name : d}</div>
            <div class="badge badge-pending">Εκκρεμεί</div>
            <div class="message">Αναμονή...</div>
        </div>`;
    }).join('');

    await api('/automate', {
        method: 'POST',
        body: JSON.stringify({ business_id: parseInt(businessId), directories: dirs }),
    });
}

async function continueAutomation() {
    await api('/automate/continue', { method: 'POST' });
    document.getElementById('continueBar').classList.remove('visible');
}

// --- SSE ---
function connectSSE() {
    eventSource = new EventSource('/api/events');
    eventSource.onopen = () => {
        document.getElementById('connectionStatus').textContent = 'Συνδεδεμένο';
    };
    eventSource.onmessage = (e) => {
        const data = JSON.parse(e.data);
        if (data.status === 'connected') return;

        // Update progress item
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

        // Show/hide continue bar
        if (data.status === 'waiting_human') {
            document.getElementById('continueMessage').textContent = data.message;
            document.getElementById('continueBar').classList.add('visible');
        }

        // All done
        if (data.directory_id === 'all' && data.step === 'done') {
            document.getElementById('startBtn').disabled = false;
            document.getElementById('startBtn').textContent = 'Εκκίνηση Αυτοματισμού';
            document.getElementById('continueBar').classList.remove('visible');
            loadSubmissions();
        }
    };
    eventSource.onerror = () => {
        document.getElementById('connectionStatus').textContent = 'Επανασύνδεση...';
    };
}

// --- Submissions / Status ---
async function loadSubmissions() {
    submissions = await api('/submissions');
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
