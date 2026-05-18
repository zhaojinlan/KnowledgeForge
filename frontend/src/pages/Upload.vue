<!-- src/pages/Upload.vue -->
<template>
  <div class="upload-page">
    <header class="page-header">
      <h1>知识库</h1>
      <p>上传文档以构建知识库，支持 RAG 混合检索</p>
    </header>

    <!-- 拖拽上传区域 -->
    <div
      class="drop-zone"
      :class="{ 'drag-over': isDragOver, uploading: isUploading }"
      @dragover.prevent="onDragOver"
      @dragleave="onDragLeave"
      @drop.prevent="onDrop"
      @click="triggerFileInput"
    >
      <input
        ref="fileInput"
        type="file"
        @change="handleFileSelect"
        :disabled="isUploading"
        style="display: none"
      />
      <div v-if="isUploading" class="uploading-state">
        <div class="spinner">
          <div class="spinner-ring"></div>
          <div class="spinner-ring"></div>
        </div>
        <span>正在处理文档...</span>
      </div>
      <div v-else class="drop-prompt">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round">
          <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
          <polyline points="17 8 12 3 7 8"/>
          <line x1="12" y1="3" x2="12" y2="15"/>
        </svg>
        <span>点击或拖拽文件到此处上传</span>
      </div>
    </div>

    <!-- 文件展示区域 -->
    <div class="files-section" v-if="uploadedFiles.length > 0">
      <h3>已上传的文件</h3>
      <div class="files-container">
        <div
          v-for="file in uploadedFiles"
          :key="file.id"
          class="file-card"
          :title="file.filename"
        >
          <div class="file-icon" :class="getFileIcon(file.filename).class">
            {{ getFileIcon(file.filename).label }}
          </div>
          <span class="filename" :title="file.filename">{{ truncateName(file.filename) }}</span>
          <small>{{ file.size }}</small>
        </div>
      </div>
    </div>

    <div v-else class="no-files">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
      </svg>
      <p>还没有上传任何文档</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';

const formatSize = (bytes) => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const fileInput = ref(null);
const isUploading = ref(false);
const isDragOver = ref(false);
const uploadedFiles = ref([]);
const socket = ref(null);

// 从服务端获取初始文件列表
const fetchInitialFiles = async () => {
  try {
    const response = await fetch('/api/v1/files');
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const files = await response.json();

    uploadedFiles.value = files.map(f => ({
      id: f.filename + '_' + f.uploaded_at,
      filename: f.filename,
      size: formatSize(f.size),
      path: f.path,
    }));
  } catch (error) {
    console.error('获取文件列表失败:', error);
  }
};

// 拖拽事件
const onDragOver = () => {
  isDragOver.value = true;
};

const onDragLeave = () => {
  isDragOver.value = false;
};

const onDrop = (e) => {
  isDragOver.value = false;
  const file = e.dataTransfer.files[0];
  if (file) {
    uploadFile(file);
  }
};

// 触发文件选择
const triggerFileInput = () => {
  if (!isUploading.value && fileInput.value) {
    fileInput.value.click();
  }
};

// 选择并上传文件
const handleFileSelect = async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  uploadFile(file);
};

// 执行上传
const uploadFile = async (file) => {
  if (isUploading.value) return;

  isUploading.value = true;

  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await fetch('/api/v1/upload', {
      method: 'POST',
      body: formData,
    });

    const result = await response.json();

    if (!response.ok) {
      throw new Error(result.detail || '上传失败');
    }
  } catch (error) {
    console.error('上传失败:', error.message);
  } finally {
    isUploading.value = false;
    if (fileInput.value) fileInput.value.value = '';
  }
};

// 获取文件类型图标
const getFileIcon = (filename) => {
  const ext = filename.split('.').pop().toLowerCase();
  const iconMap = {
    pdf:  { label: 'PDF', class: 'icon-pdf' },
    doc:  { label: 'DOC', class: 'icon-doc' },
    docx: { label: 'DOC', class: 'icon-doc' },
    md:   { label: 'MD',  class: 'icon-md' },
    txt:  { label: 'TXT', class: 'icon-txt' },
    csv:  { label: 'CSV', class: 'icon-csv' },
    json: { label: '{}',  class: 'icon-json' },
    xml:  { label: '<>',  class: 'icon-xml' },
  };
  return iconMap[ext] || { label: 'FILE', class: 'icon-file' };
};

