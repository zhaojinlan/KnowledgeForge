<!-- src/pages/Chat.vue -->
<template>
  <div class="chat-layout">
    <!-- 左侧会话列表 -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <h2>对话</h2>
        <button class="btn-new" @click="createNewSession" title="新建对话">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
            <line x1="12" y1="5" x2="12" y2="19"/>
            <line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
        </button>
      </div>
      <ul class="session-list">
        <li
          v-for="s in sessions"
          :key="s.id"
          :class="{ active: s.id === session_id }"
          @click="loadSession(s.id)"
        >
          <svg class="chat-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>
          <div class="session-info">
            <span class="session-title">{{ s.title }}</span>
          </div>
          <button
            class="btn-delete"
            @click.stop="deleteSession(s.id)"
            title="删除会话"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
              <polyline points="3 6 5 6 21 6"/>
              <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
            </svg>
          </button>
        </li>
        <li v-if="sessions.length === 0" class="empty-hint">暂无对话记录</li>
      </ul>
    </aside>

    <!-- 右侧聊天区 -->
    <div class="main-content">
      <header class="chat-header">
        <span>{{ currentTitle || 'AI 聊天助手' }}</span>
      </header>

      <div ref="chatContainer" class="chat-messages">
        <div v-if="messages.length === 0 && !isTyping" class="empty-chat">
          <svg viewBox="0 0 48 48" width="48" height="48">
            <circle cx="24" cy="24" r="20" fill="var(--primary-light)" />
            <path d="M16 20l8-6 8 6" stroke="var(--primary)" stroke-width="2.5" fill="none" stroke-linecap="round"/>
            <path d="M16 28l8 6 8-6" stroke="var(--primary)" stroke-width="2.5" fill="none" stroke-linecap="round"/>
          </svg>
          <p>发送一条消息开始对话</p>
        </div>
        <ChatMessage
          v-for="msg in messages"
          :key="msg.id"
          :content="msg.content"
          :role="msg.role"
        />
        <div v-if="isTyping" class="loading">
          <span class="typing-dots">
            <span class="dot"></span>
            <span class="dot"></span>
            <span class="dot"></span>
          </span>
          AI 正在思考
        </div>
      </div>

      <div class="input-fixed-container">
        <div class="input-wrapper">
          <textarea
            ref="textarea"
            v-model="messageInput"
            id="message-input"
            placeholder="输入消息，Enter 发送 / Shift+Enter 换行"
            @input="autoResize"
            @keydown="handleKeydown"
            :rows="1"
          ></textarea>
          <button class="btn-send" @click="sendMessage" :disabled="isTyping" title="发送">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="22" y1="2" x2="11" y2="13"/>
              <polygon points="22 2 15 22 11 13 2 9 22 2"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue';
import ChatMessage from '../components/ChatMessage.vue';

// 会话相关
const sessions = ref([]);
const session_id = ref(null);
const currentTitle = ref('AI 聊天助手');

// 聊天消息
const messages = ref([]);
const messageInput = ref('');
const isTyping = ref(false);
const chatContainer = ref(null);
const textarea = ref(null);

// 获取会话列表
const loadSessions = async () => {
  try {
    const res = await fetch('/api/v1/sessions');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    sessions.value = await res.json();
  } catch (e) {
    console.error('加载会话失败', e);
  }
};

