/**
 * EduPulse AI - Full-Featured Enterprise LLM Conversational Assistant.
 * Connects to /api/ai/chat and /api/v1/campus-ai/chat with conversation history,
 * RAG grounding, AbortController cancellation, and Markdown rendering.
 */

// Global State
let activeConversationId = null;
let currentAbortController = null;
let conversationHistoryCache = [];

document.addEventListener('DOMContentLoaded', () => {
  const chatForm = document.getElementById('campusChatForm');
  const chatInput = document.getElementById('campusChatInput');
  const sendBtn = document.getElementById('campusSendBtn');
  const stopBtn = document.getElementById('stopGenerationBtn');
  const clearBtn = document.getElementById('clearChatBtn');
  const newChatBtn = document.getElementById('newChatBtn');
  const charCountEl = document.getElementById('charCount');
  const kbSearchInput = document.getElementById('kbSearchInput');

  // 1. Initialize Active Conversation from first item if present
  const firstConvEl = document.querySelector('.conv-item');
  if (firstConvEl && firstConvEl.dataset.id) {
    selectConversation(parseInt(firstConvEl.dataset.id), false);
  }

  // 2. Character Counter & Textarea Auto-expand
  if (chatInput) {
    chatInput.addEventListener('input', () => {
      // Auto-resize
      chatInput.style.height = 'auto';
      chatInput.style.height = Math.min(chatInput.scrollHeight, 140) + 'px';

      // Char count
      if (charCountEl) {
        charCountEl.innerText = `${chatInput.value.length} / 10000`;
      }
    });

    // Enter to submit (Shift+Enter for newline)
    chatInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (chatForm) {
          chatForm.dispatchEvent(new Event('submit', { cancelable: true }));
        }
      }
    });
  }

  // 3. New Chat Button
  if (newChatBtn) {
    newChatBtn.addEventListener('click', async () => {
      try {
        const res = await fetch('/api/v1/campus-ai/conversations', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title: 'New Chat' })
        });
        const data = await res.json();
        if (data.success && data.conversation) {
          addConversationToSidebar(data.conversation);
          selectConversation(data.conversation.id, true);
        }
      } catch (err) {
        console.error('Failed to create new chat:', err);
        // Fallback: reset local state
        activeConversationId = null;
        resetChatMessagesView();
      }
    });
  }

  // 4. Conversation item click handlers
  document.querySelectorAll('.conv-item').forEach(item => {
    item.addEventListener('click', () => {
      const id = parseInt(item.dataset.id);
      if (id && id !== activeConversationId) {
        selectConversation(id, true);
      }
    });
  });

  // 5. Clear Chat Messages
  if (clearBtn) {
    clearBtn.addEventListener('click', async () => {
      if (!confirm('Are you sure you want to clear all messages in this conversation?')) return;
      if (activeConversationId) {
        try {
          await fetch(`/api/v1/campus-ai/conversations/${activeConversationId}/clear`, {
            method: 'POST'
          });
        } catch (e) {
          console.error('Failed to clear conversation on server:', e);
        }
      }
      resetChatMessagesView();
    });
  }

  // 6. Stop / Cancel Generation Button
  if (stopBtn) {
    stopBtn.addEventListener('click', () => {
      if (currentAbortController) {
        currentAbortController.abort();
        currentAbortController = null;
      }
      setChatLoadingState(false);
      removeTypingIndicator();
      appendSystemNotice('⏹ Generation stopped by user.');
    });
  }

  // 7. Chat Form Submit
  if (chatForm && chatInput) {
    chatForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const rawMessage = chatInput.value;
      const message = rawMessage.trim();

      if (!message) {
        showInputWarning("Please type a question before sending.");
        return;
      }

      // Prepare UI state
      setChatLoadingState(true);
      appendChatMessage(message, 'user');
      chatInput.value = '';
      chatInput.style.height = 'auto';
      if (charCountEl) charCountEl.innerText = '0 / 10000';

      const typingId = appendTypingIndicator();

      // Setup AbortController
      currentAbortController = new AbortController();

      try {
        const response = await fetch('/api/ai/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          },
          signal: currentAbortController.signal,
          body: JSON.stringify({
            message: message,
            conversation_id: activeConversationId,
            history: conversationHistoryCache.slice(-8)
          })
        });

        const data = await response.json();
        removeTypingIndicator(typingId);

        if (response.ok && data.success) {
          const aiReply = data.reply || "No response received.";
          const isFallback = data.is_fallback || false;
          const verifiedContext = data.verified_context_used || false;
          const modelName = data.model || 'Gemini';

          if (data.conversation_id && !activeConversationId) {
            activeConversationId = data.conversation_id;
            updateConversationTitle(activeConversationId, data.conversation_title || message.slice(0, 30));
          }

          // Update cache
          conversationHistoryCache.push({ role: 'user', text: message });
          conversationHistoryCache.push({ role: 'model', text: aiReply });

          appendChatMessage(aiReply, 'assistant', true, modelName, isFallback, verifiedContext);
        } else {
          const errMsg = data.error || `Server returned error (${response.status})`;
          appendErrorMessage(errMsg, message);
        }
      } catch (err) {
        removeTypingIndicator(typingId);
        if (err.name === 'AbortError') {
          // Handled by stop button
          return;
        }
        appendErrorMessage("Unable to connect to the EduPulse AI backend service. Please verify your connection or try again.", message);
      } finally {
        currentAbortController = null;
        setChatLoadingState(false);
        chatInput.focus();
      }
    });
  }

  // 8. Knowledge Base Real-time Search Filter
  if (kbSearchInput) {
    kbSearchInput.addEventListener('input', (e) => {
      const q = e.target.value.toLowerCase().trim();
      document.querySelectorAll('.kb-card-item').forEach(card => {
        const kw = (card.dataset.keywords || '').toLowerCase();
        const text = card.innerText.toLowerCase();
        if (!q || kw.includes(q) || text.includes(q)) {
          card.style.display = 'block';
        } else {
          card.style.display = 'none';
        }
      });
    });
  }
});

