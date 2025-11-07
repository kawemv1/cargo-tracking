// frontend/src/track-history.js

document.addEventListener('DOMContentLoaded', async () => {
    // ========== AUTHENTICATION CHECK ==========
    const token = localStorage.getItem('token');

    if (!token) {
        alert('⛔ Доступ запрещен. Требуется авторизация.');
        window.location.href = '/login';
        return;
    }

    try {
        const response = await fetch('/api/auth/me', {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) {
            localStorage.removeItem('token');
            alert('⛔ Сессия истекла. Войдите снова.');
            window.location.href = '/login';
            return;
        }

        const user = await response.json();

        // Check admin or superadmin role
        if (user.role !== 'admin' && user.role !== 'superadmin') {
            alert('⛔ Доступ запрещен. Только для администраторов.');
            window.location.href = '/';
            return;
        }

        document.getElementById('admin-name').textContent = user.name;
        console.log('✅ Auth OK:', user.name);

    } catch (error) {
        console.error('❌ Auth error:', error);
        window.location.href = '/login';
        return;
    }

    // ========== HELPER FUNCTION ==========
    async function authFetch(url, options = {}) {
        const token = localStorage.getItem('token');
        if (!options.headers) {
            options.headers = {};
        }
        options.headers['Authorization'] = `Bearer ${token}`;
        return fetch(url, options);
    }

    // ========== GLOBAL STATE ==========
    let allTracks = [];
    let filteredTracks = [];
    let currentPage = 1;
    const itemsPerPage = 15;

    // ========== LOAD ALL TRACKS ==========
    async function loadAllTracks() {
        try {
            const res = await authFetch('/api/tracks/all');

            if (!res.ok) {
                throw new Error('Failed to load tracks');
            }

            allTracks = await res.json();
            filteredTracks = [...allTracks];

            console.log('✅ Loaded', allTracks.length, 'tracks');

            updateResultsInfo();
            renderTable();
            renderPagination();

        } catch (error) {
            console.error('❌ Error loading tracks:', error);
            document.getElementById('tracks-tbody').innerHTML = `
                <tr>
                    <td colspan="6" class="text-center text-danger py-4">
                        Ошибка загрузки треков
                    </td>
                </tr>
            `;
        }
    }

    // ========== SEARCH TRACKS ==========
    document.getElementById('search-form').addEventListener('submit', (e) => {
        e.preventDefault();

        const searchTerm = document.getElementById('search-input').value.trim().toUpperCase();

        if (searchTerm === '') {
            filteredTracks = [...allTracks];
        } else {
            filteredTracks = allTracks.filter(track => 
                track.track_number.includes(searchTerm) ||
                (track.personal_code && track.personal_code.includes(searchTerm))
            );
        }

        currentPage = 1;
        updateResultsInfo();
        renderTable();
        renderPagination();

        console.log('🔍 Search:', searchTerm, 'Found:', filteredTracks.length);
    });

    // ========== UPDATE RESULTS INFO ==========
    function updateResultsInfo() {
        const start = (currentPage - 1) * itemsPerPage + 1;
        const end = Math.min(currentPage * itemsPerPage, filteredTracks.length);

        document.getElementById('results-count').textContent = 
            filteredTracks.length > 0 ? `${start} - ${end}` : '0';
        document.getElementById('total-count').textContent = filteredTracks.length;
    }

    // ========== RENDER TABLE ==========
    function renderTable() {
        const tbody = document.getElementById('tracks-tbody');

        if (filteredTracks.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center py-5">
                        <p class="text-muted">Треки не найдены</p>
                    </td>
                </tr>
            `;
            return;
        }

        const start = (currentPage - 1) * itemsPerPage;
        const end = start + itemsPerPage;
        const pageItems = filteredTracks.slice(start, end);

        tbody.innerHTML = '';

        pageItems.forEach((track, index) => {
            const globalIndex = start + index + 1;
            const statusClass = getStatusClass(track.status);
            const createdDate = track.created_at ? 
                new Date(track.created_at).toLocaleString('ru-RU') : '-';
            const departureDate = track.departure_date ? 
                new Date(track.departure_date).toLocaleDateString('ru-RU') : '-';

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><span class="track-id">${globalIndex}</span></td>
                <td><strong>${track.track_number}</strong></td>
                <td><span class="status-badge ${statusClass}">${track.status}</span></td>
                <td>${createdDate}</td>
                <td>${departureDate}</td>
                <td>
                    <button class="history-btn" onclick="showTrackHistory('${track.track_number}')">
                        История
                    </button>
                </td>
            `;

            tbody.appendChild(tr);
        });
    }

    // ========== GET STATUS CLASS ==========
    function getStatusClass(status) {
        if (!status) return 'status-transit';

        const statusLower = status.toLowerCase();

        if (statusLower.includes('выдан') || statusLower.includes('delivered')) {
            return 'status-delivered';
        } else if (statusLower.includes('склад') || statusLower.includes('warehouse')) {
            return 'status-warehouse';
        } else {
            return 'status-transit';
        }
    }

    // ========== RENDER PAGINATION ==========
    function renderPagination() {
        const totalPages = Math.ceil(filteredTracks.length / itemsPerPage);
        const pagination = document.getElementById('pagination');

        if (totalPages <= 1) {
            pagination.innerHTML = '';
            return;
        }

        let html = '';

        // Previous button
        html += `
            <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
                <a class="page-link" href="#" onclick="changePage(${currentPage - 1}); return false;">
                    &lt;
                </a>
            </li>
        `;

        // Page numbers
        const maxVisible = 5;
        let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
        let endPage = Math.min(totalPages, startPage + maxVisible - 1);

        if (endPage - startPage < maxVisible - 1) {
            startPage = Math.max(1, endPage - maxVisible + 1);
        }

        for (let i = startPage; i <= endPage; i++) {
            html += `
                <li class="page-item ${i === currentPage ? 'active' : ''}">
                    <a class="page-link" href="#" onclick="changePage(${i}); return false;">
                        ${i}
                    </a>
                </li>
            `;
        }

        // Next button
        html += `
            <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
                <a class="page-link" href="#" onclick="changePage(${currentPage + 1}); return false;">
                    &gt;
                </a>
            </li>
        `;

        pagination.innerHTML = html;
    }

    // ========== CHANGE PAGE ==========
    window.changePage = function(page) {
        const totalPages = Math.ceil(filteredTracks.length / itemsPerPage);

        if (page < 1 || page > totalPages) return;

        currentPage = page;
        updateResultsInfo();
        renderTable();
        renderPagination();

        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    // ========== SHOW TRACK HISTORY ==========
    window.showTrackHistory = async function(trackNumber) {
        const modalBody = document.getElementById('modal-body');
        modalBody.innerHTML = '<div class="text-center"><div class="spinner-border"></div><p class="mt-2">Загрузка...</p></div>';

        const modal = new bootstrap.Modal(document.getElementById('trackModal'));
        modal.show();

        try {
            const res = await authFetch(`/api/tracks/search/${trackNumber}`);

            if (!res.ok) {
                throw new Error('Track not found');
            }

            const track = await res.json();

            let html = `
                <div class="mb-3">
                    <h5>Трек-номер: <strong>${track.tracknumber}</strong></h5>
                </div>
                <table class="table table-bordered">
                    <tbody>
                        <tr>
                            <th style="width: 200px;">Статус</th>
                            <td><span class="status-badge ${getStatusClass(track.status)}">${track.status}</span></td>
                        </tr>
                        <tr>
                            <th>Личный код</th>
                            <td>${track.personalcode || '-'}</td>
                        </tr>
                        <tr>
                            <th>Дата отправления</th>
                            <td>${track.departuredate ? new Date(track.departuredate).toLocaleDateString('ru-RU') : '-'}</td>
                        </tr>
                        <tr>
                            <th>Дата прибытия</th>
                            <td>${track.arrivaldate ? new Date(track.arrivaldate).toLocaleDateString('ru-RU') : '-'}</td>
                        </tr>
                        <tr>
                            <th>Текущий склад</th>
                            <td>${track.currentwarehouse || '-'}</td>
                        </tr>
                    </tbody>
                </table>
            `;

            // Check if there's handout info
            if (track.handout_date || track.handed_by) {
                html += `
                    <div class="alert alert-success mt-3">
                        <strong>✅ Выдано</strong><br>
                        ${track.handout_date ? 'Дата: ' + new Date(track.handout_date).toLocaleString('ru-RU') + '<br>' : ''}
                        ${track.handed_by ? 'Кем: ' + track.handed_by : ''}
                    </div>
                `;
            }

            modalBody.innerHTML = html;

        } catch (error) {
            console.error('Error loading track history:', error);
            modalBody.innerHTML = '<p class="text-danger">Ошибка загрузки данных трека</p>';
        }
    };

    // ========== LOGOUT ==========
    document.querySelector('.logout').addEventListener('click', (e) => {
        e.preventDefault();
        localStorage.removeItem('token');
        window.location.href = '/login';
    });

    // ========== INITIAL LOAD ==========
    loadAllTracks();

    console.log('✅ Track history page loaded');
});
