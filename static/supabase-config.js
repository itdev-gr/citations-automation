// VPS Automation Server
const AUTOMATION_API = 'https://api.softwarecitations.com';

// Supabase Configuration
const SUPABASE_URL = 'https://jkbxdjuszhrnbvivsuvw.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImprYnhkanVzemhybmJ2aXZzdXZ3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzU2MzkyNjQsImV4cCI6MjA5MTIxNTI2NH0.GziMKhOwRiUHlvgckD4FQgk39DHrXDKt-lY-atdjGnM';

// Supabase REST API helper
async function supabase(table, { method = 'GET', filters = '', body = null, headers = {} } = {}) {
    const url = `${SUPABASE_URL}/rest/v1/${table}${filters ? '?' + filters : ''}`;
    const opts = {
        method,
        headers: {
            'apikey': SUPABASE_ANON_KEY,
            'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
            'Content-Type': 'application/json',
            'Prefer': method === 'POST' ? 'return=representation' : method === 'DELETE' ? 'return=minimal' : 'return=representation',
            ...headers,
        },
    };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(url, opts);
    if (method === 'DELETE') return [];
    return res.json();
}

// DIRECTORIES constant
const DIRECTORIES = [
    // Ελληνικοί
    { id: 'xo_gr', name: 'Χρυσός Οδηγός (xo.gr)', url: 'https://www.xo.gr', type: 'Ελληνικός' },
    { id: 'vrisko', name: 'Vrisko.gr (11880)', url: 'https://www.vrisko.gr', type: 'Ελληνικός' },
    { id: 'vres', name: 'Vres.gr', url: 'https://www.vres.gr', type: 'Ελληνικός' },
    { id: 'findhere', name: 'FindHere.gr', url: 'https://www.findhere.gr', type: 'Ελληνικός' },
    { id: 'stigmap', name: 'StigMap.gr', url: 'https://www.stigmap.gr', type: 'Ελληνικός' },
    // Πλοήγηση / Χάρτες
    { id: 'waze', name: 'Waze', url: 'https://www.waze.com', type: 'Χάρτες' },
    { id: 'tomtom', name: 'TomTom', url: 'https://www.tomtom.com', type: 'Χάρτες' },
    { id: 'here', name: 'HERE WeGo', url: 'https://wego.here.com', type: 'Χάρτες' },
    { id: 'openstreetmap', name: 'OpenStreetMap', url: 'https://www.openstreetmap.org', type: 'Χάρτες' },
    // Reviews / Social
    { id: 'foursquare', name: 'Foursquare', url: 'https://foursquare.com', type: 'Reviews' },
    { id: 'tupalo', name: 'Tupalo', url: 'https://www.tupalo.co', type: 'Reviews' },
    // Ευρωπαϊκοί / Διεθνείς
    { id: 'europages', name: 'Europages', url: 'https://www.europages.gr', type: 'Ευρωπαϊκός' },
    { id: 'cybo', name: 'Cybo', url: 'https://www.cybo.com', type: 'Διεθνής' },
    { id: 'infobel', name: 'Infobel', url: 'https://www.infobel.com', type: 'Ευρωπαϊκός' },
    { id: 'brownbook', name: 'Brownbook.net', url: 'https://www.brownbook.net', type: 'Διεθνής' },
    { id: 'storeboard', name: 'Storeboard', url: 'https://www.storeboard.com', type: 'Διεθνής' },
    { id: 'yellowplace', name: 'Yellow.Place', url: 'https://yellow.place', type: 'Διεθνής' },
    { id: 'showmelocal', name: 'ShowMeLocal', url: 'https://www.showmelocal.com', type: 'Διεθνής' },
    { id: 'globalcatalog', name: 'GlobalCatalog', url: 'https://www.globalcatalog.com', type: 'Διεθνής' },
    { id: 'twofindlocal', name: '2FindLocal', url: 'https://www.2findlocal.com', type: 'Διεθνής' },
];
