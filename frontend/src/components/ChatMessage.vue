<!-- src/components/ChatMessage.vue -->
<template>
  <div ref="messageRef" :class="['message', role]">
    <div class="message-avatar">
      <svg v-if="role === 'ai'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M12 2L2 7l10 5 10-5-10-5z"/>
        <path d="M2 17l10 5 10-5"/>
        <path d="M2 12l10 5 10-5"/>
      </svg>
      <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/>
        <circle cx="12" cy="7" r="4"/>
      </svg>
    </div>
    <div class="message-content">
      <div v-if="role === 'ai'" v-html="safeHtmlContent" class="message-text"></div>
      <div v-else class="message-text">{{ content }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, watchEffect, nextTick } from 'vue';
import { renderMarkdown } from '../utils/markdown';

const props = defineProps({
  content: {
    type: String,
    default: ''
  },
  role: {
    type: String,
    validator: value => ['user', 'ai'].includes(value),
    default: 'user'
  }
});

const messageRef = ref(null);
const safeHtmlContent = ref('');

watchEffect(() => {
  if (!props.content) {
    safeHtmlContent.value = '';
    return;
  }
  safeHtmlContent.value = renderMarkdown(props.content);

  if (props.role === 'ai') {
    nextTick(() => {
      if (messageRef.value) {
        addCopyButtons(messageRef.value);
      }
    });
  }
});

function addCopyButtons(container) {
  if (!container) return;

  const existingButtons = container.querySelectorAll('.copy-code-btn');
  existingButtons.forEach(btn => btn.remove());

  const preBlocks = container.querySelectorAll('pre');
  preBlocks.forEach(pre => {
    const codeEl = pre.querySelector('code');
    if (!codeEl) return;

    // 检测语言
    let lang = '';
    codeEl.className.split(' ').forEach(cls => {
      if (cls.startsWith('language-')) lang = cls.replace('language-', '');
    });

    const wrapper = document.createElement('div');
    wrapper.className = 'code-block-wrapper';
    wrapper.style.position = 'relative';
    wrapper.style.margin = '0.5rem 0';
    wrapper.style.borderRadius = '8px';
    wrapper.style.overflow = 'hidden';
    wrapper.style.border = '1px solid #3a3a3a';

    pre.parentNode.insertBefore(wrapper, pre);
    wrapper.appendChild(pre);

    // 语言标签
    if (lang) {
      const langLabel = document.createElement('span');
      langLabel.className = 'code-lang-label';
      langLabel.textContent = lang.toUpperCase();
      langLabel.style.position = 'absolute';
      langLabel.style.top = '6px';
      langLabel.style.left = '12px';
      langLabel.style.fontSize = '10px';
      langLabel.style.color = '#888';
      langLabel.style.zIndex = '1';
      langLabel.style.fontWeight = '600';
      langLabel.style.letterSpacing = '0.5px';
      langLabel.style.pointerEvents = 'none';
      wrapper.appendChild(langLabel);
    }

    const button = document.createElement('button');
    button.className = 'copy-code-btn';
    button.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>';
    button.style.position = 'absolute';
    button.style.top = '6px';
    button.style.right = '8px';
    button.style.zIndex = '10';
    button.style.padding = '4px 6px';
    button.style.color = '#888';
    button.style.backgroundColor = 'transparent';
    button.style.border = 'none';
    button.style.borderRadius = '4px';
    button.style.cursor = 'pointer';
    button.style.opacity = '0';
    button.style.transition = 'all 0.2s ease';
    button.style.display = 'flex';
    button.style.alignItems = 'center';

    wrapper.addEventListener('mouseenter', () => {
      button.style.opacity = '1';
    });
    wrapper.addEventListener('mouseleave', () => {
      if (!button.classList.contains('copied')) {
        button.style.opacity = '0';
      }
    });

    button.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(codeEl.textContent);
        button.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2" width="14" height="14"><polyline points="20 6 9 17 4 12"/></svg>';
        button.classList.add('copied');
        setTimeout(() => {
          button.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>';
          button.classList.remove('copied');
          button.style.opacity = '0';
        }, 2000);
      } catch (err) {
        console.error('复制失败:', err);
      }
    });

    wrapper.appendChild(button);
  });
}
</script>

