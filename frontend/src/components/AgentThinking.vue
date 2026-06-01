<!-- src/components/AgentThinking.vue -->
<template>
  <div class="agent-thinking">
    <div class="agent-header" @click="expanded = !expanded">
      <svg class="agent-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
        <path d="M12 6v6l4 2"/>
      </svg>
      <span class="agent-title">{{ title }}</span>
      <span class="agent-badge">{{ eventCount }} steps</span>
      <svg class="chevron" :class="{ rotated: expanded }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polyline points="6 9 12 15 18 9"/>
      </svg>
    </div>
    <div v-if="expanded" class="agent-body">
      <div
        v-for="(event, idx) in events"
        :key="idx"
        :class="['event-item', 'event-' + event.type]"
      >
        <div class="event-header">
          <span class="event-icon">{{ typeIcon(event.type) }}</span>
          <span class="event-label">{{ typeLabel(event.type) }}</span>
        </div>
        <div class="event-content">
          <template v-if="event.type === 'tool_call'">
            <div class="tool-name">{{ event.data.tool_name }}</div>
            <pre class="tool-args">{{ formatArgs(event.data.tool_args) }}</pre>
          </template>
          <template v-else-if="event.type === 'tool_result'">
            <div class="tool-name">Result: {{ event.data.tool_name }}</div>
            <div class="tool-result">{{ truncate(event.data.result, 500) }}</div>
          </template>
          <template v-else-if="event.type === 'thinking'">
            <div class="thinking-text">{{ event.data.message }}</div>
          </template>
          <template v-else-if="event.type === 'error'">
            <div class="error-text">{{ event.data.message }}</div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';

const props = defineProps({
  events: { type: Array, default: () => [] },
});

const expanded = ref(false);

const eventCount = computed(() => props.events.filter(
  e => e.type === 'tool_call' || e.type === 'tool_result'
).length);

const title = computed(() => {
  const toolNames = props.events
    .filter(e => e.type === 'tool_call')
    .map(e => e.data.tool_name);
  if (toolNames.length === 0) return 'Agent thinking...';
  return 'Agent: ' + toolNames.join(', ');
});

function typeIcon(type) {
  return {
    tool_call: '>',
    tool_result: '=',
    thinking: '*',
    error: '!',
    status: '-',
  }[type] || '>';
}

function typeLabel(type) {
  return {
    tool_call: 'Tool call',
    tool_result: 'Tool result',
    thinking: 'Thinking',
    error: 'Error',
    status: 'Status',
  }[type] || type;
}

function formatArgs(args) {
  if (!args || Object.keys(args).length === 0) return '{}';
  return JSON.stringify(args, null, 2);
}

function truncate(text, max) {
  if (!text) return '';
  return text.length > max ? text.slice(0, max) + '...' : text;
}
</script>

<style scoped>
.agent-thinking {
  margin: 0.5rem 0;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--card-bg);
  overflow: hidden;
  font-size: 0.85rem;
}

.agent-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 0.75rem;
  cursor: pointer;
  user-select: none;
  transition: background 0.15s;
}
.agent-header:hover {
  background: var(--bg);
}

.agent-icon {
  width: 16px;
  height: 16px;
  color: var(--primary);
  flex-shrink: 0;
}

.agent-title {
  flex: 1;
  color: var(--text);
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.agent-badge {
  font-size: 0.75rem;
  color: var(--text-secondary);
  background: var(--bg);
  padding: 0.15rem 0.5rem;
  border-radius: 10px;
}

.chevron {
  width: 14px;
  height: 14px;
  color: var(--text-secondary);
  transition: transform 0.2s;
  flex-shrink: 0;
}
.chevron.rotated {
  transform: rotate(180deg);
}

.agent-body {
  border-top: 1px solid var(--border);
  padding: 0.5rem 0.75rem;
  max-height: 320px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.event-item {
  padding: 0.4rem 0.5rem;
  border-radius: 4px;
  background: var(--bg);
}

.event-tool_call { border-left: 3px solid var(--primary); }
.event-tool_result { border-left: 3px solid #22c55e; }
.event-thinking { border-left: 3px solid #f59e0b; }
.event-error { border-left: 3px solid var(--danger); }

.event-header {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  margin-bottom: 0.25rem;
}

.event-icon {
  font-weight: 700;
  font-size: 0.75rem;
  color: var(--primary);
  font-family: monospace;
}

.event-label {
  font-size: 0.75rem;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.event-content {
  padding-left: 1rem;
}

.tool-name {
  font-family: monospace;
  font-weight: 600;
  color: var(--text);
  font-size: 0.82rem;
}

.tool-args {
  margin: 0.25rem 0 0;
  padding: 0.35rem 0.5rem;
  background: var(--card-bg);
  border-radius: 4px;
  font-size: 0.75rem;
  color: var(--text-secondary);
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 100px;
  overflow-y: auto;
}

.tool-result {
  color: var(--text);
  font-size: 0.82rem;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 120px;
  overflow-y: auto;
  line-height: 1.4;
}

.thinking-text {
  color: var(--text-secondary);
  font-style: italic;
  font-size: 0.82rem;
}

.error-text {
  color: var(--danger);
  font-size: 0.82rem;
}
</style>
