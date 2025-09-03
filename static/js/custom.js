// ===== ОБЩИЕ ФУНКЦИИ ДЛЯ ФОРМ БРОНИРОВАНИЯ =====

// Функция для обновления доступных столиков
function updateAvailableTables(hallSelect, dateInput, timeInput, guestsInput, tableSelect, loadingDiv) {
    const hallId = hallSelect.value;
    const date = dateInput.value;
    const time = timeInput.value;
    const guests = guestsInput.value || 1;

    if (!hallId || !date || !time) {
        tableSelect.innerHTML = '<option value="">-- Сначала выберите зал, дату и время --</option>';
        return;
    }

    // Показываем загрузку
    if (loadingDiv) loadingDiv.style.display = 'block';
    tableSelect.disabled = true;

    fetch(`/api/tables-by-hall/${hallId}/?date=${date}&time=${time}&guests=${guests}`)
        .then(response => response.json())
        .then(data => {
            tableSelect.innerHTML = '<option value="">-- Выберите столик --</option>';

            if (data.tables && data.tables.length > 0) {
                data.tables.forEach(table => {
                    const option = document.createElement('option');
                    option.value = table.id;
                    option.textContent = `Стол ${table.number} (${table.capacity} чел.)`;
                    tableSelect.appendChild(option);
                });
            } else {
                tableSelect.innerHTML = '<option value="">Нет доступных столиков</option>';
            }
        })
        .catch(error => {
            console.error('Ошибка:', error);
            tableSelect.innerHTML = '<option value="">Ошибка загрузки столиков</option>';
        })
        .finally(() => {
            if (loadingDiv) loadingDiv.style.display = 'none';
            tableSelect.disabled = false;
        });
}

// Функция для обновления ссылки на схему зала
function updateHallSchemaLink(hallSelect, schemaLink) {
    const hallId = hallSelect.value;
    if (hallId && schemaLink) {
        schemaLink.style.display = 'inline';
        schemaLink.href = `/hall/${hallId}/schema/`;
    } else if (schemaLink) {
        schemaLink.style.display = 'none';
    }
}

// Инициализация формы бронирования
function initReservationForm() {
    const hallSelect = document.getElementById('id_hall');
    const dateInput = document.querySelector('input[name="date"]');
    const timeInput = document.querySelector('input[name="start_time"]');
    const guestsInput = document.getElementById('id_guests_count');
    const tableSelect = document.getElementById('id_table');
    const schemaLink = document.getElementById('view-hall-schema');
    const loadingDiv = document.getElementById('table-loading');

    if (!hallSelect) return; // Если нет формы на странице

    // Слушаем изменения полей
    hallSelect.addEventListener('change', function() {
        updateHallSchemaLink(hallSelect, schemaLink);
        updateAvailableTables(hallSelect, dateInput, timeInput, guestsInput, tableSelect, loadingDiv);
    });

    dateInput.addEventListener('change', function() {
        updateAvailableTables(hallSelect, dateInput, timeInput, guestsInput, tableSelect, loadingDiv);
    });

    timeInput.addEventListener('change', function() {
        updateAvailableTables(hallSelect, dateInput, timeInput, guestsInput, tableSelect, loadingDiv);
    });

    guestsInput.addEventListener('change', function() {
        updateAvailableTables(hallSelect, dateInput, timeInput, guestsInput, tableSelect, loadingDiv);
    });

    // Инициализируем при загрузке страницы
    updateHallSchemaLink(hallSelect, schemaLink);
}

// ===== ИНИЦИАЛИЗАЦИЯ ВСЕХ КОМПОНЕНТОВ =====
document.addEventListener('DOMContentLoaded', function() {
    // Закрытие alert сообщений (общая функция)
    document.querySelectorAll('.close-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            this.parentElement.style.display = 'none';
        });
    });

    // Инициализация формы бронирования
    initReservationForm();
});

// ===== ФУНКЦИИ ДЛЯ СХЕМЫ ЗАЛА =====

// Инициализация схемы зала
function initHallSchema() {
    const tableCards = document.querySelectorAll('.table-available');
    const continueBtn = document.getElementById('continue-booking-btn');
    const selectedTableInfo = document.getElementById('selected-table-info');
    const selectedTableDetails = document.getElementById('selected-table-details');

    if (!tableCards.length) return; // Если нет схемы на странице

    let selectedTableId = null;
    let selectedHallId = null;

    tableCards.forEach(card => {
        card.addEventListener('click', function() {
            // Снимаем выделение со всех столиков
            tableCards.forEach(t => t.classList.remove('table-selected'));

            // Выделяем выбранный столик
            this.classList.add('table-selected');

            // Сохраняем данные выбранного столика
            selectedTableId = this.dataset.tableId;
            selectedHallId = this.dataset.hallId;
            const tableNumber = this.dataset.tableNumber;
            const tableCapacity = this.dataset.tableCapacity;
            const hallName = this.dataset.hallName;

            // Показываем информацию о выбранном столике
            selectedTableDetails.innerHTML = `
                <strong>Зал:</strong> ${hallName}<br>
                <strong>Столик:</strong> ${tableNumber}<br>
                <strong>Вместимость:</strong> ${tableCapacity} человек
            `;
            selectedTableInfo.style.display = 'block';

            // Обновляем ссылку для продолжения бронирования
            const bookingUrl = `${continueBtn.href.split('?')[0]}?hall_id=${selectedHallId}&table_id=${selectedTableId}`;
            continueBtn.href = bookingUrl;
            continueBtn.style.display = 'block';
        });
    });

    // Обработчик для кнопки "Продолжить бронирование"
    if (continueBtn) {
        continueBtn.addEventListener('click', function(e) {
            if (!selectedTableId) {
                e.preventDefault();
                alert('Пожалуйста, выберите столик для бронирования');
            }
        });
    }
}

// ===== ОБНОВЛЕНИЕ ИНИЦИАЛИЗАЦИИ =====
document.addEventListener('DOMContentLoaded', function() {
    // Закрытие alert сообщений (общая функция)
    document.querySelectorAll('.close-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            this.parentElement.style.display = 'none';
        });
    });

    // Инициализация формы бронирования
    initReservationForm();

    // Инициализация схемы зала
    initHallSchema();
});