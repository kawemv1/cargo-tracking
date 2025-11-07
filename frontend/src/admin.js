// frontend/src/admin.js — финальная версия

// ===== Универсальная обёртка запросов c JWT и человекочитаемыми ошибками =====
async function authFetch(url, options = {}) {
  const token = localStorage.getItem('token');
  options.headers = options.headers || {};
  if (token) options.headers.Authorization = `Bearer ${token}`;

  const res = await fetch(url, options);

  // Успех: вернуть распарсенный JSON или текст
  if (res.ok) {
    const contentType = res.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
      return await res.json();
    }
    return await res.text();
  }

  // Ошибки: попытаться вытащить detail/message
  let message = `HTTP ${res.status}`;
  try {
    const data = await res.json();
    message = data?.detail || data?.message || JSON.stringify(data);
  } catch {
    try {
      const txt = await res.text();
      if (txt) message = txt;
    } catch {}
  }
  throw new Error(message);
}

// ===== Склады =====
async function loadWarehouses() {
  try {
    console.log('📦 Loading warehouses...');
    const warehouses = await authFetch('/api/warehouses/active');

    const selects = {
      'user-branch-warehouse': (wh) => wh.name,
      'user-assigned-warehouse': (wh) => wh.code,
      'upload-warehouse': (wh) => wh.code,
      'batch-warehouse': (wh) => wh.code,
      'filter-warehouse': (wh) => wh.code
    };

    Object.keys(selects).forEach(selectId => {
      const select = document.getElementById(selectId);
      if (!select) {
        console.warn(`⚠️ #${selectId} not found`);
        return;
      }

      const placeholder = select.querySelector('option[value=""]');
      select.innerHTML = '';
      if (placeholder) select.appendChild(placeholder.cloneNode(true));

      warehouses.forEach(wh => {
        const option = document.createElement('option');
        option.value = selects[selectId](wh);
        option.textContent = `${wh.name} (${wh.code})`;
        select.appendChild(option);
      });
      console.log(`✅ Populated #${selectId}`);
    });
  } catch (error) {
    console.error('❌ Error loading warehouses:', error);
  }
}

// ===== Календарь =====
function loadCalendar() {
  const calendarEl = document.getElementById('calendar');
  if (!calendarEl) return;

  if (typeof FullCalendar === 'undefined') {
    console.error('❌ FullCalendar not loaded');
    return;
  }

  const token = localStorage.getItem('token');

  const calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: 'dayGridMonth',
    locale: 'ru',
    firstDay: 1,
    headerToolbar: { left: 'prev,next today', center: 'title', right: 'dayGridMonth' },
    buttonText: { today: 'Сегодня', month: 'Месяц' },
    height: 'auto',
    events: function(info, successCallback, failureCallback) {
      fetch('/api/tracks/calendar-events', {
        headers: { Authorization: `Bearer ${token}` }
      })
        .then(async res => {
          if (res.ok) return res.json();
          try {
            const data = await res.json();
            throw new Error(data?.detail || data?.message || 'Failed');
          } catch {
            const txt = await res.text();
            throw new Error(txt || `HTTP ${res.status}`);
          }
        })
        .then(successCallback)
        .catch(err => failureCallback(err.message || String(err)));
    },
    eventClick: function(info) { showDateTracks(info.event.startStr); },
    eventDidMount: function(info) { info.el.title = info.event.title; }
  });

  calendar.render();
  window.calendarInstance = calendar;
  console.log('✅ Calendar rendered');
}

