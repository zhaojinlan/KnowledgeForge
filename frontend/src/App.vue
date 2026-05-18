<!-- src/App.vue -->
<template>
  <Layout />
</template>

<script setup>
import Layout from './components/Layout.vue';
</script>

<style>
/* 全局重置 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html {
  font-size: 16px;
  -webkit-text-size-adjust: 100%;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background-color: var(--bg);
  color: var(--text);
  min-height: 100vh;
  overflow-x: hidden;
}

#app {
  width: 100%;
  margin: 0 auto;
  min-height: 100%;
}

/* 设计令牌 */
:root {
  --primary: #4f6ef7;
  --primary-hover: #3b5de7;
  --primary-light: #eef1ff;
  --primary-gradient: linear-gradient(135deg, #4f6ef7, #6c63ff);
  --sidebar-bg: #1a1f36;
  --sidebar-hover: #252b45;
  --sidebar-active: #2d3456;
  --bg: #f0f2f5;
  --card-bg: #ffffff;
  --text: #1a1a2e;
  --text-secondary: #6b7280;
  --border: #e5e7eb;
  --danger: #ef4444;
  --danger-hover: #dc2626;
  --success: #22c55e;
  --radius: 12px;
  --radius-sm: 8px;
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  --shadow-lg: 0 4px 12px rgba(0, 0, 0, 0.1);
}

/* 路由过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
