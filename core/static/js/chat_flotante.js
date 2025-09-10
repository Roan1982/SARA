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

    // Placeholder: usuarios (el bot y el usuario actual)
    let users = [
        {id: 'bot', name: 'SARA Bot 🤖'},
        {id: 'me', name: 'Tú'}
    ];
    let selectedUser = 'bot';

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
                renderMessages();
            };
            usersDiv.appendChild(btn);
        });
    }

    // Placeholder: mensajes
    let messages = [
        {from: 'bot', to: 'me', text: '¡Hola! Soy SARA Bot. ¿En qué puedo ayudarte?', timestamp: Date.now()}
    ];

    function renderMessages() {
        messagesDiv.innerHTML = '';
        messages.filter(m => (m.from === selectedUser || m.to === selectedUser)).forEach(m => {
            const msgDiv = document.createElement('div');
            msgDiv.style.marginBottom = '10px';
            msgDiv.style.textAlign = m.from === 'me' ? 'right' : 'left';
            msgDiv.innerHTML = `<span style="display:inline-block;padding:8px 12px;border-radius:8px;background:${m.from === 'me' ? '#007bff' : '#e0e0e0'};color:${m.from === 'me' ? 'white' : '#222'};max-width:80%;word-break:break-word;">${m.text}</span>`;
            messagesDiv.appendChild(msgDiv);
        });
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }

    form.onsubmit = (e) => {
        e.preventDefault();
        const text = input.value.trim();
        if (!text) return;
        messages.push({from: 'me', to: selectedUser, text, timestamp: Date.now()});
        input.value = '';
        renderMessages();
        // Si es al bot, simular respuesta (luego se conectará a backend)
        if (selectedUser === 'bot') {
            setTimeout(() => {
                messages.push({from: 'bot', to: 'me', text: 'Procesando tu consulta...', timestamp: Date.now()});
                renderMessages();
                // Aquí se llamará al backend para obtener respuesta real
            }, 800);
        }
    };

    renderUsers();
    renderMessages();
})();