// ===== Треки по дате + батч-операции =====
async function showDateTracks(date) {
  try {
    const tracks = await authFetch(`/api/tracks/by-date/${date}`);

    document.getElementById('selected-date').textContent = date;
    document.getElementById('total-tracks').textContent = tracks.length;

    const tbody = document.getElementById('tracks-list-body');
    tbody.innerHTML = '';

    tracks.forEach(track => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${track.track_number}</td>
        <td>${track.current_status || '-'}</td>
        <td>${track.personal_code || '-'}</td>
      `;
      tbody.appendChild(tr);
    });

    const modal = new bootstrap.Modal(document.getElementById('dateTracksModal'));
    modal.show();

    // Массовое обновление статусов
    document.getElementById('batch-update-form').onsubmit = async (e) => {
      e.preventDefault();
      const newStatus = document.getElementById('batch-new-status').value;
      if (!newStatus) {
        alert('⚠️ Выберите статус');
        return;
      }
      const formData = new FormData();
			formData.append('file', file);
			formData.append('china_departure', date);
			formData.append('current_status', status);
			formData.append('warehouse', warehouse);

			uploadBtn.disabled = true;
			uploadBtn.innerHTML = 'Загрузка...';

			try {
			const result = await authFetch('/api/tracks/upload', { method: 'POST', body: formData });
			alert(`✅ Загружено: ${result.imported || result.count || 0}`);
			fileInput.value = '';
			dateInput.value = '';
			statusSelect.value = '';
			document.getElementById('upload-warehouse').value = '';
			if (window.calendarInstance) window.calendarInstance.refetchEvents();
			} catch (error) {
			// Если сервер вернул массив ошибок внутри строки JSON, отобразим компактно
			let msg = error.message;
			try {
					const parsed = JSON.parse(error.message);
					if (Array.isArray(parsed)) {
					msg = parsed.map(e => (e.msg || e.detail || e)).join('\n');
					} else if (parsed.detail) {
					msg = parsed.detail;
					}
			} catch {}
			alert('❌ ' + msg);
			} finally {
			uploadBtn.disabled = false;
			uploadBtn.innerHTML = '📤 Загрузить';
			}


// ===== Пользователи: удалить / активировать =====
window.deleteUser = async function(userId) {
  if (!confirm('Удалить пользователя?')) return;
  try {
    await authFetch(`/api/users/${userId}`, { method: 'DELETE' });
    alert('Пользователь удалён');
    location.reload();
  } catch (err) {
    alert(`Ошибка удаления: ${err.message}`);
  }
};

window.toggleUserActive = async function(userId) {
  if (!confirm('Изменить статус пользователя?')) return;
  try {
    await authFetch(`/api/users/${userId}/toggle-active`, { method: 'POST' });
    alert('✅ Статус изменён');
    location.reload();
  } catch (err) {
    alert(`❌ Ошибка: ${err.message}`);
  }
};

// ===== Экспорт пользователей =====
window.exportUsers = async function() {
  try {
    // тут используем обычный fetch, потому что ждём blob
    const token = localStorage.getItem('token');
    const res = await fetch('/api/users/export?format=csv', {
      headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `users_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
    alert('✅ Экспорт завершён');
  } catch (error) {
    alert(`❌ Ошибка экспорта: ${error.message}`);
  }
};

// ===== Инициализация =====
document.addEventListener('DOMContentLoaded', async () => {
  console.log('🚀 Admin.js starting...');

  const token = localStorage.getItem('token');
  if (!token) {
    window.location.href = '/login';
    return;
  }

  try {
    // Проверка авторизации
    const user = await authFetch('/api/auth/me');

    if (!['admin', 'superadmin', 'warehouse_admin'].includes(user.role)) {
      window.location.href = '/';
      return;
    }

    const adminName = document.getElementById('admin-name');
    if (adminName) adminName.textContent = `${user.name} (${user.role})`;

    console.log('✅ Auth OK:', user.email);

    await loadWarehouses();

    window.addEventListener('storage', (e) => {
      if (e.key === 'warehouses_updated') loadWarehouses();
    });

    // DOM-элементы
    const form = document.getElementById('add-user-form');
    const usersTableContainer = document.getElementById('users-table-container');
    const usersTableBody = document.querySelector('#users-table tbody');
    const toggleBtn = document.getElementById('toggle-users-btn');
    const uploadBtn = document.getElementById('upload-tracks-btn');
    const dateInput = document.getElementById('china-date');
    const fileInput = document.getElementById('tracks-file');
    const statusSelect = document.getElementById('track-status-select');
    const scannerInput = document.getElementById('scanner-input');
    const scannedContainer = document.getElementById('scanned-tracks-container');
    const scannedTbody = document.getElementById('scanned-tracks-tbody');
    let scannedTracks = [];

    // ===== Фильтр пользователей =====
    async function loadUsersFiltered() {
      console.log('🔍 Loading filtered users...');
      const search = document.getElementById('user-search')?.value?.trim() || '';
      const role = document.getElementById('filter-role')?.value || '';
      const warehouse = document.getElementById('filter-warehouse')?.value || '';
      const sortBy = document.getElementById('sort-by')?.value || 'name';
      const order = document.getElementById('sort-order')?.value || 'asc';

      const params = new URLSearchParams();
      if (search) params.append('search', search);
      if (role) params.append('role', role);
      if (warehouse) params.append('warehouse', warehouse);
      params.append('sort_by', sortBy);
      params.append('order', order);

      try {
        const users = await authFetch(`/api/users/filter?${params.toString()}`);

        if (!usersTableBody) {
          console.error('❌ usersTableBody not found');
          return;
        }

        usersTableBody.innerHTML = '';

        if (!users.length) {
          usersTableBody.innerHTML = '<tr><td colspan="8" class="text-center">Ничего не найдено</td></tr>';
          return;
        }

        users.forEach(user => {
          const tr = document.createElement('tr');
          const isActive = user.is_active !== false;
          tr.innerHTML = `
            <td>${user.personalcode || user.id}</td>
            <td>${user.name}</td>
            <td>${user.email}</td>
            <td>${user.whatsapp || '-'}</td>
            <td>${user.branch || '-'}</td>
            <td><span class="badge bg-${isActive ? 'success' : 'danger'}">${user.role || 'client'}</span></td>
            <td>${user.assigned_warehouse || '-'}</td>
            <td>
              <button class="btn btn-sm btn-warning" onclick="toggleUserActive(${user.id})">${isActive ? '🔒' : '🔓'}</button>
              <button class="btn btn-sm btn-danger" onclick="deleteUser(${user.id})">✕</button>
            </td>
          `;
          usersTableBody.appendChild(tr);
        });
      } catch (error) {
        console.error('❌ Error filtering users:', error);
        if (usersTableBody) {
          usersTableBody.innerHTML = '<tr><td colspan="8">Ошибка загрузки</td></tr>';
        }
      }
    }

    function debounce(func, wait) {
      let timeout;
      return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func(...args), wait);
      };
    }

    // Роль warehouse_admin — показать назначение склада
    const roleSelect = document.getElementById('user-role');
    if (roleSelect) {
      roleSelect.addEventListener('change', (e) => {
        const container = document.getElementById('warehouse-admin-assignment-container');
        const select = document.getElementById('user-assigned-warehouse');
        if (e.target.value === 'warehouse_admin') {
          if (container) container.style.display = 'block';
          if (select) select.required = true;
        } else {
          if (container) container.style.display = 'none';
          if (select) select.required = false;
        }
      });
    }

    // Добавление пользователя
    if (form) {
      form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const role = document.getElementById('user-role').value;
        const formData = new FormData();

        formData.append('name', document.getElementById('user-name').value);
        formData.append('email', document.getElementById('user-email').value);
        formData.append('password', document.getElementById('user-password').value);
        formData.append('whatsapp', document.getElementById('user-whatsapp').value);

        const branch = document.getElementById('user-branch-warehouse')?.value;
        if (!branch) {
          alert('⚠️ Выберите склад');
          return;
        }
        formData.append('branch', branch);
        formData.append('role', role);

        const personalCode = document.getElementById('user-personal-code')?.value;
        if (personalCode) formData.append('personalcode', personalCode);

        if (role === 'warehouse_admin') {
          const warehouse = document.getElementById('user-assigned-warehouse')?.value;
          if (!warehouse) {
            alert('⚠️ Выберите назначенный склад');
            return;
          }
          formData.append('assigned_warehouse', warehouse);
        }

        try {
          await authFetch('/api/users', { method: 'POST', body: formData });
          alert('✅ Пользователь добавлен!');
          form.reset();
          const container = document.getElementById('warehouse-admin-assignment-container');
          if (container) container.style.display = 'none';

          if (usersTableContainer && usersTableContainer.style.display !== 'none') {
            loadUsersFiltered();
          }
        } catch (error) {
          alert('❌ ' + error.message);
        }
      });
    }

    // Показать/скрыть таблицу пользователей
    if (toggleBtn) {
      toggleBtn.addEventListener('click', () => {
        if (usersTableContainer.style.display === 'none') {
          usersTableContainer.style.display = 'block';
          toggleBtn.textContent = 'Скрыть';
          loadUsersFiltered();
        } else {
          usersTableContainer.style.display = 'none';
          toggleBtn.textContent = 'Показать';
        }
      });
    }

    // Привязка фильтров
    const debouncedFilter = debounce(loadUsersFiltered, 300);
    document.getElementById('user-search')?.addEventListener('input', debouncedFilter);
    document.getElementById('filter-role')?.addEventListener('change', loadUsersFiltered);
    document.getElementById('filter-warehouse')?.addEventListener('change', loadUsersFiltered);
    document.getElementById('sort-by')?.addEventListener('change', loadUsersFiltered);
    document.getElementById('sort-order')?.addEventListener('change', loadUsersFiltered);

    // Загрузка треков
    if (uploadBtn) {
      uploadBtn.addEventListener('click', async () => {
        const date = document.getElementById('china-date').value;
        const file = document.getElementById('tracks-file').files[0];
        const status = document.getElementById('track-status-select').value;
        const warehouse = document.getElementById('upload-warehouse')?.value;

        if (!file || !date || !status || !warehouse) {
          alert('⚠️ Заполните все поля!');
          return;
        }

        const formData = new FormData();
        formData.append('file', file);
        formData.append('china_departure', date);       // ИМЕНА ПАРАМЕТРОВ СЕРВЕРА
        formData.append('current_status', status);      // НЕ 'status'
        formData.append('warehouse', warehouse);

        uploadBtn.disabled = true;
        uploadBtn.innerHTML = 'Загрузка...';

        try {
          const result = await authFetch('/api/tracks/upload', { method: 'POST', body: formData });
          alert(`✅ Загружено: ${result.imported || result.count || 0}`);
          document.getElementById('tracks-file').value = '';
          document.getElementById('china-date').value = '';
          document.getElementById('track-status-select').value = '';
          document.getElementById('upload-warehouse').value = '';
          if (window.calendarInstance) window.calendarInstance.refetchEvents();
        } catch (error) {
          alert('❌ ' + error.message);
        } finally {
          uploadBtn.disabled = false;
          uploadBtn.innerHTML = '📤 Загрузить';
        }
      });
    }

    // Поиск трека
    const searchBtn = document.getElementById('track-search-btn');
    const searchInput = document.getElementById('track-search');
    const trackResult = document.getElementById('track-result');

    if (searchBtn) {
      searchBtn.addEventListener('click', async () => {
        const trackNumber = searchInput.value.trim().toUpperCase();
        if (!trackNumber) return;
        try {
          const track = await authFetch(`/api/tracks/search/${trackNumber}`);
          trackResult.innerHTML = `
            <div class="alert alert-success">
              <h5>🔍 ${track.track_number}</h5>
              <p><strong>Статус:</strong> ${track.current_status || '-'}</p>
              <p><strong>Код:</strong> ${track.personal_code || '-'}</p>
            </div>
          `;
        } catch (error) {
          trackResult.innerHTML = '<div class="alert alert-danger">Не найден</div>';
        }
      });
    }

    // Сканнер
    if (scannerInput) {
      scannerInput.addEventListener('keypress', async (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          const trackNumber = scannerInput.value.trim().toUpperCase();

          if (!trackNumber || scannedTracks.includes(trackNumber)) {
            scannerInput.value = '';
            return;
          }

          try {
            const track = await authFetch(`/api/tracks/search/${trackNumber}`);
            scannedTracks.push(trackNumber);

            const tr = document.createElement('tr');
            tr.innerHTML = `
              <td>${scannedTracks.length}</td>
              <td>${track.track_number}</td>
              <td>${track.current_status || '-'}</td>
              <td>${track.personal_code || '-'}</td>
              <td><button class="btn btn-sm btn-danger" onclick="removeScanned('${trackNumber}')">✕</button></td>
            `;
            scannedTbody.appendChild(tr);

            document.getElementById('scanned-count').textContent = scannedTracks.length;
            document.getElementById('deliver-count').textContent = scannedTracks.length;
            document.getElementById('delete-count').textContent = scannedTracks.length;

            scannedContainer.style.display = 'block';
          } catch (error) {
            // ignore
          }

          scannerInput.value = '';
          scannerInput.focus();
        }
      });
    }

    // Выдать отсканированные
    document.getElementById('deliver-scanned-btn')?.addEventListener('click', async () => {
      if (scannedTracks.length === 0) return;
      if (!confirm(`Выдать ${scannedTracks.length} посылок?`)) return;

      try {
        const formData = new FormData();
        formData.append('tracknumbers', scannedTracks.join(','));
        const result = await authFetch('/api/tracks/deliver-batch', { method: 'POST', body: formData });
        alert(`Выдано: ${result.delivered}`);
        scannedTracks = [];
        scannedTbody.innerHTML = '';
        scannedContainer.style.display = 'none';
      } catch (error) {
        alert(`Ошибка выдачи: ${error.message}`);
      }
    });

    // Удалить отсканированные
    document.getElementById('delete-scanned-btn')?.addEventListener('click', async () => {
      if (scannedTracks.length === 0) return;
      if (!confirm(`Удалить ${scannedTracks.length} треков?`)) return;

      try {
        const formData = new FormData();
        formData.append('tracknumbers', scannedTracks.join(','));
        await authFetch('/api/tracks/delete-batch', { method: 'POST', body: formData });
        alert('Удалено');
        scannedTracks = [];
        scannedTbody.innerHTML = '';
        scannedContainer.style.display = 'none';
      } catch (error) {
        alert(`Ошибка удаления: ${error.message}`);
      }
    });

    // Очистить список сканирования
    document.getElementById('clear-scanned-btn')?.addEventListener('click', () => {
      scannedTracks = [];
      scannedTbody.innerHTML = '';
      scannedContainer.style.display = 'none';
      if (scannerInput) scannerInput.focus();
    });

    // Удалить один из списка
    window.removeScanned = function(trackNumber) {
      scannedTracks = scannedTracks.filter(t => t !== trackNumber);
      scannedTbody.innerHTML = '';
      scannedTracks.forEach((t, i) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td>${i + 1}</td>
          <td>${t}</td>
          <td>-</td>
          <td>-</td>
          <td><button class="btn btn-sm btn-danger" onclick="removeScanned('${t}')">✕</button></td>
        `;
        scannedTbody.appendChild(tr);
      });
      const count = scannedTracks.length;
      document.getElementById('scanned-count').textContent = count;
      document.getElementById('deliver-count').textContent = count;
      document.getElementById('delete-count').textContent = count;
      if (!count) scannedContainer.style.display = 'none';
    };

    // Календарь
    loadCalendar();

    // Выход
    document.querySelector('.logout')?.addEventListener('click', (e) => {
      e.preventDefault();
      localStorage.removeItem('token');
      window.location.href = '/login';
    });

    console.log('✅ Admin.js loaded');
  } catch (error) {
    console.error('❌ Error:', error);
    localStorage.removeItem('token');
    window.location.href = '/login';
  }
});