/**
 * Selects and loads a conversation
 */
async function selectConversation(convId, fetchHistory = true) {
  activeConversationId = convId;

  // Update UI selection highlights
  document.querySelectorAll('.conv-item').forEach(item => {
    if (parseInt(item.dataset.id) === convId) {
      item.classList.add('active');
      item.style.background = '#eff6ff';
      item.style.borderColor = '#bfdbfe';
      const title = item.querySelector('.conv-title-text');
      if (title) {
        const activeTitleEl = document.getElementById('activeChatTitle');
        if (activeTitleEl) activeTitleEl.innerText = title.innerText;
      }
    } else {
      item.classList.remove('active');
      item.style.background = 'transparent';
      item.style.borderColor = 'transparent';
    }
  });

  if (!fetchHistory) return;

  // Fetch messages from server
  try {
    const res = await fetch(`/api/v1/campus-ai/conversations/${convId}`);
    const data = await res.json();
    if (data.success && data.conversation) {
      resetChatMessagesView();
      conversationHistoryCache = [];
      const msgs = data.conversation.messages || [];
      msgs.forEach(m => {
        conversationHistoryCache.push({ role: m.role, text: m.content });
        appendChatMessage(m.content, m.sender === 'user' ? 'user' : 'assistant', true, m.model_name, m.is_fallback, m.verified_context_used);
      });
    }
  } catch (e) {
    console.error('Failed to load conversation history:', e);
  }
}

/**
 * Fast suggestion launcher
 */
function askQuickQuestion(text) {
  const input = document.getElementById('campusChatInput');
  const form = document.getElementById('campusChatForm');
  if (input && form) {
    input.value = text;
    form.dispatchEvent(new Event('submit'));
  }
}

/**
 * Toggles disabled and loading state on chat controls
 */
