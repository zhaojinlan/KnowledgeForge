<!-- src/pages/Chat.vue -->
<template>
  <div class="chat-layout">
    <!-- 左侧会话列表 -->
    <div class="sidebar">
      <div class="sidebar-header">
        <h2>💬 聊天记录</h2>
        <button class="btn-new" @click="createNewSession">+ 新建</button>
      </div>
      <ul class="session-list">
        <li
          v-for="s in sessions"
          :key="s.id"
          :class="{ active: s.id === session_id }"
          @click="loadSession(s.id)"
        >
          {{ s.title }}
          <button
            class="btn-delete"
            @click.stop="deleteSession(s.id)"
            title="删除会话"
          >
            🗑
          </button>
        </li>
      </ul>
    </div>

    <!-- 右侧聊天区 -->
    <div class="main-content">
      <header class="chat-header">
        <span>{{ currentTitle || 'AI 聊天助手' }}</span>
      </header>

      <div ref="chatContainer" class="chat-messages">
        <ChatMessage
          v-for="msg in messages"
          :key="msg.id"
          :content="msg.content"
          :role="msg.role"
        />
        <div v-if="isTyping" class="loading">
          AI 正在思考<span class="loading-dots"></span>
        </div>
      </div>

      <div class="input-fixed-container">
        <div class="input-wrapper">
          <textarea
            ref="textarea"
            v-model="messageInput"
            id="message-input"
            placeholder="输入消息（Shift+Enter 换行，Enter 发送）"
            @input="autoResize"
            @keydown="handleKeydown"
            :rows="1"
          ></textarea>
          <button @click="sendMessage">发送</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue';
import ChatMessage from '../components/ChatMessage.vue';

// ✅ 正确导入 date-fns
import { formatDistanceToNow } from 'date-fns';
import { zhCN } from 'date-fns/locale';

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
    const res = await fetch('http://localhost:8000/api/v1/sessions');
    sessions.value = await res.json();
  } catch (e) {
    console.error('加载会话失败', e);
  }
};

// 创建新会话
const createNewSession = async () => {
  try {
    const res = await fetch('http://localhost:8000/api/v1/sessions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: '新会话' })
    });
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
    const res = await fetch(`http://localhost:8000/api/v1/session/${id}`);
    const data = await res.json();
    console.log('【关键调试】/session/:id 返回数据：', data);

    session_id.value = id;
    currentTitle.value = data.session.title;
    messages.value = data.messages;
    scrollToBottom();
  } catch (e) {
    alert('加载会话失败');
  }
};

// 发送消息
const sendMessage = async () => {
  const message = messageInput.value.trim();
  if (!message) return;

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
    const response = await fetch('http://localhost:8000/api/v1/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        session_id: session_id.value
      })
    });

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
      content: '❌ 连接失败，请检查后端服务是否运行：http://localhost:8000',
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
    await fetch(`http://localhost:8000/api/v1/session/${id}`, {
      method: 'DELETE'
    });

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

// 滚动到底部（增强版）
const scrollToBottom = () => {
  const container = chatContainer.value;
  if (!container) return;
  // 延迟确保 DOM 更新完成
  setTimeout(() => {
    container.scrollTop = container.scrollHeight;
  }, 50);
};

// 格式化时间显示
const formatDate = (ts) => {
  try {
    return formatDistanceToNow(new Date(ts), {
      locale: zhCN,
      addSuffix: true
    });
  } catch {
    return '刚刚';
  }
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
  background: #f5f6fa;
  overflow: hidden; /* 防止 body 滚动 */
}

.sidebar {
  width: 280px;
  background: white;
  border-right: 1px solid #ddd;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  padding: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #eee;
}

.sidebar-header h2 {
  margin: 0;
  font-size: 1.2rem;
  color: #2c3e50;
}

.btn-new {
  padding: 0.4rem 0.8rem;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
}

.session-list {
  list-style: none;
  margin: 0;
  padding: 0;
  overflow-y: auto;
  flex: 1;
  min-height: 0; /* ✅ 修复 flex + overflow 问题 */
}

.session-list li {
  padding: 0.8rem 1rem;
  cursor: pointer;
  border-bottom: 1px solid #eee;
  position: relative;
}

.session-list li:hover {
  background: #f0f4f8;
}

.session-list li.active {
  background: #e3f2fd;
  font-weight: bold;
}

/* 删除按钮 */
.btn-delete {
  opacity: 0;
  position: absolute;
  right: 1rem;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: #e74c3c;
  font-size: 0.9rem;
  cursor: pointer;
  padding: 0;
  width: 20px;
  height: 20px;
  line-height: 20px;
  text-align: center;
}

.session-list li:hover .btn-delete {
  opacity: 1;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden; /* ✅ 控制内部滚动 */
}

.chat-header {
  background: #3498db;
  color: white;
  padding: 1rem;
  text-align: center;
  font-weight: bold;
  flex-shrink: 0;
}

.chat-messages {
  flex: 1;
  padding: 1rem 0 0 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  background: #f9f9fb;
  min-height: 0;
  scroll-behavior: smooth;

  /* 隐藏滚动条 */
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.chat-messages::-webkit-scrollbar {
  display: none;
}


.loading {
  align-self: center;
  color: #7f8c8d;
  font-style: italic;
  padding: 0.5rem 1rem;
  background: #ecf0f1;
  border-radius: 8px;
  font-size: 0.95rem;
}

/* 省略号动画 */
.loading-dots {
  display: inline-block;
  width: 1em;
  text-align: left;
  animation: ellipsis 1.5s infinite step-start;
}

@keyframes ellipsis {
  0%, 33% { content: '.'; }
  34%, 66% { content: '..'; }
  67%, 100% { content: '...'; }
}

.input-fixed-container {
  position: sticky;
  bottom: 0;
  background: white;
  padding: 1rem 0;
  border-top: 1px solid #ddd;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.08);
  z-index: 10;
}

.input-wrapper {
  display: flex;
  gap: 0.5rem;
  align-items: flex-end;
  padding: 0 1rem;
  box-sizing: border-box;
}

#message-input {
  flex: 1;
  padding: 0.8rem;
  border: 1px solid #bdc3c7;
  border-radius: 8px;
  font-size: 1rem;
  resize: none;
  overflow: hidden;
  min-height: 44px;
  max-height: 120px;
  background: white;
  color: #2c3e50;
}

#message-input:focus {
  outline: none;
  border-color: #3498db;
}

button {
  padding: 0.8rem 1.2rem;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

button:hover {
  background: #2980b9;
}

/* 响应式：移动端适配 */
@media (max-width: 768px) {
  .sidebar {
    width: 80px;
  }
  .sidebar-header h2 {
    font-size: 1rem;
  }
  .btn-new {
    padding: 0.3rem 0.5rem;
    font-size: 0.8rem;
  }
  .session-list li {
    padding: 0.6rem 0.8rem;
    font-size: 0.9rem;
  }
  .btn-delete {
    right: 0.8rem;
  }
  .input-wrapper {
    padding: 0 0.5rem;
  }
}
</style>
