// VPS Automation Server
const AUTOMATION_API = 'http://187.124.189.45:8000';

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
    { id: 'xo_gr', name: 'Χρυσός Οδηγός (xo.gr)', url: 'https://www.xo.gr', type: 'Ελληνικός' },
    { id: 'vrisko', name: 'Vrisko.gr (11880)', url: 'https://www.vrisko.gr', type: 'Ελληνικός' },
    { id: 'europages', name: 'Europages', url: 'https://www.europages.gr', type: 'Ευρωπαϊκός' },
    { id: 'bing_places', name: 'Bing Places', url: 'https://www.bingplaces.com', type: 'Παγκόσμιος' },
    { id: 'foursquare', name: 'Foursquare', url: 'https://foursquare.com', type: 'Παγκόσμιος' },
    { id: 'apple_business', name: 'Apple Business Connect', url: 'https://businessconnect.apple.com', type: 'Παγκόσμιος' },
    { id: 'cybo', name: 'Cybo', url: 'https://www.cybo.com', type: 'Διεθνής' },
    { id: 'infobel', name: 'Infobel', url: 'https://www.infobel.com', type: 'Ευρωπαϊκός' },
];
