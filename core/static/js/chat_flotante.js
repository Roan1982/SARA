// Chat flotante básico para SARA
(function() {
    if (window.saraChatLoaded) return;
    window.saraChatLoaded = true;

    // Crear botón flotante
    const chatBtn = document.createElement('button');
    chatBtn.id = 'sara-chat-btn';
    chatBtn.innerHTML = '💬';
    chatBtn.style.position = 'fixed';
    chatBtn.style.bottom = '30px';
    chatBtn.style.right = '30px';
    chatBtn.style.zIndex = 9999;
    chatBtn.style.width = '56px';
    chatBtn.style.height = '56px';
    chatBtn.style.borderRadius = '50%';
    chatBtn.style.background = '#007bff';
    chatBtn.style.color = 'white';
    chatBtn.style.fontSize = '2rem';
    chatBtn.style.border = 'none';
    chatBtn.style.boxShadow = '0 2px 8px rgba(0,0,0,0.2)';
    chatBtn.style.cursor = 'pointer';
    chatBtn.title = 'Abrir chat';
    document.body.appendChild(chatBtn);

    // Crear ventana de chat (oculta por defecto)
    const chatWindow = document.createElement('div');
    chatWindow.id = 'sara-chat-window';
    chatWindow.style.position = 'fixed';
    chatWindow.style.bottom = '100px';
    chatWindow.style.right = '30px';
    chatWindow.style.width = '350px';
    chatWindow.style.height = '500px';
    chatWindow.style.background = 'white';
    chatWindow.style.borderRadius = '12px';
    chatWindow.style.boxShadow = '0 4px 24px rgba(0,0,0,0.18)';
    chatWindow.style.display = 'none';
    chatWindow.style.flexDirection = 'column';
    chatWindow.style.overflow = 'hidden';
    chatWindow.style.zIndex = 10000;
    chatWindow.innerHTML = `
        <div style="background:#007bff;color:white;padding:14px 16px;font-weight:bold;display:flex;align-items:center;justify-content:space-between;">
            <span>Mensajes</span>
            <button id="sara-chat-close" style="background:none;border:none;color:white;font-size:1.5rem;cursor:pointer;">&times;</button>
        </div>
        <div id="sara-chat-users" style="background:#f7f7f7;padding:8px 12px;overflow-x:auto;white-space:nowrap;"></div>
        <div id="sara-chat-messages" style="flex:1;overflow-y:auto;padding:12px;background:#f9f9f9;"></div>
        <form id="sara-chat-form" style="display:flex;padding:10px 8px 8px 8px;background:#f7f7f7;gap:8px;">
            <input id="sara-chat-input" type="text" placeholder="Escribe un mensaje..." style="flex:1;padding:8px 10px;border-radius:6px;border:1px solid #ccc;outline:none;" autocomplete="off" />
            <button type="submit" style="background:#007bff;color:white;border:none;border-radius:6px;padding:0 16px;font-weight:bold;">Enviar</button>
        </form>
    `;
    document.body.appendChild(chatWindow);

    // Mostrar/ocultar chat
    chatBtn.onclick = () => {
        chatWindow.style.display = chatWindow.style.display === 'none' ? 'flex' : 'none';
    };
    chatWindow.querySelector('#sara-chat-close').onclick = () => {
        chatWindow.style.display = 'none';
    };

    // Lógica de usuarios y mensajes (placeholder, se conectará a backend)
    const usersDiv = chatWindow.querySelector('#sara-chat-users');
    const messagesDiv = chatWindow.querySelector('#sara-chat-messages');
    const form = chatWindow.querySelector('#sara-chat-form');
    const input = chatWindow.querySelector('#sara-chat-input');

    // Estado global
    let users = [];
    let selectedUser = null;
    let messages = [];
    let myId = null;
    let ws = null;

    // Cargar usuarios desde backend
    fetch('/api/chat/users/')
        .then(r => r.json())
        .then(data => {
            users = data.users
                .filter(u => u.username !== 'SARA' && u.username !== 'sara' && u.username !== 'Sara') // Oculta usuarios humanos llamados SARA
                .map(u => ({
                    id: u.id,
                    name: u.username === 'sara_bot' ? 'SARA Bot 🤖' : (u.first_name || u.username),
                    username: u.username
                }));
            myId = users.find(u => u.username !== 'sara_bot')?.id;
            // Seleccionar el usuario bot por username y guardar su id globalmente
            const botUser = users.find(u => u.username === 'sara_bot');
            window.saraBotId = botUser ? botUser.id : null;
            selectedUser = botUser ? botUser.id : users[0].id;
            renderUsers();
            loadMessages();
            connectWS();
        });

    function renderUsers() {
        usersDiv.innerHTML = '';
        users.forEach(u => {
            const btn = document.createElement('button');
            btn.textContent = u.name;
            btn.style.marginRight = '8px';
            btn.style.padding = '6px 12px';
            btn.style.borderRadius = '6px';
            btn.style.border = 'none';
            btn.style.background = selectedUser === u.id ? '#007bff' : '#e0e0e0';
            btn.style.color = selectedUser === u.id ? 'white' : '#333';
            btn.style.cursor = 'pointer';
            btn.onclick = () => {
                selectedUser = u.id;
                renderUsers();
                loadMessages();
            };
            usersDiv.appendChild(btn);
        });
    }

    function renderMessages() {
        messagesDiv.innerHTML = '';
        messages.forEach(m => {
            const msgDiv = document.createElement('div');
            // Asegura que los mensajes enviados por el usuario actual siempre estén a la derecha y en azul
            const isMine = String(m.from_id) === String(myId);
            msgDiv.style.marginBottom = '10px';
            msgDiv.style.textAlign = isMine ? 'right' : 'left';
            msgDiv.innerHTML = `<span style="display:inline-block;padding:8px 12px;border-radius:8px;background:${isMine ? '#007bff' : '#e0e0e0'};color:${isMine ? 'white' : '#222'};max-width:80%;word-break:break-word;">${m.text}</span>`;
            messagesDiv.appendChild(msgDiv);
        });
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }

    function loadMessages() {
        if (!selectedUser) return;
        fetch(`/api/chat/messages/?other_id=${selectedUser}`)
            .then(r => r.json())
            .then(data => {
                messages = data.messages;
                renderMessages();
            });
    }

    function connectWS() {
        if (ws) ws.close();
        ws = new WebSocket(`ws://${window.location.host}/ws/chat/`);
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            // Solo mostrar si es para la conversación activa
            if (String(data.sender_id) === String(selectedUser) || String(data.recipient_id) === String(selectedUser)) {
                messages.push({
                    from: users.find(u => u.id == data.sender_id)?.name || 'Desconocido',
                    from_id: data.sender_id,
                    to: users.find(u => u.id == data.recipient_id)?.name || '',
                    to_id: data.recipient_id,
                    text: data.text,
                    timestamp: Date.now(),
                    is_bot: data.is_bot
                });
                renderMessages();
            }
        };
    }

    form.onsubmit = (e) => {
        e.preventDefault();
        const text = input.value.trim();
        if (!text || !selectedUser) return;
        // Mostrar el mensaje propio inmediatamente (opcional, pero recargamos después)
        messages.push({
            from: users.find(u => u.id == myId)?.name || 'Yo',
            from_id: myId,
            to: users.find(u => u.id == selectedUser)?.name || '',
            to_id: selectedUser,
            text: text,
            timestamp: Date.now(),
            is_bot: false
        });
        renderMessages();
        ws.send(JSON.stringify({recipient_id: selectedUser, text}));
        input.value = '';
        // Recargar mensajes del backend tras un pequeño delay para asegurar persistencia
        setTimeout(loadMessages, 400);
    };
})();
