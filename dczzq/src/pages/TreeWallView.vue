<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMindIsland } from '../composables/useMindIsland'

interface CommentItem {
  id: number
  content: string
  createdAt: string
}

interface PostItem {
  id: number
  content: string
  createdAt: string
  hugCount: number
  senseCount: number
  commentCount: number
  hugged: boolean
  sensed: boolean
  comments: CommentItem[]
}

const route = useRoute()
const router = useRouter()
const { showMessage } = useMindIsland()

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim() || 'http://127.0.0.1:8000'

function getToken() {
  return window.localStorage.getItem('mind_island_token') || ''
}

async function requestApi<T>(path: string, init?: RequestInit, withAuth = false): Promise<T> {
  const headers = new Headers(init?.headers || {})
  if (!headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }
  if (withAuth) {
    const token = getToken()
    if (token) {
      headers.set('Authorization', `Bearer ${token}`)
    }
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
  })

  let body: unknown = null
  try {
    body = await response.json()
  } catch {
    body = null
  }

  if (!response.ok) {
    const detail =
      typeof body === 'object' && body !== null && 'detail' in body
        ? String((body as Record<string, unknown>).detail)
        : `请求失败(${response.status})`
    throw new Error(detail)
  }

  return body as T
}

interface BackendComment {
  id: number
  post_id: number
  content: string
  created_at: string
}

interface BackendPost {
  id: number
  tree_slug: string
  content: string
  created_at: string
  hug_count: number
  sense_count: number
  comment_count: number
  hugged: boolean
  sensed: boolean
  comments: BackendComment[]
}

interface ToggleResult {
  post_id: number
  reaction_type: 'hug' | 'sense'
  active: boolean
  hug_count: number
  sense_count: number
}

const treeConfig: Record<string, string> = {
  anxu: '安绪树',
  baitai: '百态树',
  nuanguang: '暖光树',
}

const slug = computed(() => String(route.params.treeSlug || ''))
const treeName = computed(() => treeConfig[slug.value] || '树洞分区')

const leftPanel = ref<'notice' | 'submit'>('notice')
const postDraft = ref('')
const commentDrafts = reactive<Record<number, string>>({})
const expandedComments = reactive<Record<number, boolean>>({})
const loading = ref(false)
const noticeList = [
  '请勿发布人身攻击与泄露隐私内容。',
  '请尊重他人，不传播未核实信息。',
  '如果内容涉及紧急心理危机，请及时联系学校老师或专业机构。',
]
const posts = ref<PostItem[]>([])

if (!treeConfig[slug.value]) {
  router.replace('/tree-hole')
}

function mapPost(item: BackendPost): PostItem {
  return {
    id: item.id,
    content: item.content,
    createdAt: item.created_at,
    hugCount: item.hug_count,
    senseCount: item.sense_count,
    commentCount: item.comment_count,
    hugged: item.hugged,
    sensed: item.sensed,
    comments: item.comments.map((comment) => ({
      id: comment.id,
      content: comment.content,
      createdAt: comment.created_at,
    })),
  }
}

async function fetchPosts() {
  if (!treeConfig[slug.value]) {
    return
  }
  loading.value = true
  try {
    const data = await requestApi<BackendPost[]>(`/api/tree/posts?tree_slug=${encodeURIComponent(slug.value)}`, { method: 'GET' }, true)
    posts.value = data.map(mapPost)
  } catch (error) {
    const message = error instanceof Error ? error.message : '加载树洞失败'
    showMessage('error', message)
  } finally {
    loading.value = false
  }
}

void fetchPosts()

async function submitPost() {
  const content = postDraft.value.trim()
  if (!content) {
    return
  }
  try {
    const created = await requestApi<BackendPost>(
      '/api/tree/posts',
      {
        method: 'POST',
        body: JSON.stringify({ tree_slug: slug.value, content }),
      },
      true,
    )
    posts.value.unshift(mapPost(created))
    postDraft.value = ''
    showMessage('success', '发帖成功')
  } catch (error) {
    const message = error instanceof Error ? error.message : '发帖失败'
    showMessage('error', message)
  }
}