// 创建新会话
const createNewSession = async () => {
  try {
    const res = await fetch('/api/v1/sessions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    session_id.value = data.id;
    currentTitle.value = data.title;
    messages.value = [];
    await loadSessions();
  } catch (e) {
    alert('创建会话失败，请检查后端是否运行');
  }
};

// 加载某个会话的历史
const loadSession = async (id) => {
  try {
    const res = await fetch(`/api/v1/session/${id}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    session_id.value = id;
    currentTitle.value = data.session.title;
    messages.value = data.messages;
    scrollToBottom();
  } catch (e) {
    console.error('加载会话失败', e);
    alert('加载会话失败');
  }
};

// 发送消息
const sendMessage = async () => {
  const message = messageInput.value.trim();
  if (!message || isTyping.value) return;

  // 先显示用户消息
  messages.value.push({
    id: Date.now(),
    content: message,
    role: 'user'
  });
  messageInput.value = '';
  autoResize();
  await nextTick();
  scrollToBottom();

  isTyping.value = true;
  await nextTick();
  scrollToBottom();

  try {
    const response = await fetch('/api/v1/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        session_id: session_id.value
      })
    });

    if (!response.ok) {
      const errText = response.status === 500 ? '服务器内部错误' : `请求失败 (HTTP ${response.status})`;
      throw new Error(errText);
    }

    const data = await response.json();
    isTyping.value = false;

    if (!session_id.value && data.session_id) {
      session_id.value = data.session_id;
      await loadSessions();
    }

    messages.value.push({
      id: Date.now(),
      content: data.response,
      role: 'ai'
    });

    await nextTick();
    scrollToBottom();
  } catch (error) {
    isTyping.value = false;
    messages.value.push({
      id: Date.now(),
      content: `❌ 发送失败：${error.message}`,
      role: 'ai'
    });
  }
};

// 自动调整输入框高度
const autoResize = () => {
  const el = textarea.value;
  if (!el) return;
  el.style.height = 'auto';
  const height = Math.min(el.scrollHeight, 120);
  el.style.height = height + 'px';
  el.style.overflow = height >= 120 ? 'auto' : 'hidden';
};

// 删除会话
const deleteSession = async (id) => {
  if (!confirm('确定要删除这个会话吗？此操作不可恢复！')) return;

  try {
    const res = await fetch(`/api/v1/session/${id}`, {
      method: 'DELETE'
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    sessions.value = sessions.value.filter(s => s.id !== id);

    if (session_id.value === id) {
      session_id.value = null;
      messages.value = [];
      currentTitle.value = 'AI 聊天助手';
    }
  } catch (e) {
    alert('删除失败，请检查网络连接');
  }
};

// 回车发送，Shift+Enter 换行
const handleKeydown = (e) => {
  if (e.key === 'Enter') {
    if (e.shiftKey) {
      e.preventDefault();
      messageInput.value += '\n';
      setTimeout(autoResize, 0);
    } else {
      e.preventDefault();
      sendMessage();
    }
  }
};

// 滚动到底部
const scrollToBottom = () => {
  const container = chatContainer.value;
  if (!container) return;
  setTimeout(() => {
    container.scrollTop = container.scrollHeight;
  }, 50);
};

// 初始化
onMounted(async () => {
  await loadSessions();
  if (sessions.value.length > 0) {
    loadSession(sessions.value[0].id);
  }
});
</script>

<style scoped>
.chat-layout {
  display: flex;
  height: 100vh;
  background: var(--bg);
  overflow: hidden;
}

/* 侧边栏 */
.sidebar {
  width: 280px;
  background: var(--card-bg);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.sidebar-header {
  padding: 1rem 1.25rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--border);
}

.sidebar-header h2 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text);
}

.btn-new {
  width: 32px;
  height: 32px;
  background: var(--primary-gradient);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.btn-new:hover {
  transform: scale(1.05);
  box-shadow: 0 2px 8px rgba(79, 110, 247, 0.35);
}

.btn-new svg {
  width: 16px;
  height: 16px;
}

/* 会话列表 */
.session-list {
  list-style: none;
  margin: 0;
  padding: 0.5rem;
  overflow-y: auto;
  flex: 1;
  min-height: 0;
}

.session-list li {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  padding: 0.7rem 0.75rem;
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: background 0.15s ease;
  position: relative;
}

.session-list li:hover {
  background: var(--bg);
}

.session-list li.active {
  background: var(--primary-light);
}

.chat-icon {
  width: 18px;
  height: 18px;
  color: var(--text-secondary);
  flex-shrink: 0;
}

.session-list li.active .chat-icon {
  color: var(--primary);
}

.session-info {
  flex: 1;
  min-width: 0;
}

.session-title {
  display: block;
  font-size: 0.9rem;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.empty-hint {
  padding: 2rem 1rem;
  text-align: center;
  color: var(--text-secondary);
  font-size: 0.85rem;
}

/* 删除按钮 */
.btn-delete {
  opacity: 0;
  position: absolute;
  right: 0.75rem;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: var(--danger);
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: opacity 0.15s ease, background 0.15s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-delete:hover {
  background: rgba(239, 68, 68, 0.1);
}

.btn-delete svg {
  width: 16px;
  height: 16px;
}

.session-list li:hover .btn-delete {
  opacity: 1;
}

/* 主内容区 */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

.chat-header {
  background: var(--card-bg);
  color: var(--text);
  padding: 0.875rem 1.25rem;
  text-align: center;
  font-weight: 600;
  font-size: 0.95rem;
  flex-shrink: 0;
  border-bottom: 1px solid var(--border);
}

/* 消息区域 */
.chat-messages {
  flex: 1;
  padding: 1rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  background: var(--bg);
  min-height: 0;
  scroll-behavior: smooth;
}

.empty-chat {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  gap: 0.75rem;
  color: var(--text-secondary);
}

.empty-chat p {
  font-size: 0.9rem;
}

/* 加载动画：三个圆点 */
.loading {
  align-self: center;
  color: var(--text-secondary);
  font-style: italic;
  padding: 0.5rem 1rem;
  background: var(--card-bg);
  border-radius: var(--radius-sm);
  font-size: 0.85rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.typing-dots {
  display: inline-flex;
  gap: 3px;
}

.dot {
  width: 6px;
  height: 6px;
  background: var(--primary);
  border-radius: 50%;
  animation: typing 1.4s infinite ease-in-out;
}

.dot:nth-child(1) { animation-delay: 0s; }
.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
  40% { transform: scale(1); opacity: 1; }
}

/* 输入框 */
.input-fixed-container {
  flex-shrink: 0;
  background: var(--card-bg);
  padding: 0.75rem 0;
  border-top: 1px solid var(--border);
}

.input-wrapper {
  display: flex;
  gap: 0.5rem;
  align-items: flex-end;
  padding: 0 1rem;
}

#message-input {
  flex: 1;
  padding: 0.75rem 1rem;
  border: 1.5px solid var(--border);
  border-radius: var(--radius);
  font-size: 0.95rem;
  font-family: inherit;
  resize: none;
  overflow: hidden;
  min-height: 44px;
  max-height: 120px;
  background: var(--bg);
  color: var(--text);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
  line-height: 1.5;
}

#message-input:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px var(--primary-light);
  background: var(--card-bg);
}

.btn-send {
  width: 44px;
  height: 44px;
  background: var(--primary-gradient);
  color: white;
  border: none;
  border-radius: var(--radius);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
  flex-shrink: 0;
}

.btn-send:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: 0 2px 10px rgba(79, 110, 247, 0.35);
}

.btn-send:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-send svg {
  width: 18px;
  height: 18px;
}

/* 响应式 */
@media (max-width: 768px) {
  .sidebar {
    width: 240px;
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    z-index: 50;
    box-shadow: var(--shadow-lg);
    transform: translateX(0);
    transition: transform 0.3s ease;
  }

  .sidebar.hidden-mobile {
    transform: translateX(-100%);
  }
}
</style>