function setChatLoadingState(isLoading) {
  const input = document.getElementById('campusChatInput');
  const sendBtn = document.getElementById('campusSendBtn');
  const stopBtn = document.getElementById('stopGenerationBtn');

  if (input) {
    input.disabled = isLoading;
    input.setAttribute('placeholder', isLoading ? 'EduPulse AI is thinking & formulating answer...' : 'Type your question here... (Enter to send, Shift+Enter for new line)');
  }
  if (sendBtn) {
    sendBtn.disabled = isLoading;
    sendBtn.style.display = isLoading ? 'none' : 'inline-flex';
  }
  if (stopBtn) {
    stopBtn.style.display = isLoading ? 'inline-block' : 'none';
  }
}

/**
 * Appends student or AI messages to the visible conversation container
 */
function appendChatMessage(rawContent, sender, formatMd = false, modelName = null, isFallback = false, verifiedUsed = false) {
  const container = document.getElementById('chatMessagesContainer');
  if (!container) return;

  const wrapper = document.createElement('div');
  wrapper.className = `chat-message-wrapper ${sender}`;
  wrapper.style.display = 'flex';
  wrapper.style.flexDirection = 'column';
  wrapper.style.maxWidth = sender === 'user' ? '82%' : '88%';
  wrapper.style.alignSelf = sender === 'user' ? 'flex-end' : 'flex-start';
  wrapper.style.alignItems = sender === 'user' ? 'flex-end' : 'flex-start';

  // Sender Metadata Tag
  const metaRow = document.createElement('div');
  metaRow.style.display = 'flex';
  metaRow.style.alignItems = 'center';
  metaRow.style.gap = '0.35rem';
  metaRow.style.marginBottom = '0.25rem';

  const nameSpan = document.createElement('span');
  nameSpan.style.fontSize = '0.72rem';
  nameSpan.style.fontWeight = '700';
  nameSpan.style.color = sender === 'user' ? '#1e293b' : '#2563eb';
  nameSpan.innerText = sender === 'user' ? 'You' : 'EduPulse AI Mentor';
  metaRow.appendChild(nameSpan);

  if (sender === 'assistant') {
    if (verifiedUsed) {
      const badge = document.createElement('span');
      badge.className = 'badge';
      badge.style.background = '#dcfce7';
      badge.style.color = '#15803d';
      badge.style.fontSize = '0.65rem';
      badge.innerText = '🛡️ Verified Grounding';
      metaRow.appendChild(badge);
    }
    if (isFallback) {
      const fallbackBadge = document.createElement('span');
      fallbackBadge.className = 'badge';
      fallbackBadge.style.background = '#fef3c7';
      fallbackBadge.style.color = '#b45309';
      fallbackBadge.style.fontSize = '0.65rem';
      fallbackBadge.innerText = 'Local Knowledge Core';
      metaRow.appendChild(fallbackBadge);
    }
  }

  // Time Tag
  const timeSpan = document.createElement('span');
  timeSpan.style.fontSize = '0.68rem';
  timeSpan.style.color = '#94a3b8';
  timeSpan.innerText = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  metaRow.appendChild(timeSpan);

  wrapper.appendChild(metaRow);

  // Message Bubble
  const bubble = document.createElement('div');
  bubble.className = `chat-bubble ${sender}`;

  if (sender === 'user') {
    bubble.innerText = rawContent;
  } else {
    bubble.style.background = '#f8fafc';
    bubble.style.border = '1px solid #e2e8f0';
    bubble.style.borderRadius = '12px';
    bubble.style.padding = '0.85rem 1.1rem';
    bubble.style.color = '#1e293b';
    bubble.style.fontSize = '0.88rem';
    bubble.style.lineHeight = '1.55';
    bubble.style.boxShadow = '0 1px 2px rgba(0,0,0,0.03)';
    bubble.innerHTML = formatMarkdown(rawContent);

    // Copy Response & Action Toolbar
    const actionToolbar = document.createElement('div');
    actionToolbar.style.display = 'flex';
    actionToolbar.style.gap = '0.5rem';
    actionToolbar.style.marginTop = '0.65rem';
    actionToolbar.style.paddingTop = '0.45rem';
    actionToolbar.style.borderTop = '1px solid #e2e8f0';

    const copyBtn = document.createElement('button');
    copyBtn.type = 'button';
    copyBtn.style.background = 'none';
    copyBtn.style.border = 'none';
    copyBtn.style.fontSize = '0.72rem';
    copyBtn.style.color = '#64748b';
    copyBtn.style.cursor = 'pointer';
    copyBtn.style.display = 'inline-flex';
    copyBtn.style.alignItems = 'center';
    copyBtn.style.gap = '0.25rem';
    copyBtn.innerHTML = '📋 Copy Response';
    copyBtn.addEventListener('click', () => {
      navigator.clipboard.writeText(rawContent).then(() => {
        copyBtn.innerHTML = '✅ Copied!';
        setTimeout(() => { copyBtn.innerHTML = '📋 Copy Response'; }, 2000);
      });
    });
    actionToolbar.appendChild(copyBtn);
    bubble.appendChild(actionToolbar);
  }

  wrapper.appendChild(bubble);
  container.appendChild(wrapper);
  container.scrollTop = container.scrollHeight;
}

