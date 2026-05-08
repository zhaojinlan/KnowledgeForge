<!-- src/pages/Upload.vue -->
<template>
  <div class="upload-page">
    <header>文件上传助手</header>

    <!-- 文件展示区域 -->
    <div ref="logContainer" class="files-container">
      <!-- 已上传的文件卡片 -->
      <div
        v-for="file in uploadedFiles"
        :key="file.id"
        class="file-card"
        :title="file.filename"
      >
        <span class="filename">{{ truncateName(file.filename) }}</span>
        <small>{{ file.size }}</small>
      </div>

      <!-- 上传入口卡片（始终在最后） -->
      <label v-if="!isUploading" class="file-card upload-card" for="fileInput">
        <span class="plus">+</span>
      </label>

      <!-- 上传中状态 -->
      <div v-if="isUploading" class="file-card uploading">
        <span class="spinner">📤</span>
        <small>上传中...</small>
      </div>
    </div>

    <!-- 隐藏的文件输入 -->
    <input
      id="fileInput"
      ref="fileInput"
      type="file"
      @change="handleFileSelect"
      :disabled="isUploading"
      style="display: none"
    />

    <!-- 底部日志（可选，用于调试） -->
    <footer v-if="false">
      <div v-for="log in uploadLogs" :key="log.id" class="log-item">
        [{{ log.time }}] {{ log.message }}
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';

// 工具函数
const formatSize = (bytes) => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const formatTime = (date) => {
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
};

// 响应式数据
const fileInput = ref(null);
const isUploading = ref(false);
const uploadedFiles = ref([]);
const uploadLogs = ref([]);
const socket = ref(null);

// 添加日志
const addLog = (msg, role) => {
  uploadLogs.value.push({
    id: Date.now() + Math.random(),
    message: msg,
    role,
    time: formatTime(new Date()),
  });
};

// 从服务端获取初始文件列表
const fetchInitialFiles = async () => {
  try {
    const response = await fetch('http://localhost:8000/api/v1/files');
    const files = await response.json();

    uploadedFiles.value = files.map(f => ({
      id: f.filename + '_' + f.uploaded_at,
      filename: f.filename,
      size: formatSize(f.size),
      path: f.path,
    }));

    addLog(`已加载 ${files.length} 个文件`, 'ai');
  } catch (error) {
    addLog(`❌ 获取文件列表失败: ${error.message}`, 'ai');
  }
};

// 建立 WebSocket 连接
const connectWebSocket = () => {
  socket.value = new WebSocket('ws://localhost:8000/api/v1/ws');

  socket.value.onopen = () => {
    console.log('🟢 WebSocket 已连接');
    addLog('WebSocket 连接成功，实时同步已开启', 'ai');
  };

  socket.value.onmessage = (event) => {
    const data = JSON.parse(event.data);

    if (data.type === 'file_uploaded') {
      const f = data.data;
      uploadedFiles.value.unshift({
        id: f.filename + '_' + f.uploaded_at,
        filename: f.filename,
        size: formatSize(f.size),
        path: f.path,
      });
      addLog(`✅ 新文件已上传: ${f.filename}`, 'ai');
    }
  };

  socket.value.onclose = () => {
    console.log('🟡 WebSocket 已断开，正在重连...');
    addLog('WebSocket 断开，尝试重连...', 'ai');
    setTimeout(connectWebSocket, 3000); // 重连
  };

  socket.value.onerror = (error) => {
    console.error('🔴 WebSocket 错误:', error);
    addLog('WebSocket 发生错误', 'ai');
  };
};

// 选择并上传文件
const handleFileSelect = async (e) => {
  const file = e.target.files[0];
  if (!file || isUploading.value) return;

  addLog(`📤 正在上传: ${file.name}`, 'user');
  isUploading.value = true;

  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await fetch('http://localhost:8000/api/v1/upload', {
      method: 'POST',
      body: formData,
    });

    const result = await response.json();

    if (!response.ok) {
      throw new Error(result.detail || '上传失败');
    }

    addLog(`✅ 上传成功: ${result.filename}`, 'ai');
  } catch (error) {
    addLog(`❌ 上传失败: ${error.message}`, 'ai');
  } finally {
    isUploading.value = false;
    fileInput.value.value = '';
  }
};

// 文件名截断
const truncateName = (name) => {
  if (name.length <= 8) return name;
  return name.slice(0, 5) + '...' + name.slice(-3);
};

// 生命周期
onMounted(() => {
  fetchInitialFiles();
  connectWebSocket();
});

onUnmounted(() => {
  if (socket.value) {
    socket.value.close();
  }
});
</script>


<style scoped>/* 页面容器 - 响应式宽度优化 */
.upload-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100%;
  max-width: 100vw; /* 防止溢出 */
  margin: 0 auto;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
  border-radius: 12px;
  overflow: hidden;
  background: white;
}

/* 在桌面端限制最大宽度，在移动端占满屏幕 */
@media (min-width: 100%) {
  .upload-page {
    max-width: 800px;
    margin: 1rem auto;
    border-radius: 16px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  }
}

header {
  background: #3498db;
  color: white;
  padding: 1rem;
  text-align: center;
  font-size: 1.5rem;
  font-weight: bold;
}

/* 文件展示区域：网格布局 - 响应式列数 */
.files-container {
  flex: 1;
  padding: 1rem;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(110px, 1fr));
  gap: 1rem;
  align-content: flex-start;
  background-color: #f9f9fb;
  overflow-y: auto;
}

/* 在小屏幕上稍微缩小卡片间距 */
@media (max-width: 480px) {
  .files-container {
    padding: 0.75rem;
    gap: 0.75rem;
  }

  .file-card {
    aspect-ratio: 1 / 1;
    min-width: 0; /* 防止 grid 溢出 */
  }
}

/* 通用文件卡片样式 */
.file-card {
  aspect-ratio: 1 / 1;
  width: 100%;
  background: white;
  border: 2px dashed #bdc3c7;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.9rem;
  color: #2c3e50;
  text-align: center;
  overflow: hidden;
  min-width: 0; /* 防止内容溢出 grid 单元格 */
}

.file-card:hover {
  border-color: #3498db;
  background-color: #f0f8ff;
}

/* 上传卡片：加号 */
.upload-card .plus {
  font-size: 2rem;
  font-weight: bold;
  color: #7f8c8d;
}

/* 已上传文件的样式 */
.file-card .filename {
  font-weight: 500;
  margin-bottom: 0.2rem;
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding: 0 0.5rem;
}

.file-card small {
  color: #7f8c8d;
}

/* 上传中状态 */
.uploading {
  border-color: #3498db !important;
  background-color: #e8f4fd;
  cursor: wait;
}

.uploading .spinner {
  font-size: 1.5rem;
  animation: bounce 1s infinite;
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-5px); }
}

/* 底部日志（可选） */
footer {
  padding: 0.5rem 1rem;
  background: #eee;
  font-size: 0.8rem;
  color: #555;
  max-height: 100px;
  overflow-y: auto;
}

.log-item {
  margin: 0.2rem 0;
  white-space: pre-wrap;
}

</style>