async function submitComment(postId: number) {
  const raw = commentDrafts[postId] || ''
  const content = raw.trim()
  if (!content) {
    return
  }
  const post = posts.value.find((item) => item.id === postId)
  if (!post) {
    return
  }
  try {
    const created = await requestApi<BackendComment>(
      `/api/tree/posts/${postId}/comments`,
      {
        method: 'POST',
        body: JSON.stringify({ content }),
      },
      true,
    )
    post.comments.push({
      id: created.id,
      content: created.content,
      createdAt: created.created_at,
    })
    post.commentCount += 1
    commentDrafts[postId] = ''
    showMessage('success', '评论成功')
  } catch (error) {
    const message = error instanceof Error ? error.message : '评论失败'
    showMessage('error', message)
  }
}

async function toggleReaction(postId: number, type: 'hug' | 'sense') {
  const post = posts.value.find((item) => item.id === postId)
  if (!post) {
    return
  }
  try {
    const result = await requestApi<ToggleResult>(
      `/api/tree/posts/${postId}/reactions/toggle`,
      {
        method: 'POST',
        body: JSON.stringify({ reaction_type: type }),
      },
      true,
    )
    post.hugCount = result.hug_count
    post.senseCount = result.sense_count
    if (type === 'hug') {
      post.hugged = result.active
    }
    if (type === 'sense') {
      post.sensed = result.active
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : '操作失败'
    showMessage('error', message)
  }
}

const approvedPosts = computed(() => [...posts.value])

function approvedComments(post: PostItem) {
  return post.comments
}

const hotPosts = computed(() => {
  return [...approvedPosts.value]
    .sort((a, b) => timeScore(b.createdAt) - timeScore(a.createdAt))
    .slice(0, 10)
})

function timeScore(createdAt: string) {
  const timestamp = Date.parse(createdAt)
  if (Number.isNaN(timestamp)) {
    return 0
  }
  return timestamp
}

function excerpt(content: string) {
  return content.length > 18 ? `${content.slice(0, 18)}...` : content
}

function toggleComments(postId: number) {
  expandedComments[postId] = !expandedComments[postId]
}

function isCommentsOpen(postId: number) {
  return !!expandedComments[postId]
}
</script>

<template>
  <section class="wall-page reveal">
    <div class="wall-layout">
      <aside class="left-rail glass-panel">
        <button class="home-title" type="button" @click="router.push('/tree-hole')">首页</button>
        <p class="tree-title">{{ treeName }}</p>

        <button
          class="rail-card"
          :class="{ active: leftPanel === 'notice' }"
          type="button"
          @click="leftPanel = 'notice'"
        >
          公告
        </button>
        <button
          class="rail-card"
          :class="{ active: leftPanel === 'submit' }"
          type="button"
          @click="leftPanel = 'submit'"
        >
          投递树洞
        </button>

        <section v-if="leftPanel === 'notice'" class="rail-content">
          <p v-for="line in noticeList" :key="line" class="notice-line">{{ line }}</p>
        </section>

        <section v-else class="rail-content">
          <textarea v-model="postDraft" placeholder="匿名写下你的心声吧！" />
          <button class="submit-btn" type="button" @click="submitPost">匿名发布</button>
        </section>
      </aside>

      <main class="center-feed">
        <p v-if="loading" class="pending">正在加载树洞内容...</p>
        <article v-for="post in approvedPosts" :key="post.id" class="post-card glass-panel">
          <header class="post-head">
            <div class="author-wrap">
              <span class="avatar">👤</span>
              <span class="time">{{ post.createdAt }}</span>
            </div>
          </header>

          <p class="post-content">{{ post.content }}</p>

          <footer class="post-foot">
            <button
              class="metric like left"
              type="button"
              @click="toggleReaction(post.id, 'hug')"
            >
              <img class="metric-icon" :class="{ active: post.hugged }" src="/assets/hug.png" alt="抱抱" />
              <span>抱抱 {{ post.hugCount }}</span>
            </button>
            <button class="metric center" type="button" @click="toggleComments(post.id)">
              <img class="metric-icon" src="/assets/comments.png" alt="评论" />
              <span>评论 {{ post.commentCount }}</span>
            </button>
            <button
              class="metric right"
              type="button"
              @click="toggleReaction(post.id, 'sense')"
            >
              <img class="metric-icon" :class="{ active: post.sensed }" src="/assets/sense.png" alt="同感" />
              <span>同感 {{ post.senseCount }}</span>
            </button>
          </footer>

          <div v-if="isCommentsOpen(post.id)" class="comment-list">
            <article v-for="comment in approvedComments(post)" :key="comment.id" class="comment-card">
              <div class="comment-head">
                <span class="comment-avatar">👤</span>
                <span class="comment-time">{{ comment.createdAt }}</span>
              </div>
              <p class="comment">{{ comment.content }}</p>
            </article>
            <div class="comment-editor">
              <input v-model="commentDrafts[post.id]" placeholder="匿名评论" />
              <button type="button" @click="submitComment(post.id)">发送</button>
            </div>
          </div>
        </article>
      </main>

      <aside class="right-hot glass-panel">
        <h3 class="hot-title">嘘，新的小情绪悄悄进入树洞啦~</h3>
        <article v-for="item in hotPosts" :key="item.id" class="hot-item">
          <span class="hot-text">{{ excerpt(item.content) }}</span>
          <span class="hot-time">{{ item.createdAt }}</span>
        </article>
        <p v-if="hotPosts.length === 0" class="empty">暂无上榜内容</p>
      </aside>
    </div>
  </section>
</template>

<style scoped>
.wall-page {
  border-radius: 28px;
  padding: 18px;
  min-height: calc(100vh - 120px);
  background:
    linear-gradient(rgba(234, 245, 255, 0.82), rgba(223, 241, 255, 0.8), rgba(237, 247, 255, 0.84)),
    url('/assets/bg2.jpg') center / cover no-repeat;
  color: #1f2a44;
}

.wall-layout {
  display: grid;
  grid-template-columns: 250px minmax(0, 1fr) 290px;
  gap: 14px;
  min-height: calc(100vh - 156px);
  align-items: stretch;
}

.glass-panel {
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(184, 213, 245, 0.7);
  border-radius: 18px;
  box-shadow: 0 10px 24px rgba(70, 120, 180, 0.12);
  backdrop-filter: blur(8px);
}

.left-rail {
  padding: 14px;
  min-height: 100%;
}

.home-title {
  border: 0;
  background: transparent;
  color: #2a4f80;
  font-size: 2rem;
  font-weight: 900;
  letter-spacing: 2px;
  cursor: pointer;
  padding: 0;
}

.tree-title {
  margin-top: 4px;
  color: #6884af;
}

.rail-card {
  margin-top: 10px;
  width: 100%;
  border: 1px solid rgba(154, 194, 236, 0.55);
  border-radius: 12px;
  padding: 10px;
  background: rgba(239, 248, 255, 0.9);
  color: #2e5488;
  text-align: left;
  cursor: pointer;
}

.rail-card.active {
  background: linear-gradient(120deg, rgba(157, 207, 255, 0.7), rgba(183, 225, 255, 0.9));
}

.rail-content {
  margin-top: 12px;
}

.notice-line {
  margin-top: 8px;
  color: #476f9e;
  font-size: 0.94rem;
}

.submit-btn,
.comment-editor button {
  border: 0;
  border-radius: 999px;
  padding: 6px 12px;
  cursor: pointer;
  background: linear-gradient(120deg, #ff8ea8, #ffb27a);
  color: #fff;
}

.rail-content textarea {
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  min-height: 120px;
  border: 1px solid rgba(169, 205, 242, 0.8);
  border-radius: 12px;
  padding: 10px;
  background: rgba(255, 255, 255, 0.95);
  color: #284672;
  resize: vertical;
  font-family: inherit;
}

.submit-btn {
  margin-top: 10px;
}

.center-feed {
  display: grid;
  gap: 12px;
  align-content: start;
  min-height: 100%;
}

.post-card {
  display: flex;
  flex-direction: column;
  padding: 14px 14px 0;
}

.post-head {
  display: flex;
  justify-content: flex-start;
}

.author-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: rgba(255, 255, 255, 0.22);
  font-size: 1.05rem;
}

.time {
  color: #6b86af;
  font-size: 1.03rem;
  font-weight: 800;
}

.post-content {
  margin-top: 8px;
  line-height: 1.7;
}

.comment-list {
  margin-top: 10px;
  margin-bottom: 12px;
  border-top: 1px dashed rgba(146, 186, 229, 0.5);
  padding-top: 10px;
}

.comment {
  margin-top: 7px;
  border-radius: 10px;
  padding: 8px;
  background: rgba(232, 244, 255, 0.88);
}

.comment-card {
  margin-top: 7px;
}

.comment-head {
  display: flex;
  align-items: center;
  gap: 8px;
}

.comment-avatar {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: rgba(255, 255, 255, 0.86);
}

.comment-time {
  color: #6b86af;
  font-size: 0.86rem;
}

.pending {
  margin-top: 6px;
  color: #6386b6;
  font-size: 0.9rem;
}

.comment-editor {
  margin-top: 8px;
  display: flex;
  gap: 8px;
}

.comment-editor input {
  flex: 1;
  max-width: 100%;
  box-sizing: border-box;
  border: 1px solid rgba(161, 201, 241, 0.75);
  border-radius: 10px;
  padding: 8px;
  background: rgba(255, 255, 255, 0.95);
  color: #274571;
}

.post-foot {
  margin: auto -14px 0;
  padding: 10px 14px;
  border-top: 1px solid rgba(158, 197, 239, 0.45);
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  align-items: center;
}

.metric {
  color: #4a6f9e;
  background: transparent;
  border: 0;
  font-size: 1.25rem;
  padding: 0;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-family: 'KaiTi', 'STKaiti', serif;
  letter-spacing: 1px;
  transition: transform 0.2s ease, filter 0.2s ease, text-shadow 0.2s ease;
}

.metric-icon {
  width: 48px;
  height: 48px;
  object-fit: contain;
}

.metric-icon.active {
  transform: translateY(-2px) scale(1.08);
  filter: drop-shadow(0 0 18px rgba(106, 170, 255, 0.82));
  text-shadow: 0 0 14px rgba(122, 176, 255, 0.68);
}

.metric.left {
  justify-self: start;
}

.metric.center {
  justify-self: center;
}

.metric.right {
  justify-self: end;
}

.metric.like {
  color: #4a6f9e;
}

.right-hot {
  padding: 14px;
  min-height: 100%;
}

.hot-title {
  white-space: normal;
  line-height: 1.35;
}

.hot-item {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  border-radius: 10px;
  padding: 8px;
  background: rgba(236, 247, 255, 0.95);
}

.hot-text {
  color: #2f4d78;
}

.hot-time {
  color: #7390b6;
  font-size: 0.9rem;
}

.empty {
  margin-top: 8px;
  color: #6488b8;
}

.reveal {
  animation: reveal 0.45s ease both;
}

@keyframes reveal {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 1100px) {
  .wall-layout {
    grid-template-columns: 220px minmax(0, 1fr);
  }

  .right-hot {
    grid-column: 1 / -1;
  }
}

@media (max-width: 860px) {
  .wall-layout {
    grid-template-columns: 1fr;
  }
}
</style>
