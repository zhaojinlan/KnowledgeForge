<!-- src/pages/Home.vue -->
<template>
  <div class="home-layout">
 
 
    <main class="main-content">
      <div class="welcome">
        <h1>欢迎使用 AI 助手</h1>
        <p>点击左侧菜单开始聊天。</p>
        <ul>
          <li>✅ Markdown 渲染</li>
          <li>✅ 代码块高亮 + 复制</li>
          <li>✅ Enter 发送，Shift+Enter 换行</li>
        </ul>
      </div>
    </main>
  </div>
</template>

<style scoped>
.home-layout {
  display: flex;
  height: 100vh;
  font-family: 'Segoe UI', sans-serif;
}

.sidebar {
  width: 240px;
  background: #2c3e50;
  color: white;
  padding: 1.5rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.sidebar h2 {
  margin: 0;
  font-size: 1.4rem;
  text-align: center;
}

.sidebar ul {
  list-style: none;
  padding: 0;
  margin: 0;
  flex: 1;
}

.sidebar a {
  display: block;
  padding: 0.8rem 1rem;
  color: #ecf0f1;
  text-decoration: none;
  border-radius: 8px;
  transition: background 0.3s;
}

.sidebar a:hover,
.sidebar a.router-link-active {
  background: #34495e;
  color: white;
}

.main-content {
  flex: 1;
  padding: 2rem;
  background: #f5f6fa;
  overflow-y: auto;
}

.welcome {
  max-width: 600px;
  margin: 0 auto;
  text-align: center;
}

.welcome h1 {
  color: #2c3e50;
  margin-bottom: 1rem;
}

.welcome p {
  color: #7f8c8d;
  margin-bottom: 1.5rem;
}

.welcome ul {
  text-align: left;
  margin-top: 1rem;
  color: #2c3e50;
}
</style>
