<!-- src/pages/Home.vue -->
<template>
  <div class="home-page">
    <div class="welcome">
      <div class="logo">
        <svg viewBox="0 0 80 80" width="80" height="80">
          <defs>
            <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" style="stop-color:#4f6ef7;stop-opacity:1" />
              <stop offset="100%" style="stop-color:#6c63ff;stop-opacity:1" />
            </linearGradient>
          </defs>
          <circle cx="40" cy="40" r="36" fill="url(#grad)" />
          <path d="M25 35l15-12 15 12" stroke="white" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M25 45l15 12 15-12" stroke="white" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </div>
      <h1>欢迎使用 AI 助手</h1>
      <p>基于 RAG 知识库的智能对话系统，支持文档检索与上下文增强</p>
      <div class="features">
        <div class="feature-card">
          <div class="feature-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>
          </div>
          <h3>智能对话</h3>
          <p>多轮会话，支持上下文记忆</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
          </div>
          <h3>文档上传</h3>
          <p>上传文档自动构建知识库</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          </div>
          <h3>混合检索</h3>
          <p>向量 + 全文混合检索，精准召回</p>
        </div>
      </div>
      <router-link to="/chat" class="start-btn">开始对话</router-link>
    </div>
  </div>
</template>

<style scoped>
.home-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 2rem;
  background: var(--bg);
}

.welcome {
  max-width: 640px;
  text-align: center;
}

.logo {
  margin-bottom: 1.5rem;
}

h1 {
  font-size: 2rem;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 0.75rem;
}

.welcome > p {
  color: var(--text-secondary);
  font-size: 1.05rem;
  margin-bottom: 2.5rem;
  line-height: 1.6;
}

.features {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.25rem;
  margin-bottom: 2.5rem;
}

.feature-card {
  background: var(--card-bg);
  border-radius: var(--radius);
  padding: 1.5rem 1rem;
  box-shadow: var(--shadow);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.feature-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.feature-icon {
  width: 40px;
  height: 40px;
  background: var(--primary-light);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 0.75rem;
  color: var(--primary);
}

.feature-icon svg {
  width: 20px;
  height: 20px;
}

.feature-card h3 {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 0.25rem;
}

.feature-card p {
  font-size: 0.8rem;
  color: var(--text-secondary);
  line-height: 1.4;
}

.start-btn {
  display: inline-block;
  padding: 0.85rem 2.5rem;
  background: var(--primary-gradient);
  color: white;
  font-size: 1rem;
  font-weight: 600;
  border-radius: 50px;
  text-decoration: none;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  box-shadow: 0 4px 14px rgba(79, 110, 247, 0.35);
}

.start-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(79, 110, 247, 0.45);
}

@media (max-width: 640px) {
  .home-page {
    padding: 1.5rem;
  }
  .features {
    grid-template-columns: 1fr;
    gap: 0.75rem;
  }
  h1 {
    font-size: 1.5rem;
  }
}
</style>
