// frontend/src/superadmin.js - ПОЛНАЯ ИСПРАВЛЕННАЯ ВЕРСИЯ

// Глобальная функция authFetch (СНАРУЖИ DOMContentLoaded)
async function authFetch(url, options = {}) {
    const token = localStorage.getItem('token');
    
    if (!token) {
        console.error('❌ No token found in localStorage');
        window.location.href = '/login';
        throw new Error('Authentication required');
    }
    
    if (!options.headers) {
        options.headers = {};
    }
    
    options.headers['Authorization'] = `Bearer ${token}`;
    
    try {
        const response = await fetch(url, options);
        
        if (response.status === 401) {
            console.error('❌ 401 Unauthorized - Token expired or invalid');
            localStorage.removeItem('token');
            window.location.href = '/login';
            throw new Error('Unauthorized');
        }
        
        return response;
    } catch (error) {
        console.error('❌ authFetch error:', error);
        throw error;
    }
}

// ===== HELPER FUNCTIONS =====
async function authFetch(url, options = {}) {
    const token = localStorage.getItem('token');
    if (!options.headers) options.headers = {};
    options.headers['Authorization'] = `Bearer ${token}`;
    return fetch(url, options);
}

// Global state for preventing duplicate requests
const requestLocks = {
    creatingWarehouse: false,
    editingWarehouse: false,
    deletingWarehouse: false
};

// Глобальные функции для модалов
window.showEditWarehouse = async function(warehouseId) {
    try {
        const res = await authFetch('/api/warehouses');
        const warehouses = await res.json();
        const wh = warehouses.find(w => w.id === warehouseId);
        if (!wh) return;
        
        document.getElementById('edit-warehouse-id').value = wh.id;
        document.getElementById('edit-warehouse-name').value = wh.name;
        document.getElementById('edit-warehouse-code').value = wh.code;
        document.getElementById('edit-warehouse-address').value = wh.address || '';
        document.getElementById('edit-warehouse-phone').value = wh.phone || '';
        document.getElementById('edit-warehouse-manager').value = wh.manager || '';
        document.getElementById('edit-warehouse-active').checked = wh.is_active;
        
        new bootstrap.Modal(document.getElementById('editWarehouseModal')).show();
    } catch (error) {
        alert('❌ Ошибка загрузки склада');
    }
};

window.showWarehouseStats = async function(code) {
    try {
        const res = await authFetch(`/api/warehouses/${code}/stats`);
        const data = await res.json();
        
        document.getElementById('stats-warehouse-name').textContent = data.warehouse.name;
        document.getElementById('stats-total-tracks').textContent = data.stats.total_tracks;
        document.getElementById('stats-delivered').textContent = data.stats.delivered;
        document.getElementById('stats-in-transit').textContent = data.stats.in_transit;
        document.getElementById('stats-users').textContent = data.stats.users_count;
        
        const tbody = document.getElementById('stats-activity-body');
        tbody.innerHTML = '';
        data.recent_activity.forEach(log => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${log.action}</td>
                <td>${log.by}</td>
                <td>${new Date(log.time).toLocaleString('ru-RU')}</td>
            `;
            tbody.appendChild(tr);
        });
        
        new bootstrap.Modal(document.getElementById('warehouseStatsModal')).show();
    } catch (error) {
        alert('❌ Ошибка загрузки статистики');
    }
};

window.showWarehouseLogs = async function(code) {
    try {
        const res = await authFetch(`/api/audit/logs/warehouse/${code}`);
        const logs = await res.json();
        
        const tbody = document.getElementById('warehouse-logs-body');
        tbody.innerHTML = '';
        
        logs.forEach(log => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${new Date(log.timestamp).toLocaleString('ru-RU')}</td>
                <td>${log.action}</td>
                <td>${log.performed_by}</td>
                <td>${log.target_entity || '-'}</td>
                <td><small>${JSON.stringify(log.details)}</small></td>
            `;
            tbody.appendChild(tr);
        });
        
        new bootstrap.Modal(document.getElementById('warehouseLogsModal')).show();
    } catch (error) {
        alert('❌ Ошибка загрузки логов');
    }
};

window.deleteUser = async function(userId) {
    if (!confirm("Удалить пользователя?")) return;

    try {
        const res = await authFetch(`/api/users/${userId}`, { method: "DELETE" });
        if (res.ok) {
            alert("✅ Пользователь удалён");
            location.reload();
        } else {
            alert("❌ Ошибка удаления");
        }
    } catch (error) {
        alert("❌ Ошибка: " + error.message);
    }
};

