async function authFetch(url, options = {}) {
    const token = localStorage.getItem('token');
    if (!options.headers) options.headers = {};
    options.headers['Authorization'] = `Bearer ${token}`;
    return fetch(url, options);
}

let currentPage = 0;
const pageSize = 100;
let allLogs = [];

document.addEventListener('DOMContentLoaded', async () => {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = '/login';
        return;
    }

    try {
        const response = await authFetch('/api/auth/me');
        if (!response.ok) {
            localStorage.removeItem('token');
            window.location.href = '/login';
            return;
        }

        const user = await response.json();
        if (user.role !== 'superadmin') {
            alert('⛔ Доступ запрещён');
            window.location.href = '/admin';
            return;
        }

        document.getElementById('admin-name').textContent = `${user.name} (Superadmin)`;
    } catch (error) {
        console.error('Auth error:', error);
        window.location.href = '/login';
        return;
    }

    await loadWarehouses();
    await loadLogs();

    document.getElementById('apply-filters')?.addEventListener('click', () => {
        currentPage = 0;
        loadLogs();
    });

    document.getElementById('load-more')?.addEventListener('click', () => {
        currentPage++;
        loadLogs(true);
    });

    document.querySelector('.logout')?.addEventListener('click', (e) => {
        e.preventDefault();
        localStorage.removeItem('token');
        window.location.href = '/login';
    });
});

async function loadWarehouses() {
    try {
        const res = await authFetch('/api/warehouses/active');
        if (!res.ok) return;

        const warehouses = await res.json();
        const select = document.getElementById('filter-warehouse');

        warehouses.forEach(wh => {
            const option = document.createElement('option');
            option.value = wh.name;
            option.textContent = `${wh.name} (${wh.code})`;
            select.appendChild(option);
        });
        
        console.log('✅ Warehouses loaded');
    } catch (error) {
        console.error('Error:', error);
    }
}

async function loadLogs(append = false) {
    const dateFrom = document.getElementById('filter-date-from')?.value;
    const dateTo = document.getElementById('filter-date-to')?.value;
    const action = document.getElementById('filter-action')?.value;
    const user = document.getElementById('filter-user')?.value.trim();
    const warehouse = document.getElementById('filter-warehouse')?.value;

    const params = new URLSearchParams();
    if (dateFrom) params.append('date_from', dateFrom + 'T00:00:00');
    if (dateTo) params.append('date_to', dateTo + 'T23:59:59');
    if (action) params.append('action', action);
    if (user) params.append('user', user);
    if (warehouse) params.append('warehouse', warehouse);
    params.append('limit', pageSize);
    params.append('offset', currentPage * pageSize);

    try {
        const res = await authFetch(`/api/audit/logs?${params.toString()}`);
        if (!res.ok) throw new Error('Failed');

        const logs = await res.json();
        console.log('✅ Logs loaded:', logs.length);

        if (!append) {
            allLogs = logs;
        } else {
            allLogs = [...allLogs, ...logs];
        }

        renderLogs();
        updateStats();

    } catch (error) {
        console.error('Error:', error);
        const tbody = document.getElementById('logs-tbody');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-danger">Ошибка загрузки</td></tr>';
        }
    }
}

