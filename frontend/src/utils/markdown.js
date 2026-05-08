// src/utils/markdown.js
import { marked } from 'marked';
import hljs from 'highlight.js';
import 'highlight.js/styles/github.css'; // 主题样式

// 设置 marked
marked.setOptions({
  highlight: function (code, lang) {
    if (!lang) return code; // 如果没有语言，不处理
    try {
      if (hljs.getLanguage(lang)) {
        return hljs.highlight(code, { language: lang }).value;
      } else {
        return hljs.highlightAuto(code).value;
      }
    } catch (err) {
      console.error('代码高亮失败:', err);
      return code; // 失败时返回原始代码
    }
  },
  langPrefix: 'language-', // CSS 类前缀
  mangle: false, // 禁用 email 混淆（一般不需要）
  headerIds: false // 禁用标题 ID（可选）
});

// ✅ 移除了 sanitize: true
export function renderMarkdown(text) {
  if (!text) return '';
  const html = marked(text);
  return html;
}
