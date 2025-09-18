<template>
  <div v-if="showLogs" class="terminal-container rounded-lg shadow-2xl border border-slate-800 overflow-hidden mb-8">
    <!-- Terminal Header -->
    <div class="terminal-header flex items-center justify-between px-4 py-3 bg-slate-800 border-b border-slate-700">
      <div class="flex items-center text-slate-300">
        <span class="font-mono text-sm">{{ config.name.toLowerCase() }}-scanner@botu:~$</span>
      </div>
      <button
        @click="refreshLogs"
        class="px-3 py-1 bg-slate-700 hover:bg-slate-600 text-green-400 rounded text-sm font-mono transition-colors duration-200 border border-slate-600"
      >
        ↻ refresh
      </button>
    </div>

    <!-- Terminal Body -->
    <div class="terminal-body bg-black text-green-400 font-mono text-sm leading-relaxed">
      <div ref="terminalContent" class="terminal-content max-h-96 overflow-y-auto p-4 space-y-1">
        <div
          v-for="log in logs"
          :key="`${log.timestamp}-${log.message}`"
          class="terminal-line flex items-start space-x-3"
        >
          <span class="text-slate-500 text-xs w-20 flex-shrink-0">
            {{ formatLogTime(log.timestamp) }}
          </span>
          <span :class="getTerminalLogColor(log.level)" class="w-24 flex-shrink-0 font-bold whitespace-nowrap">
            [{{ (log.level || 'INFO').toUpperCase() }}]
          </span>
          <span :class="getTerminalLogColor(log.level)" class="flex-1 break-words">
            {{ cleanLogMessage(log.message) }}
          </span>
        </div>

        <!-- Next Scan Countdown at the bottom when bot is running -->
        <div v-if="botStatus.isRunning && nextScanCountdown" class="terminal-line flex items-start space-x-3 bg-slate-800 bg-opacity-30 rounded p-2 mt-2 sticky-bottom">
          <span class="text-slate-500 text-xs w-20 flex-shrink-0">
            {{ formatCurrentTime() }}
          </span>
          <span class="text-cyan-400 w-24 flex-shrink-0 font-bold whitespace-nowrap">
            [SCANNER]
          </span>
          <span class="text-cyan-400 flex-1 break-words">
            Próximo escaneo en: {{ nextScanCountdown }}
          </span>
        </div>

        <div v-if="!logs || logs.length === 0" class="terminal-empty text-center py-8">
          <div class="text-slate-600 mb-4">
            <span class="text-2xl">⚡</span>
          </div>
          <div class="text-slate-400 mb-2">$ No logs available</div>
          <div class="text-slate-600 text-xs">Scanner logs will appear here when bot is active...</div>
        </div>
      </div>
    </div>

    <!-- Terminal Footer -->
    <div v-if="logs && logs.length > 0" class="terminal-footer px-4 py-2 bg-slate-900 border-t border-slate-700">
      <div class="flex items-center justify-between text-xs font-mono">
        <span class="text-slate-500">Lines: {{ logs.length }}</span>
        <span class="text-slate-500">Last update: {{ formatUTCTime() }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, watch, onMounted, onUnmounted, ref, nextTick } from 'vue'

const props = defineProps({
  logs: {
    type: Array,
    default: () => []
  },
  config: {
    type: Object,
    required: true
  },
  botStatus: {
    type: Object,
    required: true
  },
  nextScanCountdown: {
    type: String,
    default: null
  },
  formatLogTime: {
    type: Function,
    required: true
  },
  getLogClass: {
    type: Function,
    required: true
  },
  getLogTextClass: {
    type: Function,
    required: true
  },
  getLogIcon: {
    type: Function,
    required: true
  },
  refreshLogs: {
    type: Function,
    required: true
  }
})

// Referencias para auto-scroll
const terminalContent = ref(null)

let autoRefreshInterval = null

// Auto-refresh logs when bot is running
const startAutoRefresh = () => {
  if (autoRefreshInterval) return
  
  autoRefreshInterval = setInterval(() => {
    if (props.botStatus.isRunning) {
      props.refreshLogs()
    }
  }, 5000) // Refresh every 5 seconds
}

const stopAutoRefresh = () => {
  if (autoRefreshInterval) {
    clearInterval(autoRefreshInterval)
    autoRefreshInterval = null
  }
}

// Watch bot status to start/stop auto-refresh
watch(() => props.botStatus.isRunning, (isRunning) => {
  if (isRunning) {
    startAutoRefresh()
  } else {
    stopAutoRefresh()
  }
}, { immediate: true })

onMounted(() => {
  if (props.botStatus.isRunning) {
    startAutoRefresh()
  }
})

// Auto-scroll to bottom function
const scrollToBottom = () => {
  if (terminalContent.value) {
    nextTick(() => {
      terminalContent.value.scrollTop = terminalContent.value.scrollHeight
    })
  }
}