/**
 * Appends user-friendly error message with Retry option
 */
function appendErrorMessage(errorText, originalPrompt = null) {
  const container = document.getElementById('chatMessagesContainer');
  if (!container) return;

  const alertBox = document.createElement('div');
  alertBox.className = 'chat-message-wrapper assistant';
  alertBox.style.alignSelf = 'flex-start';
  alertBox.style.maxWidth = '88%';

  const inner = document.createElement('div');
  inner.style.background = '#fef2f2';
  inner.style.border = '1px solid #fecaca';
  inner.style.borderRadius = '10px';
  inner.style.padding = '0.75rem 1rem';
  inner.style.color = '#991b1b';
  inner.style.fontSize = '0.85rem';

  inner.innerHTML = `<strong>⚠️ Error:</strong> ${escapeHtml(errorText)}`;

  if (originalPrompt) {
    const retryRow = document.createElement('div');
    retryRow.style.marginTop = '0.5rem';
    const retryBtn = document.createElement('button');
    retryBtn.type = 'button';
    retryBtn.className = 'btn btn-secondary btn-sm';
    retryBtn.style.fontSize = '0.75rem';
    retryBtn.style.padding = '0.25rem 0.6rem';
    retryBtn.innerHTML = '🔄 Retry Prompt';
    retryBtn.addEventListener('click', () => {
      alertBox.remove();
      askQuickQuestion(originalPrompt);
    });
    retryRow.appendChild(retryBtn);
    inner.appendChild(retryRow);
  }

  alertBox.appendChild(inner);
  container.appendChild(alertBox);
  container.scrollTop = container.scrollHeight;
}

function appendSystemNotice(noticeText) {
  const container = document.getElementById('chatMessagesContainer');
  if (!container) return;
  const el = document.createElement('div');
  el.style.textAlign = 'center';
  el.style.fontSize = '0.75rem';
  el.style.color = '#94a3b8';
  el.style.margin = '0.5rem 0';
  el.innerText = noticeText;
  container.appendChild(el);
  container.scrollTop = container.scrollHeight;
}

/**
 * Animated Loading Indicator
 */
function appendTypingIndicator() {
  const container = document.getElementById('chatMessagesContainer');
  const id = 'typing-' + Date.now();

  const wrapper = document.createElement('div');
  wrapper.id = id;
  wrapper.className = 'chat-message-wrapper assistant';
  wrapper.style.alignSelf = 'flex-start';

  wrapper.innerHTML = `
    <div style="font-size: 0.72rem; font-weight: 700; color: #2563eb; margin-bottom: 0.25rem;">EduPulse AI Mentor</div>
    <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 0.65rem 1rem; display: inline-flex; align-items: center; gap: 0.5rem;">
      <span style="display:inline-block; width:8px; height:8px; background:#2563eb; border-radius:50%; animation: ping 1s cubic-bezier(0,0,0.2,1) infinite;"></span>
      <span style="color:#64748b; font-size: 0.84rem; font-style:italic;">EduPulse AI is formulating an answer...</span>
    </div>
  `;

  container.appendChild(wrapper);
  container.scrollTop = container.scrollHeight;
  return id;
}

