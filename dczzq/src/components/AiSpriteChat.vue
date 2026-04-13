<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

type ChatRole = 'user' | 'assistant'

interface ChatMessage {
  id: number
  role: ChatRole
  text: string
  time: string
}

const route = useRoute()
const panelOpen = ref(false)
const inputText = ref('')
const typing = ref(false)
const scrollRef = ref<HTMLElement | null>(null)
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim() || 'http://127.0.0.1:8000'
const TOKEN_KEY = 'mind_island_token'

let streamAbort: AbortController | null = null

const visibleRouteNames = new Set(['home', 'analysis', 'encyclopedia', 'mentor', 'relax', 'tree-hole', 'tree-wall', 'profile'])
const isVisible = computed(() => visibleRouteNames.has(String(route.name || '')))

const messages = ref<ChatMessage[]>([
  {
    id: 1,
    role: 'assistant',
    text: '你好呀，我叫小屿！这里是只属于你的温柔小岛，不用伪装、不用着急，开心可以分享，难过也可以放心倾诉。我会安安静静陪着你，倾听你的所有情绪。',
    time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
  },
])

function nowText() {
  return new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

function scrollToBottom() {
  nextTick(() => {
    const dom = scrollRef.value
    if (!dom) {
      return
    }
    dom.scrollTop = dom.scrollHeight
  })
}

function togglePanel() {
  panelOpen.value = !panelOpen.value
  if (panelOpen.value) {
    scrollToBottom()
  }
}

function closePanel() {
  panelOpen.value = false
}

function buildHistory() {
  return messages.value
    .filter((msg) => msg.id !== 1)
    .slice(-10)
    .map((msg) => ({
      role: msg.role === 'user' ? 'user' : 'assistant',
      content: msg.text,
    }))
}

function appendAssistantChunk(targetId: number, chunk: string) {
  const target = messages.value.find((msg) => msg.id === targetId)
  if (!target) {
    return
  }
  target.text += chunk
}

function extractDataLines(rawEvent: string) {
  return rawEvent
    .split('\n')
    .filter((line) => line.startsWith('data:'))
    .map((line) => line.slice(5).trim())
}

function getToken() {
  if (typeof window === 'undefined') {
    return ''
  }
  return window.localStorage.getItem(TOKEN_KEY) || ''
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || typing.value) {
    return
  }
  const historyPayload = buildHistory()

  const token = getToken()

  messages.value.push({
    id: Date.now(),
    role: 'user',
    text,
    time: nowText(),
  })

  const assistantId = Date.now() + 1
  messages.value.push({
    id: assistantId,
    role: 'assistant',
    text: '',
    time: nowText(),
  })

  inputText.value = ''
  typing.value = true
  scrollToBottom()

  if (streamAbort) {
    streamAbort.abort()
  }
  streamAbort = new AbortController()

  try {
    const response = await fetch(`${API_BASE_URL}/api/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({
        message: text,
        history: historyPayload,
      }),
      signal: streamAbort.signal,
    })

    if (!response.ok || !response.body) {
      let detail = ''
      try {
        const err = (await response.json()) as { detail?: string }
        detail = err?.detail || ''
      } catch {
        detail = ''
      }
      throw new Error(detail || `请求失败(${response.status})`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) {
        break
      }
      buffer += decoder.decode(value, { stream: true })

      let splitIndex = buffer.indexOf('\n\n')
      while (splitIndex >= 0) {
        const eventBlock = buffer.slice(0, splitIndex)
        buffer = buffer.slice(splitIndex + 2)
        splitIndex = buffer.indexOf('\n\n')

        const dataLines = extractDataLines(eventBlock)
        for (const data of dataLines) {
          if (!data || data === '[DONE]') {
            continue
          }
          try {
            const payload = JSON.parse(data) as { type?: string; content?: string; message?: string }
            if (payload.type === 'delta' && payload.content) {
              appendAssistantChunk(assistantId, payload.content)
              scrollToBottom()
            }
            if (payload.type === 'error' && payload.message) {
              appendAssistantChunk(assistantId, `\n[错误] ${payload.message}`)
              scrollToBottom()
            }
          } catch {
            continue
          }
        }
      }
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : '流式对话失败'
    appendAssistantChunk(assistantId, `对话失败：${message}`)
  } finally {
    typing.value = false
    scrollToBottom()
    streamAbort = null
  }
}

watch(
  () => route.name,
  () => {
    if (!isVisible.value) {
      panelOpen.value = false
      if (streamAbort) {
        streamAbort.abort()
        streamAbort = null
      }
    }
  },
)
</script>

<template>
  <div v-if="isVisible" class="sprite-root">
    <button class="sprite-btn" type="button" @click="togglePanel" aria-label="打开AI对话">
      <img class="sprite-image" src="/assets/xiaoyu.png" alt="心屿小精灵" />
    </button>

    <Transition name="slide-chat">
      <section v-if="panelOpen" class="chat-panel" role="dialog" aria-label="AI聊天窗口">
        <header class="chat-header">
          <div>
            <h3>小屿</h3>
            <p>心屿AI陪伴助手</p>
          </div>
          <button type="button" class="close-btn" @click="closePanel">收起</button>
        </header>

        <div ref="scrollRef" class="chat-body">
          <article v-for="msg in messages" :key="msg.id" class="msg-row" :class="msg.role">
            <p class="bubble">{{ msg.text }}</p>
            <time>{{ msg.time }}</time>
          </article>
          <div v-if="typing" class="typing">小精灵正在组织语言...</div>
        </div>

        <footer class="chat-footer">
          <input
            v-model="inputText"
            type="text"
            maxlength="300"
            placeholder="输入你想说的话..."
            @keydown.enter.prevent="sendMessage"
          />
          <button type="button" @click="sendMessage">发送</button>
        </footer>
      </section>
    </Transition>
  </div>
</template>

<style scoped>
.sprite-root {
  position: fixed;
  right: 0;
  bottom: 88px;
  z-index: 45;
}

.sprite-btn {
  width: 147px;
  height: 183px;
  border: 0;
  border-radius: 28px 0 0 28px;
  background: transparent;
  cursor: pointer;
  box-shadow: none;
  transform: translateX(30px);
  transition: transform 0.25s ease;
  position: relative;
  padding: 0;
}

.sprite-btn:hover {
  transform: translateX(14px);
}

.sprite-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
  filter: drop-shadow(0 12px 18px rgba(59, 32, 20, 0.26));
  display: block;
}

.chat-panel {
  position: fixed;
  right: 12px;
  bottom: 84px;
  width: min(92vw, 380px);
  height: min(72vh, 560px);
  border-radius: 20px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(255, 246, 240, 0.96));
  border: 1px solid rgba(255, 255, 255, 0.9);
  box-shadow: 0 18px 40px rgba(58, 33, 23, 0.2);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  backdrop-filter: blur(14px);
}

.chat-header {
  padding: 14px 16px 10px;
  border-bottom: 1px solid rgba(235, 196, 179, 0.5);
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 10px;
}

.chat-header h3 {
  margin: 0;
  color: #7d3e2d;
  font-size: 18px;
}

.chat-header p {
  margin: 4px 0 0;
  color: #966f5d;
  font-size: 12px;
}

.close-btn {
  border: 0;
  border-radius: 999px;
  padding: 6px 10px;
  background: rgba(255, 180, 147, 0.24);
  color: #7a3f2d;
  cursor: pointer;
}

.chat-body {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.msg-row {
  display: flex;
  flex-direction: column;
  gap: 5px;
  max-width: 86%;
}

.msg-row.user {
  align-self: flex-end;
  align-items: flex-end;
}

.msg-row.assistant {
  align-self: flex-start;
  align-items: flex-start;
}

.bubble {
  margin: 0;
  padding: 10px 12px;
  border-radius: 14px;
  line-height: 1.5;
  font-size: 14px;
}

.msg-row.user .bubble {
  background: linear-gradient(140deg, #ff9d83, #ff7c99);
  color: #fff;
}

.msg-row.assistant .bubble {
  background: #fff;
  color: #5f4538;
  border: 1px solid #f3d7cc;
}

.msg-row time {
  font-size: 11px;
  color: #997f73;
}

.typing {
  font-size: 12px;
  color: #8d7063;
  animation: breath 1s ease-in-out infinite;
}

.chat-footer {
  border-top: 1px solid rgba(235, 196, 179, 0.5);
  padding: 10px;
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 10px;
}

.chat-footer input {
  border: 1px solid #f2cab9;
  border-radius: 12px;
  padding: 10px 12px;
  font-size: 14px;
  outline: none;
  background: rgba(255, 255, 255, 0.92);
}

.chat-footer button {
  border: 0;
  border-radius: 12px;
  padding: 0 16px;
  background: linear-gradient(140deg, #ffa95f, #ff7b8c);
  color: #fff;
  font-weight: 700;
  cursor: pointer;
}

.slide-chat-enter-active,
.slide-chat-leave-active {
  transition: all 0.25s ease;
}

.slide-chat-enter-from,
.slide-chat-leave-to {
  opacity: 0;
  transform: translateX(24px);
}

@keyframes breath {
  0%,
  100% {
    opacity: 0.35;
  }
  50% {
    opacity: 1;
  }
}

@media (max-width: 768px) {
  .sprite-root {
    bottom: 76px;
  }

  .sprite-btn {
    width: 132px;
    height: 165px;
    transform: translateX(26px);
  }

  .sprite-btn:hover {
    transform: translateX(16px);
  }

  .chat-panel {
    right: 8px;
    left: 8px;
    width: auto;
    bottom: 72px;
    height: min(70vh, 520px);
  }
}
</style>
