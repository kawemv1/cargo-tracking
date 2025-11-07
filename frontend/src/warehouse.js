// frontend/src/warehouse.js - ПОЛНАЯ РАБОЧАЯ ВЕРСИЯ

const API_BASE = window.location.origin;
let USER_DATA = null;

function getToken() {
    return localStorage.getItem('token');
}

function authFetch(url, options = {}) {
    const token = getToken();
    if (!token) return Promise.reject('No token');
    
    options.headers = {
        ...options.headers,
        'Authorization': `Bearer ${token}`
    };
    
    return fetch(url, options);
}

// LOAD USER DATA
async function loadUserData() {
    try {
        const res = await authFetch(`${API_BASE}/api/auth/me`);
        if (res.ok) {
            USER_DATA = await res.json();
            document.getElementById('admin-name').textContent = USER_DATA.name;
            document.getElementById('warehouse-name').textContent = USER_DATA.assigned_warehouse || USER_DATA.branch || 'Склад';
        }
    } catch (err) {
        console.error(err);
    }
}

// LOAD STATS
async function loadStats() {
    try {
        const res = await authFetch(`${API_BASE}/api/warehouse/stats`);
        if (res.ok) {
            const stats = await res.json();
            document.getElementById('warehouse-parcels-count').textContent = stats.warehouse_count || 0;
            document.getElementById('today-handouts').textContent = stats.today_handouts || 0;
        }
    } catch (err) {
        console.error(err);
    }
}

// LOAD INVENTORY
async function loadInventory() {
    try {
        const res = await authFetch(`${API_BASE}/api/warehouse/inventory`);
        if (res.ok) {
            const parcels = await res.json();
            const tbody = document.getElementById('inventory-list');
            tbody.innerHTML = '';
            
            parcels.forEach(p => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td><strong>${p.track_number}</strong></td>
                    <td>${p.personal_code || '-'}</td>
                    <td>${p.received_date ? new Date(p.received_date).toLocaleDateString('ru-RU') : '-'}</td>
                `;
                tbody.appendChild(tr);
            });
        }
    } catch (err) {
        console.error(err);
    }
}

// RECEIVE PARCEL
async function receiveParcel() {
    const input = document.getElementById('receive-track-input');
    const trackNumber = input.value.trim().toUpperCase();
    
    if (!trackNumber) {
        alert('Введите трек-номер');
        return;
    }
    
    const formData = new FormData();
    formData.append('track_number', trackNumber);
    
    try {
        const res = await authFetch(`${API_BASE}/api/warehouse/receive`, {
            method: 'POST',
            body: formData
        });
        
        const result = await res.json();
        const resultDiv = document.getElementById('receive-result');
        
        if (res.ok) {
            resultDiv.innerHTML = `
                <div class="alert alert-success mt-2">
                    <strong>✅ Посылка принята!</strong><br>
                    Трек: ${result.track_number}<br>
                    Клиент: ${result.personal_code || 'Не назначен'}
                </div>
            `;
            input.value = '';
            loadStats();
            loadInventory();
        } else {
            resultDiv.innerHTML = `
                <div class="alert alert-danger mt-2">
                    <strong>❌ Ошибка:</strong> ${result.detail}
                </div>
            `;
        }
        
        setTimeout(() => { resultDiv.innerHTML = ''; }, 5000);
    } catch (err) {
        alert('❌ Ошибка: ' + err.message);
    }
}

// HANDOUT PARCEL
async function handoutParcel() {
    const input = document.getElementById('handout-track-input');
    const trackNumber = input.value.trim().toUpperCase();
    
    if (!trackNumber) {
        alert('Введите трек-номер');
        return;
    }
    
    if (!confirm(`Выдать посылку ${trackNumber} клиенту?`)) return;
    
    const formData = new FormData();
    formData.append('track_number', trackNumber);
    
    try {
        const res = await authFetch(`${API_BASE}/api/warehouse/handout`, {
            method: 'POST',
            body: formData
        });
        
        const result = await res.json();
        const resultDiv = document.getElementById('handout-result');
        
        if (res.ok) {
            resultDiv.innerHTML = `
                <div class="alert alert-success mt-2">
                    <strong>✅ Посылка выдана!</strong><br>
                    Трек: ${result.track_number}<br>
                    Клиент: ${result.personal_code}
                </div>
            `;
            input.value = '';
            loadStats();
            loadInventory();
        } else {
            resultDiv.innerHTML = `
                <div class="alert alert-danger mt-2">
                    <strong>❌ Ошибка:</strong> ${result.detail}
                </div>
            `;
        }
        
        setTimeout(() => { resultDiv.innerHTML = ''; }, 5000);
    } catch (err) {
        alert('❌ Ошибка: ' + err.message);
    }
}

// LOGOUT
function logout() {
    localStorage.removeItem('token');
    window.location.href = '/login';
}

// INIT
document.addEventListener('DOMContentLoaded', async () => {
    if (!getToken()) {
        window.location.href = '/login';
        return;
    }
    
    await loadUserData();
    await loadStats();
    await loadInventory();
    
    // Enter key handlers
    document.getElementById('receive-track-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') receiveParcel();
    });
    
    document.getElementById('handout-track-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handoutParcel();
    });
    
    // Search
    document.getElementById('inventory-search').addEventListener('input', (e) => {
        const search = e.target.value.toLowerCase();
        const rows = document.querySelectorAll('#inventory-list tr');
        rows.forEach(row => {
            row.style.display = row.textContent.toLowerCase().includes(search) ? '' : 'none';
        });
    });
});

// Make functions global
window.receiveParcel = receiveParcel;
window.handoutParcel = handoutParcel;
window.logout = logout;
window.loadInventory = loadInventory;

console.log('Warehouse.js loaded');