window.deleteWarehouse = async function(warehouseId) {
    if (!confirm("Удалить склад?")) return;

    try {
        const res = await authFetch(`/api/warehouses/${warehouseId}`, { method: "DELETE" });
        if (res.ok) {
            alert("✅ Склад удалён");
            location.reload();
        } else {
            alert("❌ Ошибка удаления");
        }
    } catch (error) {
        alert("❌ Ошибка: " + error.message);
    }
};

window.showChangeRoleModal = function(userId, userName, userEmail, currentRole) {
    document.getElementById('change-role-user-id').value = userId;
    document.getElementById('change-role-user-name').textContent = userName;
    document.getElementById('change-role-user-email').textContent = userEmail;
    document.getElementById('change-role-current').textContent = currentRole;
    document.getElementById('change-role-new').value = currentRole;
    
    new bootstrap.Modal(document.getElementById('changeRoleModal')).show();
};

window.deleteSuperadminUser = async function(userId) {
    if (!confirm('Удалить пользователя?')) return;
    
    try {
        const res = await authFetch(`/api/users/${userId}`, { method: 'DELETE' });
        if (res.ok) {
            alert('✅ Удалён');
            const loadAllUsersFunc = window.loadAllUsersSuperadmin;
            if (loadAllUsersFunc) loadAllUsersFunc();
        } else {
            alert('❌ Ошибка');
        }
    } catch (error) {
        alert('❌ ' + error.message);
    }
};

