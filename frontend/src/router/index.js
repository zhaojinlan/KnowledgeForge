// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', redirect: '/home' },
    { path: '/home', component: () => import('../pages/Home.vue') },
    { path: '/chat', component: () => import('../pages/Chat.vue') },
    {path: '/upload',component: () => import('../pages/Upload.vue')}
  ]
})

export default router
