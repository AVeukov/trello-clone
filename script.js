document.addEventListener('DOMContentLoaded', () => {
  if (!localStorage.getItem('boards')) {
    localStorage.setItem('boards', '{}');
  }
  const deleteBoardModal = document.getElementById('deleteBoardModal');
  const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
  const cancelDeleteBtn = document.getElementById('cancelDeleteBtn');
  let boardIdToDelete = null;

  const startScreen = document.getElementById('startScreen');
  const columnSetup = document.getElementById('columnSetup');
  const boardNameInput = document.getElementById('boardName');
  const createBoardBtn = document.getElementById('createBoardBtn');
  const setupColumnsBtn = document.getElementById('setupColumnsBtn');
  const boardList = document.getElementById('boardList');

  const mainBoard = document.getElementById('mainBoard');
  const columnsContainer = document.getElementById('columns');
  const addColumnBtn = document.getElementById('addColumnBtn');
  const cardModal = document.getElementById('cardModal');
  const cardText = document.getElementById('cardText');
  const cardDate = document.getElementById('cardDate');
  const saveCardBtn = document.getElementById('saveCardBtn');
  const cancelCardBtn = document.getElementById('cancelCardBtn');

  const cardDescription = document.getElementById('cardDescription');
  const cardTags = document.getElementById('cardTags');
  const customTagInput = document.getElementById('customTagInput');


  const calendarBtn = document.getElementById('calendarViewBtn');
  const calendarView = document.getElementById('calendarView');
  const backToBoardBtn = document.getElementById('backToBoardBtn');
  const calendarEl = document.getElementById('calendar');

  const tableBtn = document.getElementById('tableViewBtn');
  const tableView = document.getElementById('tableView');
  const backFromTableBtn = document.getElementById('backFromTableBtn');
  const tableBody = document.getElementById('tableBody');

  const addColumnModal = document.getElementById('addColumnModal');
  const newColumnName = document.getElementById('newColumnName');
  const confirmAddColumn = document.getElementById('confirmAddColumn');
  const cancelAddColumn = document.getElementById('cancelAddColumn');

  const editColumnModal = document.getElementById('editColumnModal');
  const editColumnName = document.getElementById('editColumnName');
  const confirmEditColumn = document.getElementById('confirmEditColumn');
  const cancelEditColumn = document.getElementById('cancelEditColumn');

  let columnToEdit = null;


  const backToStartBtn = document.getElementById('backToStartBtn');

  let currentColumn = null;
  let editCard = null;
  let currentBoardId = null;

  cardModal.classList.add('hidden');

  const cardViewPopup = document.getElementById('cardViewPopup');
  const closePopupBtn = document.getElementById('closePopupBtn');
  const editCardFromPopupBtn = document.getElementById('editCardFromPopupBtn');
  let currentViewedCard = null;

  const notificationsBtn = document.getElementById('notificationsBtn');

  function generateId() {
    return 'board-' + Math.random().toString(36).substr(2, 9);
  }

  function saveAllBoards(boards) {
    localStorage.setItem('boards', JSON.stringify(boards));
  }

  function loadAllBoards() {
    try {
      const data = localStorage.getItem('boards');
      return data ? JSON.parse(data) : {};
    } catch (e) {
      console.error('Ошибка при чтении boards из localStorage:', e);
      return {};
    }
  }

  function renderBoardList() {
    const boards = loadAllBoards();
    boardList.innerHTML = '';

    for (const [id, board] of Object.entries(boards)) {
      const btn = document.createElement('button');
      btn.textContent = board.name;
      btn.onclick = () => {
        currentBoardId = id;
        showMainBoard(board.columns);
      };
      boardList.appendChild(btn);
    }
  }

  function showMainBoard(columnsData) {
    startScreen.classList.add('hidden');
    columnSetup.classList.add('hidden');
    mainBoard.classList.remove('hidden');
    calendarView.classList.add('hidden');
    tableView.classList.add('hidden');

    columnsContainer.innerHTML = '';

    columnsData.forEach(col => {
      const column = createColumn(col.title, col.color || '#eaf6ff');
      const container = column.querySelector('.card-container');
      if (col.color) {
        column.style.setProperty('--column-color', col.color);
        const colorInput = column.querySelector('.color-picker');
        if (colorInput) colorInput.value = col.color;
      }

      col.cards?.forEach(card => {
        currentColumn = container;
        createCard(card.text, card.date, card.description || '', card.tags || [], card.id, card.color || '#eaf6ff', card.time || '09:00');
      });
      
    });
  }

  function createColumn(title = 'Новая колонка', color = '#eaf6ff') {
    const column = document.createElement('div');
    column.className = 'column';
    
    const columnTitle = document.createElement('div');
    columnTitle.className = 'column-title';
    columnTitle.textContent = title;


    const colorBtn = document.createElement('input');
    colorBtn.type = 'color';
    colorBtn.className = 'color-picker';
    colorBtn.title = 'Выбрать цвет колонки';
    colorBtn.value = color;
    column.style.setProperty('--column-color', color);  // дефолт

    colorBtn.oninput = () => {
      column.style.setProperty('--column-color', colorBtn.value);
      //updateColumnColor(column, colorBtn.value);
      saveState();
    };


    //column.appendChild(columnTitle);
    const headerWrapper = document.createElement('div');
    headerWrapper.style.display = 'flex';
    headerWrapper.style.justifyContent = 'space-between';
    headerWrapper.style.alignItems = 'center';
    headerWrapper.appendChild(columnTitle);
    headerWrapper.appendChild(colorBtn);
    column.appendChild(headerWrapper);

  
    const cardContainer = document.createElement('div');
    cardContainer.className = 'card-container';
    column.appendChild(cardContainer);
  
    column.addEventListener('dragover', e => e.preventDefault());
    column.addEventListener('drop', e => {
      const id = e.dataTransfer.getData('text/plain');
      const card = document.getElementById(id);
      cardContainer.appendChild(card);
      sortCardsByDate(cardContainer);
      saveState();
    });
  
    const addCardBtn = document.createElement('button');
    addCardBtn.className = 'add-card-btn';
    addCardBtn.textContent = 'Добавить карточку';
    addCardBtn.onclick = () => {
      currentColumn = cardContainer;
      editCard = null;
      cardText.value = '';
      cardDate.value = '';
      cardModal.classList.remove('hidden');
    };
  
    column.appendChild(addCardBtn);
    columnsContainer.appendChild(column);
  
    // === 🔽 Модальное редактирование заголовка колонки ===
    columnTitle.onclick = () => {
      columnToEdit = columnTitle;
      editColumnName.value = columnTitle.textContent;
      editColumnModal.classList.remove('hidden');
    };
  
    return column;
  }
  

  function createCard(text, date, description = '', tags = [], id = null, color = '#eaf6ff', time = '09:00') {
    if (!currentColumn) return;
  
    const card = document.createElement('div');
    card.className = 'card';
    card.draggable = true;
    card.id = id || 'card-' + Math.random().toString(36).substr(2, 9);
    card.style.backgroundColor = color;
  
    const cardTextDiv = document.createElement('div');
    cardTextDiv.className = 'card-text';
    cardTextDiv.textContent = text;
  
    const cardDescDiv = document.createElement('div');
    cardDescDiv.className = 'card-description';
    cardDescDiv.textContent = description;
  
    const cardDateDiv = document.createElement('div');
    cardDateDiv.className = 'card-date';
    cardDateDiv.textContent = date;
    cardDateDiv.dataset.time = time;
  
    const cardTagsDiv = document.createElement('div');
    cardTagsDiv.className = 'card-tags';
    cardTagsDiv.textContent = tags.join(', ');
  
    card.appendChild(cardTextDiv);
    if (description) card.appendChild(cardDescDiv);
    card.appendChild(cardDateDiv);
    if (tags.length > 0) card.appendChild(cardTagsDiv);
  
    const deleteBtn = document.createElement('button');
    deleteBtn.className = 'delete-btn';
    deleteBtn.textContent = '✕';
    deleteBtn.onclick = () => {
      card.remove();
      saveState();
    };
    card.appendChild(deleteBtn);
  
    card.ondragstart = e => {
      e.dataTransfer.setData('text/plain', card.id);
    };
  
    card.addEventListener('click', event => {
      if (event.target === deleteBtn) return;
      editCard = card;
      currentColumn = card.parentElement;
      cardText.value = card.querySelector('.card-text').textContent;
      const dateEl = card.querySelector('.card-date');
      cardDate.value = dateEl.textContent;
      document.getElementById('cardTime').value = dateEl.dataset.time || '09:00';
      document.getElementById('cardColor').value = card.style.backgroundColor || '#eaf6ff';
  
      const desc = card.querySelector('.card-description');
      document.getElementById('cardDescription').value = desc ? desc.textContent : '';
  
      const tagsText = card.querySelector('.card-tags')?.textContent || '';
      const tagList = tagsText.split(',').map(t => t.trim()).filter(Boolean);
      const tagSelect = document.getElementById('cardTags');
      const customInput = document.getElementById('customTagInput');
  
      // Сброс
      Array.from(tagSelect.options).forEach(opt => (opt.selected = false));
      customInput.value = '';
      customInput.classList.add('hidden');
  
      tagList.forEach(tag => {
        const match = Array.from(tagSelect.options).find(opt => opt.value === tag);
        if (match) {
          match.selected = true;
          if (tag === 'другое') customInput.classList.remove('hidden');
        } else {
          tagSelect.value = 'другое';
          customInput.value = tag;
          customInput.classList.remove('hidden');
        }
      });
  
      cardModal.classList.remove('hidden');
    });
  
    currentColumn.appendChild(card);
    sortCardsByDate(currentColumn);
  }
  
  

  function sortCardsByDate(container) {
    const cards = Array.from(container.querySelectorAll('.card'));
    cards.sort((a, b) => new Date(a.querySelector('.card-date').textContent) - new Date(b.querySelector('.card-date').textContent));
    cards.forEach(card => container.appendChild(card));
  }

  function saveState() {
    const boards = loadAllBoards();
    const currentBoard = boards[currentBoardId];
    if (!currentBoard) return;
  
    const columns = [];
    document.querySelectorAll('.column').forEach(column => {
      const columnTitle = column.querySelector('.column-title').textContent;
      const cards = [];
      column.querySelectorAll('.card').forEach(card => {
        const text = card.querySelector('.card-text')?.textContent || '';
        const dateEl = card.querySelector('.card-date');
        const date = dateEl?.textContent || '';
        const time = dateEl?.dataset.time || '09:00';
        const description = card.querySelector('.card-description')?.textContent || '';
        const tags = (card.querySelector('.card-tags')?.textContent || '')
          .split(',')
          .map(t => t.trim())
          .filter(Boolean);
        const color = card.style.backgroundColor || '#eaf6ff';
  
        cards.push({ text, date, time, description, tags, color });
      });
      const color = getComputedStyle(column).getPropertyValue('--column-color').trim();
      columns.push({ title: columnTitle, color, cards });

    });
  
    boards[currentBoardId] = {
      name: currentBoard.name,
      columns
    };
    saveAllBoards(boards);
  }
  
  

  saveCardBtn.onclick = () => {
    const text = cardText.value.trim();
    const date = cardDate.value;
    const time = document.getElementById('cardTime').value;
    const description = cardDescription.value.trim();
    const selectedOptions = Array.from(cardTags.selectedOptions).map(opt => opt.value);
    const customTag = customTagInput.value.trim();
    const color = document.getElementById('cardColor').value;
  
    const tags = [...selectedOptions];
    if (selectedOptions.includes('другое') && customTag) {
      tags.push(customTag);
    }
  
    if (!text || !date) {
      alert('Введите текст и дату задачи!');
      return;
    }
  
    if (editCard) {
      editCard.querySelector('.card-text').textContent = text;
      const dateEl = editCard.querySelector('.card-date');
      dateEl.textContent = date;
      dateEl.dataset.time = time;
      editCard.style.backgroundColor = color;
  
      let descEl = editCard.querySelector('.card-description');
      if (!descEl && description) {
        descEl = document.createElement('div');
        descEl.className = 'card-description';
        editCard.insertBefore(descEl, editCard.querySelector('.card-date'));
      }
      if (descEl) descEl.textContent = description;
  
      let tagEl = editCard.querySelector('.card-tags');
      if (!tagEl && tags.length > 0) {
        tagEl = document.createElement('div');
        tagEl.className = 'card-tags';
        editCard.appendChild(tagEl);
      }
      if (tagEl) tagEl.textContent = tags.join(', ');
    } else {
      createCard(text, date, description, tags, null, color, time);
    }
  
    saveState();
    cardModal.classList.add('hidden');
  };
  

  function renderCalendar(selectedTag = '') {
    const events = [];
  
    document.querySelectorAll('.column').forEach(column => {
      const columnTitle = column.querySelector('.column-title').textContent;
      column.querySelectorAll('.card').forEach(card => {
        const text = card.querySelector('.card-text').textContent;
        const dateEl = card.querySelector('.card-date');
        const date = dateEl.textContent;
        const time = dateEl.dataset.time || '09:00';
        const tagsText = card.querySelector('.card-tags')?.textContent || '';
        const cardColor = card.style.backgroundColor || '#eaf6ff';
  
        if (selectedTag && !tagsText.includes(selectedTag)) return;
  
        if (date && !isNaN(Date.parse(date))) {
          const [hours, minutes] = time.split(':');
          const startDate = new Date(date);
          startDate.setHours(parseInt(hours), parseInt(minutes));

          events.push({
            title: `${text} [${columnTitle}]`,
            start: startDate.toISOString(),
            backgroundColor: cardColor,
            borderColor: cardColor,
            textColor: 'black',
            allDay: false
          });
        }
      });
    });
  
    calendarEl.innerHTML = '';
  
    window.currentCalendar = new FullCalendar.Calendar(calendarEl, {
      initialView: 'dayGridMonth',
      locale: 'ru',
      height: 650,
      events,
      editable: true,
      headerToolbar: {
        left: 'prev,next today',
        center: 'title',
        right: 'dayGridMonth,timeGridWeek'
      },
      slotMinTime: '00:00:00',
      slotMaxTime: '24:00:00',
      allDaySlot: false,
      slotDuration: '01:00:00',
      scrollTime: '08:00:00',
      expandRows: true,
      slotEventOverlap: false,
      eventTimeFormat: {
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
      },
      views: {
        timeGridWeek: {
          type: 'timeGrid',
          dayHeaderFormat: { weekday: 'short' },
          slotLabelFormat: {
            hour: '2-digit',
            minute: '2-digit',
            hour12: false
          }
        }
      },
      eventDrop: function(info) {
        const event = info.event;
        const newDate = event.start;
        
        document.querySelectorAll('.card').forEach(card => {
          const text = card.querySelector('.card-text')?.textContent;
          const dateEl = card.querySelector('.card-date');
          
          if (event.title.includes(text)) {
            dateEl.textContent = newDate.toISOString().split('T')[0];
            dateEl.dataset.time = newDate.toTimeString().slice(0, 5);
            saveState();
          }
        });
      },
      eventClick: function(info) {
        const titleText = info.event.title;
        const dateText = info.event.startStr;
  
        let matchedCard = null;
        let columnTitle = '';
        document.querySelectorAll('.column').forEach(column => {
          const colTitle = column.querySelector('.column-title').textContent;
          column.querySelectorAll('.card').forEach(card => {
            const text = card.querySelector('.card-text')?.textContent;
            const date = card.querySelector('.card-date')?.textContent;
            if (titleText.includes(text) && date === dateText.split('T')[0]) {
              matchedCard = card;
              columnTitle = colTitle;
            }
          });
        });
  
        if (matchedCard) {
          showCardPopup(matchedCard, columnTitle);
        }
      }
    });
  
    window.currentCalendar.render();
    setTimeout(() => window.currentCalendar.updateSize(), 50);
  }
  

  tableBtn.onclick = () => {
    mainBoard.classList.add('hidden');
    tableView.classList.remove('hidden');
    renderTable();
  };

  backFromTableBtn.onclick = () => {
    tableView.classList.add('hidden');
    mainBoard.classList.remove('hidden');
  };

  function renderTable() {
    tableBody.innerHTML = '';
    document.querySelectorAll('.column').forEach(column => {
      const columnTitle = column.querySelector('.column-title').textContent;
      column.querySelectorAll('.card').forEach(card => {
        const text = card.querySelector('.card-text').textContent;
        const date = card.querySelector('.card-date').textContent;
        const color = card.style.backgroundColor || '#eaf6ff';
        const row = document.createElement('tr');
        row.style.backgroundColor = color;
        row.innerHTML = `<td>${text}</td><td>${columnTitle}</td><td>${date}</td>`;
        tableBody.appendChild(row);
      });
    });
  }

  // addColumnBtn.onclick = () => {
  //   const title = prompt('Название новой колонки:');
  //   if (title) {
  //     createColumn(title);
  //     saveState();
  //   }
  // };

  createBoardBtn.onclick = () => {
    const name = boardNameInput.value.trim();
    const boards = loadAllBoards();
    const errorEl = document.getElementById('nameError');
  
    // Очистка предыдущих ошибок
    errorEl.classList.add('hidden');
    boardNameInput.classList.remove('error');
  
    if (!name) {
      errorEl.textContent = 'Введите название доски!';
      errorEl.classList.remove('hidden');
      boardNameInput.classList.add('error');
      return;
    }
  
    for (const board of Object.values(boards)) {
      if (board.name.toLowerCase() === name.toLowerCase()) {
        errorEl.textContent = 'Доска с таким названием уже существует!';
        errorEl.classList.remove('hidden');
        boardNameInput.classList.add('error');
        return;
      }
    }
  
    // Успешный сценарий
    currentBoardId = generateId();
    startScreen.classList.add('hidden');
    columnSetup.classList.remove('hidden');
  
    const defaultNames = ["Нужно сделать", "В процессе", "Готово"];
    document.querySelectorAll('.column-input').forEach((input, index) => {
      input.value = defaultNames[index] || '';
    });
  };
  
  function renderBoardList() {
    const boards = loadAllBoards();
    boardList.innerHTML = '';
  
    for (const [id, board] of Object.entries(boards)) {
      const container = document.createElement('div');
      container.className = 'board-item';
  
      const nameSpan = document.createElement('span');
      nameSpan.className = 'board-name';
      nameSpan.textContent = board.name;
  
      nameSpan.onclick = () => {
        currentBoardId = id;
        showMainBoard(board.columns);
      };
  
      const deleteBtn = document.createElement('button');
      deleteBtn.className = 'delete-board-btn';
      deleteBtn.textContent = '✕';
      deleteBtn.onclick = (e) => {
        e.stopPropagation();
        boardIdToDelete = id;
        deleteBoardModal.classList.remove('hidden');
      };
  
      container.appendChild(nameSpan);
      container.appendChild(deleteBtn);
      boardList.appendChild(container);
    }
  }
  
  
  
  confirmDeleteBtn.onclick = () => {
    if (boardIdToDelete) {
      const boards = loadAllBoards();
      delete boards[boardIdToDelete];
      saveAllBoards(boards);
      renderBoardList();
      boardIdToDelete = null;
      deleteBoardModal.classList.add('hidden');
    }
  };
  
  
  cancelDeleteBtn.onclick = () => {
    boardIdToDelete = null;
    deleteBoardModal.classList.add('hidden');
  };
  

  setupColumnsBtn.onclick = () => {
    const boards = loadAllBoards();
    const columns = [];

    document.querySelectorAll('.column-input').forEach(input => {
      const title = input.value.trim();
      if (title) {
        columns.push({ title, cards: [] });
      }
    });

    if (columns.length === 0) {
      alert('Введите хотя бы одну колонку!');
      return;
    }

    const boardName = boardNameInput.value.trim();
    if (!boardName) {
      alert('Введите название доски!');
      return;
    }

    boards[currentBoardId] = {
      name: boardName,
      columns
    };

    saveAllBoards(boards);
    showMainBoard(columns);
  };

  backToStartBtn.onclick = () => {
    mainBoard.classList.add('hidden');
    calendarView.classList.add('hidden');
    tableView.classList.add('hidden');
    columnSetup.classList.add('hidden');
    startScreen.classList.remove('hidden');
    renderBoardList();
  };

  confirmEditColumn.onclick = () => {
    const newName = editColumnName.value.trim();
    if (newName && columnToEdit) {
      columnToEdit.textContent = newName;
      editColumnModal.classList.add('hidden');
      saveState(); // сохранить изменения
    }
  };
  
  cancelEditColumn.onclick = () => {
    editColumnModal.classList.add('hidden');
    editColumnName.value = '';
    columnToEdit = null;
  };
  
  // Показать модалку при нажатии на "Добавить колонку"
  addColumnBtn.onclick = () => {
    newColumnName.value = '';
    addColumnModal.classList.remove('hidden');
  };

  // Подтверждение добавления новой колонки
  confirmAddColumn.onclick = () => {
    const name = newColumnName.value.trim();
    if (name) {
      createColumn(name);
      saveState();
    }
    addColumnModal.classList.add('hidden');
  };

  // Отмена добавления колонки
  cancelAddColumn.onclick = () => {
    addColumnModal.classList.add('hidden');
    newColumnName.value = '';
  };

  calendarBtn.onclick = () => {
    mainBoard.classList.add('hidden');
    calendarView.classList.remove('hidden');
    renderCalendar();
    document.getElementById('monthViewBtn')?.addEventListener('click', () => {
      window.currentCalendar?.changeView('dayGridMonth');
    });
    
    document.getElementById('weekViewBtn')?.addEventListener('click', () => {
      window.currentCalendar?.changeView('timeGridWeek');
    });
    
    document.getElementById('tagFilter')?.addEventListener('change', e => {
      const selectedTag = e.target.value;
      if (selectedTag === 'all') {
        renderCalendar();
      } else {
        renderCalendar(selectedTag);
      }
    });
  };
  
  backToBoardBtn.onclick = () => {
    calendarView.classList.add('hidden');
    mainBoard.classList.remove('hidden');
  };
  
  cardTags.addEventListener('change', () => {
    if (cardTags.value === 'другое') {
      customTagInput.classList.remove('hidden');
    } else {
      customTagInput.classList.add('hidden');
      customTagInput.value = '';
    }
  });
  
  renderBoardList();

  cancelCardBtn.onclick = () => {
    cardModal.classList.add('hidden');
    cardText.value = '';
    cardDate.value = '';
    cardDescription.value = '';
    cardTags.selectedIndex = 0;
    customTagInput.value = '';
    customTagInput.classList.add('hidden');
    editCard = null;
  };

  closePopupBtn.onclick = () => {
    cardViewPopup.classList.add('hidden');
  };

  editCardFromPopupBtn.onclick = () => {
    if (currentViewedCard) {
      cardViewPopup.classList.add('hidden');
      currentViewedCard.click();
    }
  };

  function showCardPopup(card, columnTitle) {
    currentViewedCard = card;
    const title = card.querySelector('.card-text').textContent;
    const description = card.querySelector('.card-description')?.textContent || 'Описание отсутствует';
    const dateEl = card.querySelector('.card-date');
    const date = dateEl.textContent;
    const time = dateEl.dataset.time;
    const tags = card.querySelector('.card-tags')?.textContent || 'Теги отсутствуют';

    document.getElementById('popupCardTitle').textContent = title;
    document.getElementById('popupCardDescription').textContent = description;
    document.getElementById('popupCardDateTime').textContent = `${date} ${time}`;
    document.getElementById('popupCardColumn').textContent = columnTitle;
    document.getElementById('popupCardTags').textContent = tags;

    cardViewPopup.classList.remove('hidden');
  }

  // Обработчик кнопки уведомлений
  if (notificationsBtn) {
    notificationsBtn.onclick = () => {
      const githubUsername = prompt('Введите ваш GitHub логин:');
      if (!githubUsername) return;

      // Открываем Telegram бота в новом окне
      window.open('https://t.me/trello2_notification_bot', '_blank');
      
      // Показываем инструкции
      alert(
        'Для подписки на уведомления:\n\n' +
        '1. Откройте бота в Telegram\n' +
        '2. Отправьте команду /start\n' +
        '3. Введите ваш GitHub логин\n\n' +
        'После этого вы будете получать уведомления за день до дедлайна задачи.'
      );
    };

    // Добавляем кнопку для тестирования уведомлений
    const testNotificationBtn = document.createElement('button');
    testNotificationBtn.textContent = '🔔 Тест уведомлений';
    testNotificationBtn.className = 'sidebar-btn';
    testNotificationBtn.onclick = async () => {
      try {
        const result = await sendTelegramNotification('Тестовое уведомление', new Date().toISOString());
        if (result.status === 'success') {
          alert('Тестовое уведомление отправлено! Проверьте Telegram.');
        } else {
          alert('Ошибка: ' + result.message);
        }
      } catch (error) {
        alert('Ошибка при отправке тестового уведомления: ' + error.message);
      }
    };
    document.querySelector('.sidebar').appendChild(testNotificationBtn);
  }
});

async function sendTelegramNotification(task, deadline) {
  try {
    const response = await fetch(config.API_URL, {
      method: 'POST',
      mode: 'cors',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ task, deadline })
    });
    
    const result = await response.json();
    if (result.error) throw new Error(result.error);
    return result;
  } catch (error) {
    console.error('Ошибка:', error);
    throw error;
  }
}