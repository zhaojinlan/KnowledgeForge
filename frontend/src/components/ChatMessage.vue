<!-- src/components/ChatMessage.vue -->
<template>
  <div ref="messageRef" :class="['message', role]">
    <div v-if="role === 'ai'" v-html="safeHtmlContent"></div>
    <div v-else>{{ content }}</div>
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

// 渲染 Markdown 并添加复制按钮
watchEffect(() => {
  if (!props.content) {
    safeHtmlContent.value = '';
    return;
  }
  safeHtmlContent.value = renderMarkdown(props.content);

  // 只有 AI 消息才添加复制按钮
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

  // 清理已存在的复制按钮（防止重复）
  const existingButtons = container.querySelectorAll('.copy-code-btn');
  existingButtons.forEach(btn => btn.remove());

  const preBlocks = container.querySelectorAll('pre');
  preBlocks.forEach(pre => {
    const codeEl = pre.querySelector('code');
    if (!codeEl) return;

    // 创建外层容器（用于定位）
    const wrapper = document.createElement('div');
    wrapper.className = 'code-block-wrapper';
    wrapper.style.position = 'relative';
    wrapper.style.margin = '0.5rem 0';
    wrapper.style.borderRadius = '8px';
    wrapper.style.overflow = 'hidden';
    wrapper.style.border = '1px solid #e0e0e0';
    wrapper.style.backgroundColor = '#1e1e1e';

    // 移动 pre 到 wrapper 中
    pre.parentNode.insertBefore(wrapper, pre);
    wrapper.appendChild(pre);

    // 创建复制按钮
    const button = document.createElement('button');
    button.className = 'copy-code-btn';
    button.textContent = '复制';
    button.style.position = 'absolute';
    button.style.top = '8px';
    button.style.right = '8px';
    button.style.zIndex = '10';
    button.style.padding = '4px 8px';
    button.style.fontSize = '12px';
    button.style.color = '#fff';
    button.style.backgroundColor = '#6c757d';
    button.style.border = 'none';
    button.style.borderRadius = '4px';
    button.style.cursor = 'pointer';
    button.style.opacity = '0';
    button.style.transition = 'all 0.3s ease';

    // 悬停代码块时显示按钮
    wrapper.addEventListener('mouseenter', () => {
      button.style.opacity = '1';
    });
    wrapper.addEventListener('mouseleave', () => {
      if (!button.classList.contains('copied')) {
        button.style.opacity = '0';
      }
    });

    // 点击复制
    button.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(codeEl.textContent);
        button.textContent = '已复制';
        button.classList.add('copied');
        button.style.backgroundColor = '#28a745';

        setTimeout(() => {
          button.textContent = '复制';
          button.classList.remove('copied');
          button.style.backgroundColor = '#6c757d';
          button.style.opacity = '0';
        }, 2000);
      } catch (err) {
        console.error('复制失败:', err);
        button.textContent = '失败';
        button.style.backgroundColor = '#dc3545';

        setTimeout(() => {
          button.textContent = '复制';
          button.style.backgroundColor = '#6c757d';
        }, 1500);
      }
    });

    wrapper.appendChild(button);
  });
}
</script>

<style scoped>
.message {
  max-width: 80%;
  padding: 0.8rem;
  border-radius: 12px;
  line-height: 1.5;
  overflow-wrap: break-word;
  font-size: 14px;
  margin-bottom: 0.5rem;
}

.user {
  align-self: flex-end;
  background: #3498db;
  color: white;
  border-bottom-right-radius: 4px;
}

.ai {
  align-self: flex-start;
  background: #f9f9fb;
  color: #2c3e50;
  border-bottom-left-radius: 4px;
}

/* 代码块内字体 */
.message.ai :deep(code) {
  font-family: 'Courier New', monospace;
  color: #dcdcdc;
  font-size: 14px;
  direction: ltr;
}
</style>