function removeTypingIndicator(id = null) {
  if (id) {
    const el = document.getElementById(id);
    if (el) el.remove();
  } else {
    document.querySelectorAll('[id^="typing-"]').forEach(el => el.remove());
  }
}

function resetChatMessagesView() {
  const container = document.getElementById('chatMessagesContainer');
  if (container) {
    container.innerHTML = `
      <div class="chat-message-wrapper assistant" style="display: flex; flex-direction: column; align-items: flex-start; max-width: 88%;">
        <div style="display: flex; align-items: center; gap: 0.4rem; margin-bottom: 0.25rem;">
          <span style="font-size: 0.72rem; font-weight: 700; color: #2563eb;">EduPulse AI Mentor</span>
          <span class="badge" style="background: #eff6ff; color: #1d4ed8; font-size: 0.65rem;">Official Assistant</span>
        </div>
        <div class="chat-bubble assistant" style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 0.85rem 1.1rem; color: #1e293b; font-size: 0.88rem; line-height: 1.55; box-shadow: 0 1px 2px rgba(0,0,0,0.03);">
          Hello! I am your <strong>EduPulse AI Mentor</strong>. Ask me anything about your academic courses, attendance status, Python & DSA problem-solving, placement readiness, exam policies, or university regulations.
        </div>
      </div>
    `;
  }
}

function showInputWarning(msg) {
  const input = document.getElementById('campusChatInput');
  if (input) {
    input.focus();
    input.parentElement.style.borderColor = '#ef4444';
    setTimeout(() => {
      input.parentElement.style.borderColor = '#cbd5e1';
    }, 2000);
  }
}

function addConversationToSidebar(conv) {
  const list = document.getElementById('conversationsList');
  const notice = document.getElementById('noConversationsNotice');
  if (notice) notice.remove();
  if (!list) return;

  const item = document.createElement('div');
  item.className = 'conv-item active';
  item.dataset.id = conv.id;
  item.style.padding = '0.65rem 0.75rem';
  item.style.borderRadius = '8px';
  item.style.cursor = 'pointer';
  item.style.display = 'flex';
  item.style.justifyContent = 'space-between';
  item.style.alignItems = 'center';
  item.style.background = '#eff6ff';
  item.style.border = '1px solid #bfdbfe';

  item.innerHTML = `
    <div style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 0.82rem; font-weight: 600; color: #1e293b; flex: 1;">
      <span style="margin-right: 0.35rem;">💭</span>
      <span class="conv-title-text">${escapeHtml(conv.title)}</span>
    </div>
    <div class="conv-actions" style="display: flex; gap: 0.2rem;">
      <button type="button" class="btn-icon" onclick="event.stopPropagation(); renameConvPrompt(${conv.id}, '${escapeHtml(conv.title)}')" title="Rename" style="background: none; border: none; font-size: 0.75rem; cursor: pointer; color: #64748b; padding: 2px;">✏️</button>
      <button type="button" class="btn-icon" onclick="event.stopPropagation(); deleteConvConfirm(${conv.id})" title="Delete" style="background: none; border: none; font-size: 0.75rem; cursor: pointer; color: #ef4444; padding: 2px;">🗑️</button>
    </div>
  `;

  item.addEventListener('click', () => {
    selectConversation(conv.id, true);
  });

  list.prepend(item);
}

function updateConversationTitle(convId, newTitle) {
  const item = document.querySelector(`.conv-item[data-id="${convId}"]`);
  if (item) {
    const titleSpan = item.querySelector('.conv-title-text');
    if (titleSpan) titleSpan.innerText = newTitle;
  }
}