// 文件名截断
const truncateName = (name) => {
  if (name.length <= 14) return name;
  return name.slice(0, 10) + '...' + name.slice(-3);
};

// WebSocket 实时同步
const connectWebSocket = () => {
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${wsProtocol}//${window.location.host}/api/v1/ws`;
  socket.value = new WebSocket(wsUrl);

  socket.value.onopen = () => {
    console.log('WebSocket 已连接');
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
    }
  };

  socket.value.onclose = () => {
    console.log('WebSocket 断开，正在重连...');
    setTimeout(connectWebSocket, 3000);
  };
};

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

<style scoped>
.upload-page {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  padding: 2rem;
  max-width: 960px;
  margin: 0 auto;
}

/* 页头 */
.page-header {
  margin-bottom: 2rem;
}

.page-header h1 {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--text);
  margin-bottom: 0.25rem;
}

.page-header p {
  color: var(--text-secondary);
  font-size: 0.95rem;
}

/* 拖拽上传区域 */
.drop-zone {
  border: 2px dashed var(--border);
  border-radius: var(--radius);
  padding: 3rem 2rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
  background: var(--card-bg);
  margin-bottom: 2rem;
}

.drop-zone:hover {
  border-color: var(--primary);
  background: var(--primary-light);
}

.drop-zone.drag-over {
  border-color: var(--primary);
  background: var(--primary-light);
  transform: scale(1.01);
}

.drop-zone.uploading {
  cursor: wait;
  pointer-events: none;
}

.drop-prompt {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  color: var(--text-secondary);
}

.drop-prompt svg {
  width: 40px;
  height: 40px;
  color: var(--primary);
}

.drop-prompt span {
  font-size: 1rem;
}

/* 上传中状态 */
.uploading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  color: var(--primary);
}

.spinner {
  position: relative;
  width: 48px;
  height: 48px;
}

.spinner-ring {
  position: absolute;
  width: 100%;
  height: 100%;
  border: 3px solid transparent;
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.spinner-ring:nth-child(2) {
  width: 70%;
  height: 70%;
  top: 15%;
  left: 15%;
  border-top-color: var(--primary-light);
  animation-direction: reverse;
  animation-duration: 0.75s;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 文件展示区域 */
.files-section {
  flex: 1;
}

.files-section h3 {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 1rem;
}

.files-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 1rem;
}

.file-card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
  min-width: 0;
}

.file-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
  border-color: var(--primary);
}

.file-icon {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.7rem;
  letter-spacing: 0.5px;
  flex-shrink: 0;
}

.file-icon.icon-pdf  { background: #fef2f2; color: #ef4444; }
.file-icon.icon-doc   { background: #eff6ff; color: #3b82f6; }
.file-icon.icon-md    { background: #f0fdf4; color: #22c55e; }
.file-icon.icon-txt   { background: #f5f3ff; color: #8b5cf6; }
.file-icon.icon-csv   { background: #fff7ed; color: #f97316; }
.file-icon.icon-json  { background: #fefce8; color: #ca8a04; }
.file-icon.icon-xml   { background: #fdf2f8; color: #ec4899; }
.file-icon.icon-file  { background: #f3f4f6; color: #6b7280; }

.filename {
  font-size: 0.85rem;
  color: var(--text);
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  width: 100%;
}

.file-card small {
  color: var(--text-secondary);
  font-size: 0.75rem;
}

/* 空状态 */
.no-files {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  color: var(--text-secondary);
  padding: 3rem 0;
}

.no-files svg {
  width: 48px;
  height: 48px;
  opacity: 0.4;
}

/* 响应式 */
@media (max-width: 640px) {
  .upload-page {
    padding: 1rem;
  }
  .files-container {
    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
    gap: 0.75rem;
  }
  .drop-zone {
    padding: 2rem 1rem;
  }
}
</style>
