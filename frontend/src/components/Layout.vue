<template>
  <div class="app-layout" :class="{ 'sidebar-collapsed': collapsed }">
    <!-- 左侧导航栏 -->
    <nav class="sidebar" aria-label="主导航">
      <!-- 标题 -->
      <div class="sidebar-header">
        <svg v-show="!collapsed" class="logo-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 2L2 7l10 5 10-5-10-5z"/>
          <path d="M2 17l10 5 10-5"/>
          <path d="M2 12l10 5 10-5"/>
        </svg>
        <h2 v-show="!collapsed">AI 助手</h2>
      </div>

      <!-- 导航菜单 -->
      <ul>
        <li v-for="item in navItems" :key="item.path">
          <router-link
            :to="item.path"
            :aria-label="item.label"
            :title="collapsed ? item.label : null"
          >
            <span class="icon" v-html="item.icon"></span>
            <span v-show="!collapsed" class="link-text">{{ item.text }}</span>
          </router-link>
        </li>
      </ul>

      <!-- 折叠按钮 -->
      <button
        class="collapse-btn"
        @click="toggleSidebar"
        :aria-label="collapsed ? '展开侧边栏' : '收起侧边栏'"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" :class="{ 'is-collapsed': collapsed }">
          <path v-if="!collapsed" d="M11 17l-5-5 5-5"/>
          <path v-if="!collapsed" d="M18 17l-5-5 5-5"/>
          <path v-if="collapsed" d="M13 17l5-5-5-5"/>
          <path v-if="collapsed" d="M6 17l5-5-5-5"/>
        </svg>
      </button>
    </nav>

    <!-- 主内容区 -->
    <main class="main-content">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const collapsed = ref(false)

const toggleSidebar = () => {
  collapsed.value = !collapsed.value
}

const navItems = [
  { path: '/', label: '首页', text: '首页', icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>' },
  { path: '/chat', label: '聊天', text: '聊天', icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>' },
  { path: '/upload', label: '知识库', text: '知识库', icon: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>' },
]
</script>

<style scoped>
.app-layout {
  display: flex;
  height: 100vh;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  overflow: hidden;
}

/* 侧边栏 */
.sidebar {
  width: 240px;
  background: var(--sidebar-bg);
  color: white;
  padding: 1.25rem 0.75rem;
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
  overflow: hidden;
  position: relative;
}

/* 标题区域 */
.sidebar-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem 0.5rem;
  margin-bottom: 0.5rem;
}

.logo-icon {
  width: 28px;
  height: 28px;
  color: var(--primary);
  flex-shrink: 0;
}

.sidebar h2 {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 600;
  white-space: nowrap;
  transition: opacity 0.3s ease;
}

/* 导航列表 */
.sidebar ul {
  list-style: none;
  padding: 0;
  margin: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.sidebar li a {
  display: flex;
  align-items: center;
  padding: 0.75rem 0.75rem;
  color: #b0b8c8;
  text-decoration: none;
  border-radius: var(--radius-sm);
  transition: all 0.2s ease;
  white-space: nowrap;
  position: relative;
}

.sidebar li a:hover {
  background: var(--sidebar-hover);
  color: white;
}

.sidebar li a.router-link-active {
  background: var(--sidebar-active);
  color: white;
  font-weight: 500;
}

/* 激活状态左侧指示条 */
.sidebar li a.router-link-active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 60%;
  background: var(--primary);
  border-radius: 0 2px 2px 0;
}

.sidebar .icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  margin-right: 0.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.sidebar .icon :deep(svg) {
  width: 20px;
  height: 20px;
}

.link-text {
  flex: 1;
}

/* 折叠按钮 */
.collapse-btn {
  position: absolute;
  top: 1rem;
  right: 0.75rem;
  background: transparent;
  color: #8892a8;
  border: none;
  width: 32px;
  height: 32px;
  border-radius: 6px;
  cursor: pointer;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.collapse-btn:hover {
  background: var(--sidebar-hover);
  color: white;
}

.collapse-btn svg {
  width: 18px;
  height: 18px;
}

/* 主内容区 */
.main-content {
  flex: 1;
  background: var(--bg);
  overflow-y: auto;
  min-width: 0;
}

/* 折叠状态 */
.app-layout.sidebar-collapsed .sidebar {
  width: 64px;
  padding: 1.25rem 0.5rem;
}

.app-layout.sidebar-collapsed .sidebar h2 {
  opacity: 0;
  visibility: hidden;
}

.app-layout.sidebar-collapsed .link-text {
  display: none;
}

.app-layout.sidebar-collapsed .icon {
  margin-right: 0;
}

/* 响应式：移动端 */
@media (max-width: 768px) {
  .app-layout {
    flex-direction: column;
  }

  .sidebar {
    width: 100%;
    height: auto;
    flex-direction: row;
    align-items: center;
    padding: 0.5rem 0.75rem;
    gap: 0;
  }

  .sidebar-header {
    margin-bottom: 0;
    padding: 0;
  }

  .logo-icon {
    width: 24px;
    height: 24px;
  }

  .sidebar h2 {
    font-size: 1rem;
    opacity: 1;
    visibility: visible;
  }

  .collapse-btn {
    position: static;
    width: 28px;
    height: 28px;
    margin-left: auto;
    order: 10;
  }

  .sidebar ul {
    flex-direction: row;
    gap: 0.125rem;
    overflow-x: auto;
    padding: 0 0.5rem;
  }

  .sidebar li a {
    padding: 0.5rem 0.75rem;
    font-size: 0.875rem;
  }

  .sidebar li a.router-link-active::before {
    height: 3px;
    width: 60%;
    top: 0;
    left: 50%;
    transform: translateX(-50%);
    border-radius: 0 0 2px 2px;
  }

  .main-content {
    padding: 0;
  }

  .app-layout.sidebar-collapsed .sidebar {
    width: 100%;
    padding: 0.5rem 0.75rem;
  }
}
</style>