function renameConvPrompt(convId, currentTitle) {
  const newTitle = prompt("Enter new title for this conversation:", currentTitle);
  if (newTitle && newTitle.trim()) {
    fetch(`/api/v1/campus-ai/conversations/${convId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: newTitle.trim() })
    }).then(res => res.json()).then(data => {
      if (data.success) {
        updateConversationTitle(convId, newTitle.trim());
      }
    });
  }
}

function deleteConvConfirm(convId) {
  if (confirm("Are you sure you want to delete this conversation?")) {
    fetch(`/api/v1/campus-ai/conversations/${convId}`, {
      method: 'DELETE'
    }).then(res => res.json()).then(data => {
      if (data.success) {
        const item = document.querySelector(`.conv-item[data-id="${convId}"]`);
        if (item) item.remove();
        if (activeConversationId === convId) {
          activeConversationId = null;
          resetChatMessagesView();
        }
      }
    });
  }
}

function escapeHtml(text) {
  if (!text) return '';
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

/**
 * Rich Markdown & Code Formatter
 */
function formatMarkdown(text) {
  if (!text) return '';

  let html = text;

  // Escape raw HTML first
  html = html.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

  // Fenced Code blocks
  html = html.replace(/```([a-zA-Z0-9_-]*)\n([\s\S]*?)```/g, (match, lang, code) => {
    const safeLang = lang || 'CODE';
    return `
      <div style="position: relative; margin: 0.75rem 0; border-radius: 8px; overflow: hidden; border: 1px solid #334155;">
        <div style="background: #1e293b; color: #94a3b8; font-size: 0.72rem; padding: 0.35rem 0.75rem; text-transform: uppercase; font-weight: bold; display: flex; justify-content: space-between; align-items: center;">
          <span>${safeLang}</span>
          <button type="button" onclick="navigator.clipboard.writeText(this.closest('div').nextElementSibling.innerText)" style="background: #334155; border: none; color: #e2e8f0; font-size: 0.7rem; padding: 0.2rem 0.45rem; border-radius: 4px; cursor: pointer;">Copy Code</button>
        </div>
        <pre style="background: #0f172a; color: #38bdf8; padding: 1rem; overflow-x: auto; margin: 0; font-family: 'Fira Code', monospace; font-size: 0.85rem; line-height: 1.5;"><code class="language-${safeLang}">${code}</code></pre>
      </div>
    `;
  });

  // Inline code
  html = html.replace(/`([^`]+)`/g, '<code style="background: #e2e8f0; color: #0f172a; padding: 0.15rem 0.4rem; border-radius: 4px; font-family: monospace; font-size: 0.85em;">$1</code>');

  // Headers
  html = html.replace(/^### (.*$)/gim, '<h4 style="color: #0f172a; font-weight: 700; margin: 0.75rem 0 0.35rem 0; font-size: 0.98rem;">$1</h4>');
  html = html.replace(/^## (.*$)/gim, '<h3 style="color: #0f172a; font-weight: 700; margin: 0.85rem 0 0.4rem 0; font-size: 1.08rem;">$1</h3>');

  // Bold & Italic
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');

  // Blockquotes
  html = html.replace(/^> (.*$)/gim, '<blockquote style="border-left: 3px solid #3b82f6; padding-left: 0.75rem; margin: 0.5rem 0; color: #475569; background: #eff6ff; padding: 0.4rem 0.75rem; border-radius: 0 6px 6px 0;">$1</blockquote>');

  // Unordered Lists
  html = html.replace(/^\s*-\s+(.*$)/gim, '<li style="margin-left: 1.25rem; font-size: 0.88rem; margin-bottom: 0.2rem;">$1</li>');

  // Line breaks
  html = html.replace(/\n\n/g, '<div style="height: 0.5rem;"></div>');
  html = html.replace(/\n/g, '<br>');

  return html;
}
