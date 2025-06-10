// script.js for the main chat interface (index.html)
class ChatInterface {
    constructor() {
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.chatMessages = document.getElementById('chatMessages');
        this.typingIndicator = document.getElementById('typingIndicator');

        this.init();
    }

    init() {
        this.sendButton.addEventListener('click', () => this.sendMessage());
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });
        this.checkSystemStatus();
    }

    async checkSystemStatus() {
        try {
            const response = await fetch('/api/stats');
            if (response.ok) {
                const stats = await response.json();
                if (stats.total_chunks > 0) {
                    this.enableChat();
                } else {
                    this.disableChat('Aucun document n\'est traité. Uploadez des fichiers pour commencer.');
                }
            } else {
                this.disableChat('Erreur de connexion avec le serveur.');
            }
        } catch (error) {
            this.disableChat('Impossible de joindre le backend.');
        }
    }

    enableChat() {
        this.messageInput.disabled = false;
        this.sendButton.disabled = false;
        this.messageInput.placeholder = 'Posez votre question...';
    }

    disableChat(message) {
        this.messageInput.disabled = true;
        this.sendButton.disabled = true;
        this.messageInput.placeholder = message;
    }

    async sendMessage() {
        const messageText = this.messageInput.value.trim();
        if (messageText === '') return;

        this.addMessage(messageText, 'user');
        this.messageInput.value = '';
        this.showTypingIndicator();

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: messageText })
            });

            if (!response.ok) {
                throw new Error('La réponse du serveur n\'était pas OK');
            }
            
            const data = await response.json();
            this.addMessage(data.response, 'bot', data.sources);

        } catch (error) {
            console.error('Erreur lors de l\'envoi du message:', error);
            this.addMessage('Désolé, une erreur est survenue. Veuillez réessayer.', 'bot');
        } finally {
            this.hideTypingIndicator();
        }
    }

    addMessage(text, sender, sources = []) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message', `${sender}-message`);

        let sourcesHTML = '';
        if (sources && sources.length > 0) {
            sourcesHTML = `<div class="sources"><strong>Sources:</strong> ${sources.join(', ')}</div>`;
        }

        const icon = sender === 'bot' ? 'fa-robot' : 'fa-user';
        const author = sender === 'bot' ? 'Assistant' : 'Vous';
        
        messageElement.innerHTML = `
            <div class="message-content">
                <strong><i class="fas ${icon}"></i> ${author}:</strong>
                <p>${this.formatText(text)}</p>
                ${sourcesHTML}
            </div>
        `;

        this.chatMessages.appendChild(messageElement);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    formatText(text) {
        // Convertit les sauts de ligne en balises <br>
        return text.replace(/\n/g, '<br>');
    }

    showTypingIndicator() {
        this.typingIndicator.style.display = 'block';
        this.disableChat('L\'assistant réfléchit...');
    }

    hideTypingIndicator() {
        this.typingIndicator.style.display = 'none';
        this.enableChat();
    }
}

document.addEventListener('DOMContentLoaded', () => new ChatInterface());