// Watch for changes in logs to auto-scroll
watch(() => props.logs, () => {
  scrollToBottom()
}, { deep: true })

// Scroll to bottom when component mounts
onMounted(() => {
  scrollToBottom()
})

onUnmounted(() => {
  stopAutoRefresh()
})

const showLogs = computed(() => {
  return props.botStatus.isRunning || (props.logs && props.logs.length > 0)
})

// Terminal color scheme for logs
const getTerminalLogColor = (level) => {
  switch (level?.toLowerCase()) {
    case 'error':
      return 'text-red-400'
    case 'warning':
    case 'warn':
      return 'text-yellow-400'
    case 'success':
      return 'text-green-400'
    case 'info':
      return 'text-cyan-400'
    case 'debug':
      return 'text-purple-400'
    default:
      return 'text-slate-300'
  }
}

// Clean log messages to avoid formatting issues
const cleanLogMessage = (message) => {
  if (!message) return ''
  
  // Remove any stray brackets or formatting issues
  let cleaned = message.toString().trim()
  
  // Remove trailing closing brackets that appear on new lines
  cleaned = cleaned.replace(/\n\s*\]/g, ']')
  
  // Replace multiple spaces with single space
  cleaned = cleaned.replace(/\s+/g, ' ')
  
  // Remove any control characters
  cleaned = cleaned.replace(/[\x00-\x1F\x7F]/g, '')
  
  return cleaned
}

// Format current time in UTC
const formatUTCTime = () => {
  const now = new Date()
  const utcTime = now.toUTCString().split(' ')[4] // Gets HH:MM:SS from UTC string
  return `${utcTime} UTC`
}

// Format current time for countdown display
const formatCurrentTime = () => {
  const now = new Date()
  return now.toLocaleTimeString().split(' ')[0] // Gets HH:MM:SS
}
</script>

<style scoped>
/* Terminal styling */
.terminal-container {
  background: linear-gradient(145deg, #1e293b, #0f172a);
  box-shadow: 
    0 25px 50px -12px rgba(0, 0, 0, 0.5),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.terminal-header {
  background: linear-gradient(145deg, #334155, #1e293b);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.terminal-body {
  background: #000000;
  background-image: 
    radial-gradient(circle at 1px 1px, rgba(34, 197, 94, 0.05) 1px, transparent 0);
  background-size: 20px 20px;
}

/* Improved text clarity for logs */
.terminal-line {
  font-size: 13px;
  line-height: 1.5;
  min-height: 20px;
  display: flex;
  align-items: flex-start;
  margin-bottom: 2px;
}

/* Ensure proper spacing and no overlap */
.terminal-line > span {
  display: inline-block;
  vertical-align: top;
}

/* Log level badges */
.terminal-line > span:nth-child(2) {
  min-width: 96px;
  text-align: left;
  margin-right: 8px;
}

/* Better color contrast for log levels */
.text-red-400 {
  color: #ff6b6b !important;
  font-weight: 600;
}

.text-yellow-400 {
  color: #ffd93d !important; 
  font-weight: 600;
}

.text-green-400 {
  color: #51cf66 !important;
  font-weight: 600;
}

.text-cyan-400 {
  color: #22d3ee !important;
  font-weight: 600;
}

.text-purple-400 {
  color: #c084fc !important;
  font-weight: 600;
}

.text-slate-300 {
  color: #cbd5e1 !important;
  font-weight: 500;
}

.text-slate-500 {
  color: #94a3b8 !important;
  font-weight: 400;
}

.terminal-content {
  scrollbar-width: thin;
  scrollbar-color: #22c55e #000000;
}

.terminal-content::-webkit-scrollbar {
  width: 8px;
}

.terminal-content::-webkit-scrollbar-track {
  background: #000000;
}

.terminal-content::-webkit-scrollbar-thumb {
  background: #22c55e;
  border-radius: 4px;
}

.terminal-content::-webkit-scrollbar-thumb:hover {
  background: #16a34a;
}

.terminal-line {
  transition: all 0.2s ease;
  padding: 2px 0;
  border-radius: 2px;
}

.terminal-line:hover {
  background: rgba(34, 197, 94, 0.05);
  transform: translateX(2px);
}


/* Terminal text effects - removed text-shadow for clearer text */
.terminal-body {
  /* text-shadow removed for better clarity */
}


.terminal-body {
  position: relative;
}

/* Font styling for better readability */
.font-mono {
  font-family: 'SF Mono', 'Monaco', 'Consolas', 'Menlo', 'Ubuntu Mono', 'Courier New', monospace;
  font-weight: 500;
  letter-spacing: 0.05em;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
}

/* Terminal footer */
.terminal-footer {
  background: linear-gradient(145deg, #0f172a, #1e293b);
  border-top: 1px solid rgba(34, 197, 94, 0.2);
}
</style>