<style scoped>
.message {
  display: flex;
  gap: 0.75rem;
  max-width: 85%;
  padding: 0;
}

.message.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message.ai {
  align-self: flex-start;
}

/* 头像 */
.message-avatar {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 2px;
}

.message.ai .message-avatar {
  background: var(--primary-light);
  color: var(--primary);
}

.message.ai .message-avatar svg {
  width: 18px;
  height: 18px;
}

.message.user .message-avatar {
  background: #e5e7eb;
  color: #6b7280;
}

.message.user .message-avatar svg {
  width: 18px;
  height: 18px;
}

/* 消息内容 */
.message-content {
  min-width: 0;
}

.message-text {
  padding: 0.75rem 1rem;
  border-radius: var(--radius);
  line-height: 1.65;
  font-size: 0.95rem;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.message.user .message-text {
  background: var(--primary-gradient);
  color: white;
  border-bottom-right-radius: 4px;
}

.message.ai .message-text {
  background: var(--card-bg);
  color: var(--text);
  border-bottom-left-radius: 4px;
  box-shadow: var(--shadow);
}

/* AI 消息内的 Markdown 样式 */
.message.ai .message-text :deep(p) {
  margin: 0.5rem 0;
}

.message.ai .message-text :deep(p:first-child) {
  margin-top: 0;
}

.message.ai .message-text :deep(p:last-child) {
  margin-bottom: 0;
}

.message.ai .message-text :deep(ul),
.message.ai .message-text :deep(ol) {
  margin: 0.5rem 0;
  padding-left: 1.5rem;
}

.message.ai .message-text :deep(li) {
  margin: 0.25rem 0;
}

.message.ai .message-text :deep(h1),
.message.ai .message-text :deep(h2),
.message.ai .message-text :deep(h3),
.message.ai .message-text :deep(h4) {
  margin: 1rem 0 0.5rem;
  font-weight: 600;
  line-height: 1.3;
}

.message.ai .message-text :deep(h1) { font-size: 1.3rem; }
.message.ai .message-text :deep(h2) { font-size: 1.15rem; }
.message.ai .message-text :deep(h3) { font-size: 1.05rem; }

.message.ai .message-text :deep(blockquote) {
  margin: 0.5rem 0;
  padding: 0.5rem 1rem;
  border-left: 3px solid var(--primary);
  background: var(--primary-light);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  color: var(--text-secondary);
}

.message.ai .message-text :deep(table) {
  border-collapse: collapse;
  margin: 0.5rem 0;
  width: 100%;
}

.message.ai .message-text :deep(th),
.message.ai .message-text :deep(td) {
  border: 1px solid var(--border);
  padding: 0.4rem 0.6rem;
  text-align: left;
}

.message.ai .message-text :deep(th) {
  background: var(--bg);
  font-weight: 600;
}

.message.ai .message-text :deep(hr) {
  border: none;
  border-top: 1px solid var(--border);
  margin: 1rem 0;
}

/* 行内代码 */
.message.ai .message-text :deep(:not(pre) > code) {
  background: #f0f0f0;
  padding: 0.15rem 0.4rem;
  border-radius: 4px;
  font-family: 'SF Mono', 'Fira Code', 'Courier New', monospace;
  font-size: 0.85em;
  color: #e83e8c;
}

/* 代码块 */
.message.ai .message-text :deep(pre) {
  background: #1e1e1e;
  padding: 1rem;
  border-radius: 8px;
  overflow-x: auto;
  margin: 0.5rem 0;
}

.message.ai .message-text :deep(pre code) {
  font-family: 'SF Mono', 'Fira Code', 'Courier New', monospace;
  color: #dcdcdc;
  font-size: 0.875rem;
  line-height: 1.5;
  direction: ltr;
}

/* 链接 */
.message.ai .message-text :deep(a) {
  color: var(--primary);
  text-decoration: none;
}

.message.ai .message-text :deep(a:hover) {
  text-decoration: underline;
}
</style>
