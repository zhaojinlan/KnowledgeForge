<!-- src/App.vue -->
<template>
  <Layout />
</template>

<script setup>
import Layout from './components/Layout.vue';
</script>

<style>
/* 全局重置与布局控制 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html {
  font-size: 16px;
  /* 禁用字体大小自动缩放（尤其在 iOS Safari 中） */
  -webkit-text-size-adjust: 100%;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background-color: #f5f7fa;
  color: #333;
  min-height: 100vh;
  /* 防止内容溢出屏幕 */
  overflow-x: hidden;
}

/* 全局容器最大宽度限制 */
#app {
  width: 100%;
  margin: 0 auto;
  min-height: 100%;
}

</style>
