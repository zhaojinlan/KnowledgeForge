<template>
  <div class="app-layout" :class="{ 'sidebar-collapsed': collapsed }">
    <!-- 左侧导航栏 -->
    <nav class="sidebar" aria-label="主导航">
      <!-- 折叠按钮：位于侧边栏右上角 -->
      <button
        class="collapse-btn"
        @click="toggleSidebar"
        aria-label="切换侧边栏"
      >
        <svg
          viewBox="0 0 100 100"
          class="menu-icon"
          :class="{ 'is-collapsed': collapsed }"
        >
          <line x1="20" y1="30" x2="80" y2="30" stroke="white" stroke-width="8" />
          <line x1="20" y1="50" x2="80" y2="50" stroke="white" stroke-width="8" />
          <line x1="20" y1="70" x2="80" y2="70" stroke="white" stroke-width="8" />
        </svg>
      </button>

      <!-- 标题 -->
      <h2 v-show="!collapsed">AI 助手</h2>

      <!-- 导航菜单 -->
      <ul :class="{ 'collapsed': collapsed }">
        <li v-for="item in navItems" :key="item.path">
          <router-link
            :to="item.path"
            :aria-label="item.label"
            :title="collapsed ? item.label : null"
          >
            <span class="icon">{{ item.icon }}</span>
            <span v-show="!collapsed" class="link-text">{{ item.text }}</span>
          </router-link>
        </li>
      </ul>
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

// 侧边栏折叠状态
const collapsed = ref(false)

// 切换折叠状态
const toggleSidebar = () => {
  collapsed.value = !collapsed.value
}

// 导航项配置
const navItems = [
  { path: '/', label: '首页', text: '首页', icon: '🏠' },
  { path: '/chat', label: '聊天', text: '聊天', icon: '💬' },
  { path: '/upload', label: '知识库', text: '知识库', icon: '📄' },
]
</script>

<style scoped>
.app-layout {
  display: flex;
  height: 100vh;
  font-family: 'Segoe UI', sans-serif;
  transition: all 0.3s ease;
  overflow: hidden;
}

/* 侧边栏 */
.sidebar {
  width: 240px;
  background: #2c3e50;
  color: white;
  padding: 1.5rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  transition: width 0.3s ease, padding 0.3s ease;
  overflow: hidden;
  position: relative; /* 必须：让 collapse-btn 能绝对定位 */
}

/* 折叠按钮 */
.collapse-btn {
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: #1a2530;
  color: white;
  border: none;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  cursor: pointer;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  transition: all 0.3s ease;
}

.collapse-btn:hover {
  background: #3a506b;
  transform: scale(1.05);
}

/* 菜单图标旋转动画 */
.menu-icon {
  transition: transform 0.3s ease;
  width: 24px;
  height: 24px;
}

.menu-icon.is-collapsed {
  transform: rotate(90deg);
}

/* 标题 */
.sidebar h2 {
  margin: 0;
  font-size: 1.4rem;
  text-align: center;
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
  gap: 0.5rem;
}

.sidebar ul.collapsed {
  gap: 0.25rem;
}

.sidebar a {
  display: flex;
  align-items: center;
  padding: 0.8rem 1rem;
  color: #ecf0f1;
  text-decoration: none;
  border-radius: 8px;
  transition: background 0.3s, color 0.3s;
  white-space: nowrap;
}

.sidebar a:hover,
.sidebar a.router-link-active {
  background: #34495e;
  color: white;
}

.icon {
  font-size: 1.2rem;
  margin-right: 0.8rem;
}

.link-text {
  flex: 1;
}

/* 主内容区 */
.main-content {
  flex: 1;
  padding: 2rem;
  background: #f5f6fa;
  overflow-y: auto;
  transition: margin-left 0.3s ease;
}

/* 折叠状态样式 */
.app-layout.sidebar-collapsed .sidebar {
  width: 80px;
  padding: 1.5rem 0.5rem;
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
  font-size: 1.4rem;
}

/* 响应式：移动端适配 */
@media (max-width: 768px) {
  .app-layout {
    flex-direction: column;
  }

  .sidebar {
    width: 100%;
    height: auto;
    flex-direction: row;
    padding: 0.8rem 0.5rem;
    gap: 0.5rem;
  }

  .collapse-btn {
    top: 0.7rem;
    right: 0.7rem;
    width: 32px;
    height: 32px;
  }

  .sidebar h2 {
    font-size: 1.1rem;
    opacity: 1;
    visibility: visible;
  }

  .sidebar ul {
    flex-direction: row;
    gap: 0.25rem;
    overflow-x: auto;
    padding-bottom: 4px;
  }

  .sidebar a {
    padding: 0.6rem 0.8rem;
    font-size: 0.9rem;
  }

  .icon {
    margin-right: 0.5rem;
    font-size: 1.1rem;
  }

  .main-content {
    padding: 1rem;
  }

  /* 移动端折叠状态：简化 */
  .app-layout.sidebar-collapsed .sidebar {
    padding: 0.5rem;
  }

  .app-layout.sidebar-collapsed .sidebar h2 {
    opacity: 0;
  }
}
</style>