window.exportUsers = async function() {
    try {
        const res = await authFetch('/api/users/export?format=csv');
        if (!res.ok) throw new Error('Failed');
        
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `users_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
        alert('✅ Экспорт завершён!');
    } catch (error) {
        alert('❌ Ошибка экспорта');
    }
};

// DOMContentLoaded
document.addEventListener("DOMContentLoaded", async () => {
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
            window.location.href = '/admin';
            return;
        }

        const adminNameEl = document.getElementById('admin-name');
        if (adminNameEl) adminNameEl.textContent = user.name + ' (Superadmin)';

        console.log('✅ Superadmin authenticated:', user.name);

    } catch (error) {
        console.error('❌ Auth error:', error);
        window.location.href = '/login';
        return;
    }

    // Load initial data
    loadStats();
    loadWarehouses();
    loadCalendar();

    // Add warehouse
        // Добавить склад
    // Добавить склад
    let isCreatingWarehouse = false;

// Найди form submit handler
document.getElementById('add-warehouse-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // ЗАЩИТА ОТ ДВОЙНОГО ЗАПРОСА
    
    
    isCreatingWarehouse = true;
    const submitBtn = e.submitter || e.target.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Создание...';
    
    try {
        const formData = new FormData(e.target);
        const res = await authFetch('/api/warehouses', {
            method: 'POST',
            body: formData
        });
        
        if (!res.ok) {
            const error = await res.json();
            throw new Error(error.detail);
        }
        
        const result = await res.json();
        console.log('✅ Warehouse created:', result);
        alert('✅ Склад создан');
        
        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('addWarehouseModal'));
        if (modal) modal.hide();
        
        e.target.reset();
        await loadWarehouses();
        
    } catch (error) {
        console.error('❌ Error:', error);
        alert('❌ Ошибка: ' + error.message);
    } finally {
        isCreatingWarehouse = false;
        submitBtn.disabled = false;
        submitBtn.textContent = 'Создать склад';
    }
});


   // ========== ADD WAREHOUSE ==========
// ✅ ОСТАВЬ ТОЛЬКО ЭТОТ (с защитой)


// Create Warehouse Handler (with duplicate request prevention)
// Create Warehouse Handler (with duplicate request prevention)
document.getElementById('add-warehouse-btn')?.addEventListener('click', async () => {
    // Prevent duplicate requests
    if (requestLocks.creatingWarehouse) {
        console.warn('⚠️ Warehouse creation already in progress');
        return;
    }
    
    const name = document.getElementById('warehouse-name')?.value.trim();
    const code = document.getElementById('warehouse-code')?.value.trim();
    const address = document.getElementById('warehouse-address')?.value.trim();
    const phone = document.getElementById('warehouse-phone')?.value.trim();
    const manager = document.getElementById('warehouse-manager')?.value.trim();
    
    if (!name || !code) {
        alert('⚠️ Заполните название и код склада');
        return;
    }
    
    // Lock the request
    requestLocks.creatingWarehouse = true;
    
    const btn = document.getElementById('add-warehouse-btn');
    const originalText = btn.textContent;
    btn.disabled = true;
    btn.textContent = 'Создание...';
    
    const formData = new FormData();
    formData.append('name', name);
    formData.append('code', code.toUpperCase());
    if (address) formData.append('address', address);
    if (phone) formData.append('phone', phone);
    if (manager) formData.append('manager', manager);
    
    try {
        const res = await authFetch('/api/warehouses', {
            method: 'POST',
            body: formData
        });
        
        if (res.ok) {
            const result = await res.json();
            console.log('✅ Warehouse created:', result);
            alert(`✅ Склад "${result.name}" (${result.code}) создан!`);
            
            // Clear all fields
            document.getElementById('warehouse-name').value = '';
            document.getElementById('warehouse-code').value = '';
            document.getElementById('warehouse-address').value = '';
            document.getElementById('warehouse-phone').value = '';
            document.getElementById('warehouse-manager').value = '';
            
            // Reload data
            await loadWarehouses();
            await loadStats();
            await loadWarehousesForUserForm();
        } else {
            const error = await res.json();
            alert('❌ Ошибка: ' + (error.detail || 'Failed to create warehouse'));
        }
    } catch (error) {
        console.error('❌ Error creating warehouse:', error);
        alert('❌ Ошибка: ' + error.message);
    } finally {
        // Always unlock and restore button
        requestLocks.creatingWarehouse = false;
        btn.disabled = false;
        btn.textContent = originalText;
    }
});



// ========== ADD USER FORM ========== (ТЕПЕРЬ ВНЕ!)
const form = document.getElementById("add-user-form");
if (form) {
    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const role = document.getElementById("user-role").value;
        const branch = document.getElementById("user-branch")?.value;
        
        if (!branch) {
            alert("⚠️ Выберите склад");
            return;
        }

        const formData = new FormData();
        formData.append("name", document.getElementById("user-name").value);
        formData.append("email", document.getElementById("user-email").value);
        formData.append("password", document.getElementById("user-password").value);
        formData.append("whatsapp", document.getElementById("user-whatsapp").value);
        formData.append("branch", branch);
        formData.append("role", role);

        const personalCode = document.getElementById("user-personal-code")?.value.trim();
        if (personalCode) {
            formData.append("personalcode", personalCode);
        }

        try {
            const res = await authFetch("/api/users", {
                method: "POST",
                body: formData
            });

            if (res.ok) {
                const result = await res.json();
                alert("✅ Пользователь добавлен!\n" + 
                    "Email: " + result.email + "\n" + 
                    "Личный код: " + (result.personalcode || "не указан"));
                
                form.reset();
                
                const warehouseContainer = document.getElementById("warehouse-select-container");
                if (warehouseContainer) {
                    warehouseContainer.style.display = "none";
                }
                
                await loadStats();
                
                console.log('✅ User added successfully');
            } else {
                const error = await res.json();
                console.error('❌ Error response:', error);
                alert("❌ Ошибка: " + error.detail);
            }
        } catch (error) {
            console.error("❌ Error adding user:", error);
            alert("❌ Ошибка добавления пользователя: " + error.message);
        }
    });
}

// ========== ROLE CHANGE HANDLER ==========

    // Save warehouse edit
    document.getElementById('save-warehouse-edit-btn')?.addEventListener('click', async () => {
        const id = document.getElementById('edit-warehouse-id').value;
        const formData = new FormData();
        formData.append('name', document.getElementById('edit-warehouse-name').value);
        formData.append('code', document.getElementById('edit-warehouse-code').value);
        formData.append('address', document.getElementById('edit-warehouse-address').value);
        formData.append('phone', document.getElementById('edit-warehouse-phone').value);
        formData.append('manager', document.getElementById('edit-warehouse-manager').value);
        formData.append('is_active', document.getElementById('edit-warehouse-active').checked);
        
        try {
            const res = await authFetch(`/api/warehouses/${id}`, { method: 'PUT', body: formData });
            
            if (res.ok) {
                alert('✅ Склад обновлён!');
                bootstrap.Modal.getInstance(document.getElementById('editWarehouseModal')).hide();
                loadWarehouses();
            } else {
                const error = await res.json();
                alert('❌ ' + error.detail);
            }
        } catch (error) {
            alert('❌ ' + error.message);
        }
    });

    // USER MANAGEMENT
    const usersContainer = document.getElementById('users-container');
    const usersTableBody = document.getElementById('users-table-body');
    const toggleUsersBtn = document.getElementById('toggle-users-btn');

    async function loadAllUsers() {
        console.log('🔍 Loading users...');
        
        const search = document.getElementById('superadmin-user-search')?.value?.trim() || '';
        const role = document.getElementById('superadmin-filter-role')?.value || '';
        const warehouse = document.getElementById('superadmin-filter-warehouse')?.value || '';
        const sortBy = document.getElementById('superadmin-sort-by')?.value || 'name';
        const order = document.getElementById('superadmin-sort-order')?.value || 'asc';
        
        const params = new URLSearchParams();
        if (search) params.append('search', search);
        if (role) params.append('role', role);
        if (warehouse) params.append('warehouse', warehouse);
        params.append('sort_by', sortBy);
        params.append('order', order);
        
        try {
            const res = await authFetch(`/api/users/filter?${params.toString()}`);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            
            const users = await res.json();
            console.log('✅ Loaded:', users.length);
            
            if (!usersTableBody) return;
            
            usersTableBody.innerHTML = '';
            
            if (users.length === 0) {
                usersTableBody.innerHTML = '<tr><td colspan="7" class="text-center">Ничего не найдено</td></tr>';
                return;
            }
            
            users.forEach(user => {
                const tr = document.createElement('tr');
                
                let roleColor = 'primary';
                if (user.role === 'superadmin') roleColor = 'danger';
                else if (user.role === 'admin') roleColor = 'warning';
                else if (user.role === 'warehouse_admin') roleColor = 'info';
                
                const safeName = (user.name || '').replace(/'/g, "\\'");
                
                tr.innerHTML = `
                    <td><strong>${user.personalcode || user.id}</strong></td>
                    <td>${user.name}</td>
                    <td>${user.email}</td>
                    <td>${user.whatsapp || '-'}</td>
                    <td>${user.branch || '-'}</td>
                    <td><span class="badge bg-${roleColor}">${user.role || 'client'}</span></td>
                    <td>
                        <button class="btn btn-sm btn-info" onclick="showChangeRoleModal(${user.id}, '${safeName}', '${user.email}', '${user.role}')">👤</button>
                        <button class="btn btn-sm btn-danger" onclick="deleteSuperadminUser(${user.id})">✕</button>
                    </td>
                `;
                usersTableBody.appendChild(tr);
            });
            
        } catch (error) {
            console.error('❌ Error:', error);
            if (usersTableBody) {
                usersTableBody.innerHTML = '<tr><td colspan="7">Ошибка</td></tr>';
            }
        }
    }

    window.loadAllUsersSuperadmin = loadAllUsers;

    if (toggleUsersBtn) {
        toggleUsersBtn.addEventListener('click', () => {
            if (usersContainer.style.display === 'none') {
                usersContainer.style.display = 'block';
                toggleUsersBtn.textContent = 'Скрыть';
                loadAllUsers();
                loadWarehousesForUserFilter();
            } else {
                usersContainer.style.display = 'none';
                toggleUsersBtn.textContent = 'Показать пользователей';
            }
        });
    }

    function debounce(func, wait) {
        let timeout;
        return function(...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func(...args), wait);
        };
    }

    const debouncedUserFilter = debounce(loadAllUsers, 300);

    document.getElementById('superadmin-user-search')?.addEventListener('input', debouncedUserFilter);
    document.getElementById('superadmin-filter-role')?.addEventListener('change', loadAllUsers);
    document.getElementById('superadmin-filter-warehouse')?.addEventListener('change', loadAllUsers);
    document.getElementById('superadmin-sort-by')?.addEventListener('change', loadAllUsers);
    document.getElementById('superadmin-sort-order')?.addEventListener('change', loadAllUsers);

    async function loadWarehousesForUserFilter() {
        try {
            const res = await authFetch('/api/warehouses/active');
            if (!res.ok) return;

            const warehouses = await res.json();
            const select = document.getElementById('superadmin-filter-warehouse');
            
            if (select) {
                const placeholder = select.querySelector('option[value=""]');
                select.innerHTML = '';
                if (placeholder) select.appendChild(placeholder.cloneNode(true));
                
                warehouses.forEach(wh => {
                    const option = document.createElement('option');
                    option.value = wh.code;
                    option.textContent = `${wh.name} (${wh.code})`;
                    select.appendChild(option);
                });
            }
        } catch (error) {
            console.error('❌ Error:', error);
        }
    }

    document.getElementById('save-role-btn')?.addEventListener('click', async () => {
        const userId = document.getElementById('change-role-user-id').value;
        const newRole = document.getElementById('change-role-new').value;
        
        if (!confirm('Изменить роль?')) return;
        
        try {
            const formData = new FormData();
            formData.append('new_role', newRole);
            
            const res = await authFetch(`/api/users/${userId}/role`, { method: 'PUT', body: formData });
            
            if (res.ok) {
                alert('✅ Роль изменена!');
                bootstrap.Modal.getInstance(document.getElementById('changeRoleModal')).hide();
                loadAllUsers();
            } else {
                const error = await res.json();
                alert('❌ ' + error.detail);
            }
        } catch (error) {
            alert('❌ ' + error.message);
        }
    });

    // Functions
    async function loadStats() {
        try {
            const res = await authFetch("/api/stats");
            if (!res.ok) throw new Error("Failed");

            const stats = await res.json();

            document.getElementById("stat-tracks").textContent = stats.total_tracks || 0;
            document.getElementById("stat-users").textContent = stats.total_users || 0;
            document.getElementById("stat-warehouses").textContent = stats.total_warehouses || 0;
            document.getElementById("stat-delivered").textContent = stats.delivered_tracks || 0;

            console.log("✅ Stats loaded");
        } catch (error) {
            console.error("❌ Error:", error);
        }
    }

    async function loadWarehouses() {
    console.log('📦 Loading warehouses...');
    
    try {
        const res = await authFetch('/api/warehouses');
        
        if (!res.ok) {
            console.error('❌ Failed to load warehouses:', res.status);
            throw new Error('Failed to load warehouses');
        }

        const warehouses = await res.json();
        console.log('✅ Warehouses loaded:', warehouses.length, warehouses);
        
        const tbody = document.getElementById('warehouses-table-body');
        
        if (!tbody) {
            console.error('❌ warehouses-table-body not found!');
            return;
        }
        
        // Очистить таблицу
        tbody.innerHTML = '';
        
        if (warehouses.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center">Нет складов</td></tr>';
            return;
        }
        
        // Заполнить таблицу
        warehouses.forEach(wh => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong>${wh.code}</strong></td>
                <td>${wh.name}</td>
                <td>${wh.address || '-'}</td>
                <td>${wh.phone || '-'}</td>
                <td>${wh.manager || '-'}</td>
                <td><span class="badge bg-${wh.is_active ? 'success' : 'danger'}">${wh.is_active ? 'Активен' : 'Неактивен'}</span></td>
                <td>
                    <button class="btn btn-sm btn-info" onclick="showEditWarehouse(${wh.id})" title="Редактировать">✏️</button>
                    <button class="btn btn-sm btn-primary" onclick="showWarehouseStats('${wh.code}')" title="Статистика">📊</button>
                    <button class="btn btn-sm btn-danger" onclick="deleteWarehouse(${wh.id})" title="Удалить">✕</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
        
        console.log('✅ Warehouses table updated with', warehouses.length, 'items');
        
    } catch (error) {
        console.error('❌ Error loading warehouses:', error);
        const tbody = document.getElementById('warehouses-table-body');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-danger">Ошибка загрузки складов</td></tr>';
        }
    }
}


    function loadCalendar() {
        const calendarEl = document.getElementById("calendar");
        if (!calendarEl || typeof FullCalendar === 'undefined') return;

        const calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: "dayGridMonth",
            locale: "ru",
            firstDay: 1,
            headerToolbar: {
                left: "prev,next today",
                center: "title",
                right: "dayGridMonth"
            },
            buttonText: { today: "Сегодня", month: "Месяц" },
            height: "auto",
            events: function(info, successCallback, failureCallback) {
                authFetch('/api/tracks/calendar-events')
                .then(r => r.json())
                .then(data => successCallback(data))
                .catch(err => failureCallback(err));
            }
        });

        calendar.render();
        console.log("✅ Calendar rendered");
    }

    document.querySelector(".logout")?.addEventListener("click", (e) => {
        e.preventDefault();
        localStorage.removeItem("token");
        window.location.href = "/login";
    });
    // Загрузить склады в форму добавления пользователя
    async function loadWarehousesForUserForm() {
        try {
            const res = await authFetch('/api/warehouses/active');
            if (!res.ok) return;

            const warehouses = await res.json();
            const select = document.getElementById('user-branch');
            
            if (select) {
                const placeholder = select.querySelector('option[value=""]');
                select.innerHTML = '';
                if (placeholder) select.appendChild(placeholder.cloneNode(true));
                
                warehouses.forEach(wh => {
                    const option = document.createElement('option');
                    option.value = wh.name; // Сохраняем название склада в branch
                    option.textContent = `${wh.name} (${wh.code})`;
                    select.appendChild(option);
                });
                console.log('✅ Warehouses loaded for user form');
            }
        } catch (error) {
            console.error('❌ Error loading warehouses for form:', error);
        }
    }

    // Вызвать при загрузке страницы
    loadWarehousesForUserForm();

    console.log("✅ Superadmin loaded");
});