function renderLogs() {
    const tbody = document.getElementById('logs-tbody');
    if (!tbody) return;
    
    tbody.innerHTML = '';

    if (allLogs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center">Логов не найдено</td></tr>';
        return;
    }

    allLogs.forEach(log => {
        const tr = document.createElement('tr');
        const actionColor = getActionColor(log.action);
        
        // ✅ КРАСИВЫЙ ПАРСИНГ для каждого типа действия
        let detailsHtml = '-';
        if (log.details) {
            try {
                const details = JSON.parse(log.details);
                const parts = [];
                
                // LOGIN_SUCCESS
                if (log.action === 'LOGIN_SUCCESS' || log.action === 'LOGIN') {
                    if (details.name) parts.push(`<strong>${details.name}</strong>`);
                    if (details.role) parts.push(`Роль: ${translateRole(details.role)}`);
                }
                
                // CREATE_USER
                else if (log.action === 'CREATE_USER') {
                    if (details.user_name) parts.push(`<strong>${details.user_name}</strong>`);
                    if (details.user_email) parts.push(`Email: ${details.user_email}`);
                    if (details.user_role) parts.push(`Роль: ${translateRole(details.user_role)}`);
                    if (details.personal_code) parts.push(`Код: ${details.personal_code}`);
                }
                
                // CREATE_WAREHOUSE / DELETE_WAREHOUSE
                else if (log.action === 'CREATE_WAREHOUSE' || log.action === 'DELETE_WAREHOUSE') {
                    if (details.name) parts.push(`<strong>${details.name}</strong>`);
                    if (details.code) parts.push(`Код: ${details.code}`);
                }
                
                // BATCH_DELIVER / BATCH_DELETE
                else if (log.action === 'BATCH_DELIVER' || log.action === 'BATCH_DELETE') {
                    if (details.warehouse) parts.push(`<strong>Склад:</strong> ${details.warehouse}`);
                    if (details.count !== undefined) parts.push(`<strong>Кол-во:</strong> ${details.count}`);
                    if (details.tracks && details.tracks.length > 0) {
                        const trackList = details.tracks.slice(0, 3).join(', ');
                        const more = details.tracks.length > 3 ? ` <em>+${details.tracks.length - 3} ещё</em>` : '';
                        parts.push(`<strong>Треки:</strong> ${trackList}${more}`);
                    }
                    if (details.errors_count > 0) {
                        parts.push(`<span class="text-danger">Ошибок: ${details.errors_count}</span>`);
                    }
                }
                
                // UPLOAD_TRACKS
                else if (log.action === 'UPLOAD_TRACKS') {
                    if (details.filename) parts.push(`<strong>Файл:</strong> ${details.filename}`);
                    if (details.warehouse) parts.push(`<strong>Склад:</strong> ${details.warehouse}`);
                    if (details.tracks_added !== undefined) parts.push(`Добавлено: ${details.tracks_added}`);
                    if (details.errors_count > 0) {
                        parts.push(`<span class="text-danger">Ошибок: ${details.errors_count}</span>`);
                    }
                }
                
                // UPDATE_TRACK
                else if (log.action === 'UPDATE_TRACK') {
                    if (details.track_number) parts.push(`<strong>${details.track_number}</strong>`);
                    if (details.old_status && details.new_status) {
                        parts.push(`${details.old_status} → ${details.new_status}`);
                    }
                    if (details.warehouse) parts.push(`Склад: ${details.warehouse}`);
                }
                
                // HANDOUT_TRACK
                else if (log.action === 'HANDOUT_TRACK') {
                    if (details.track_number) parts.push(`<strong>${details.track_number}</strong>`);
                    if (details.recipient) parts.push(`Получатель: ${details.recipient}`);
                    if (details.warehouse) parts.push(`Склад: ${details.warehouse}`);
                }
                
                // CHANGE_USER_ROLE
                else if (log.action === 'CHANGE_USER_ROLE') {
                    if (details.user_email) parts.push(`<strong>${details.user_email}</strong>`);
                    if (details.old_role && details.new_role) {
                        parts.push(`${translateRole(details.old_role)} → ${translateRole(details.new_role)}`);
                    }
                }
                
                // Если ничего не распарсили - показать сырой JSON
                if (parts.length === 0) {
                    detailsHtml = JSON.stringify(details).substring(0, 100);
                } else {
                    detailsHtml = parts.join('<br>');
                }
                
            } catch (e) {
                detailsHtml = log.details.substring(0, 100);
            }
        }
        
        tr.innerHTML = `
            <td><small>${new Date(log.timestamp).toLocaleString('ru-RU')}</small></td>
            <td><span class="badge bg-${actionColor}">${translateAction(log.action)}</span></td>
            <td>${log.performed_by}</td>
            <td><small>${log.ip_address || '-'}</small></td>
            <td><small>${log.target_entity || '-'}</small></td>
            <td><small>${detailsHtml}</small></td>
        `;
        tbody.appendChild(tr);
    });

    document.getElementById('logs-count').textContent = allLogs.length;
}

// ✅ Перевод ролей
function translateRole(role) {
    const roles = {
        'superadmin': 'Супер Админ',
        'admin': 'Админ',
        'warehouse_admin': 'Админ склада',
        'client': 'Клиент'
    };
    return roles[role] || role;
}

// ✅ Перевод действий
function translateAction(action) {
    const actions = {
        'LOGIN_SUCCESS': 'Вход',
        'LOGIN': 'Вход',
        'CREATE_USER': 'Создан пользователь',
        'DELETE_USER': 'Удалён пользователь',
        'CREATE_WAREHOUSE': 'Создан склад',
        'UPDATE_WAREHOUSE': 'Обновлён склад',
        'DELETE_WAREHOUSE': 'Удалён склад',
        'UPLOAD_TRACKS': 'Загрузка треков',
        'BATCH_DELIVER': 'Массовая выдача',
        'BATCH_DELETE': 'Массовое удаление',
        'HANDOUT_TRACK': 'Выдача трека',
        'UPDATE_TRACK': 'Изменение трека',
        'CHANGE_USER_ROLE': 'Изменение роли'
    };
    return actions[action] || action;
}


function getActionColor(action) {
    const colors = {
        'LOGIN': 'success',
        'CREATE_USER': 'primary',
        'DELETE_USER': 'danger',
        'CREATE_WAREHOUSE': 'info',
        'UPDATE_WAREHOUSE': 'warning',
        'DELETE_WAREHOUSE': 'danger',
        'UPLOAD_TRACKS': 'success',
        'BATCH_DELIVER': 'success',
        'BATCH_DELETE': 'danger',        // ← ДОБАВЛЕНО
        'HANDOUT_TRACK': 'success',
        'UPDATE_TRACK': 'warning',
        'CHANGE_USER_ROLE': 'warning'
    };
    return colors[action] || 'secondary';
}
function updateStats() {
    const total = allLogs.length;
    const today = new Date().toDateString();
    const todayLogs = allLogs.filter(log => 
        new Date(log.timestamp).toDateString() === today
    );
    const uniqueUsers = new Set(allLogs.map(log => log.performed_by));

    document.getElementById('stat-total').textContent = total;
    document.getElementById('stat-today').textContent = todayLogs.length;
    document.getElementById('stat-users').textContent = uniqueUsers.size;
}
