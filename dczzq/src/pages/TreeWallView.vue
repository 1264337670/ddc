<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

interface CommentItem {
  id: number
  content: string
  status: 'approved' | 'pending' | 'rejected'
  createdAt: string
}

interface PostItem {
  id: number
  content: string
  status: 'approved' | 'pending' | 'rejected'
  createdAt: string
  likes: number
  views: number
  comments: CommentItem[]
}

interface ModerationItem {
  id: number
  type: 'post' | 'comment'
  postId: number
  commentId?: number
  content: string
  createdAt: string
}

const route = useRoute()
const router = useRouter()

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
const activeState = reactive<Record<number, { hug: boolean; sense: boolean }>>({})
const noticeList = [
  '请勿发布人身攻击与泄露隐私内容。',
  '所有发帖和评论都需要审核后才会公开显示。',
  '如果内容涉及紧急心理危机，请及时联系学校老师或专业机构。',
]

const seedPosts: Record<string, PostItem[]> = {
  anxu: [
    {
      id: 1,
      content: '最近备赛压力很大，晚上总是失眠，但我还是想继续坚持下去。',
      status: 'approved',
      createdAt: '今天 09:15',
      likes: 46,
      views: 321,
      comments: [
        { id: 11, content: '抱抱你，先把目标拆小，一步一步来。', status: 'approved', createdAt: '今天 09:30' },
      ],
    },
    {
      id: 2,
      content: '和朋友闹别扭后心里一直堵着，想主动和好又怕尴尬。',
      status: 'approved',
      createdAt: '今天 11:42',
      likes: 30,
      views: 268,
      comments: [
        { id: 21, content: '可以先发一句“我很在意这段关系”。', status: 'approved', createdAt: '今天 11:56' },
      ],
    },
  ],
  baitai: [
    {
      id: 3,
      content: '第一次上台汇报，手一直抖，但讲完后发现其实没那么可怕。',
      status: 'approved',
      createdAt: '今天 08:24',
      likes: 52,
      views: 410,
      comments: [
        { id: 31, content: '你已经突破舒适区了，超厉害。', status: 'approved', createdAt: '今天 09:01' },
      ],
    },
  ],
  nuanguang: [
    {
      id: 4,
      content: '今天在食堂有人给我让座，突然觉得这个世界还是很温暖。',
      status: 'approved',
      createdAt: '今天 13:02',
      likes: 67,
      views: 520,
      comments: [
        { id: 41, content: '善意会传递，愿你也被温柔对待。', status: 'approved', createdAt: '今天 13:20' },
      ],
    },
  ],
}

const posts = ref<PostItem[]>(seedPosts[slug.value] ? [...seedPosts[slug.value]] : [])
const seq = ref(1000)

if (!treeConfig[slug.value]) {
  router.replace('/tree-hole')
}

function nextId() {
  seq.value += 1
  return seq.value
}

function formatNow() {
  return '刚刚'
}

function submitPost() {
  const content = postDraft.value.trim()
  if (!content) {
    return
  }
  const postId = nextId()
  posts.value.unshift({
    id: postId,
    content,
    status: 'pending',
    createdAt: formatNow(),
    likes: 0,
    views: Math.floor(Math.random() * 20) + 1,
    comments: [],
  })
  const queueItem: ModerationItem = {
    id: nextId(),
    type: 'post',
    postId,
    content,
    createdAt: formatNow(),
  }
  postDraft.value = ''
  window.setTimeout(() => {
    const post = posts.value.find((item) => item.id === queueItem.postId)
    if (post && post.status === 'pending') {
      post.status = 'approved'
    }
  }, 700)
}

function submitComment(postId: number) {
  const raw = commentDrafts[postId] || ''
  const content = raw.trim()
  if (!content) {
    return
  }
  const post = posts.value.find((item) => item.id === postId)
  if (!post) {
    return
  }
  const commentId = nextId()
  post.comments.push({
    id: commentId,
    content,
    status: 'pending',
    createdAt: formatNow(),
  })
  const queueItem: ModerationItem = {
    id: nextId(),
    type: 'comment',
    postId,
    commentId,
    content,
    createdAt: formatNow(),
  }
  commentDrafts[postId] = ''
  window.setTimeout(() => {
    const foundPost = posts.value.find((item) => item.id === queueItem.postId)
    const comment = foundPost?.comments.find((item) => item.id === queueItem.commentId)
    if (comment && comment.status === 'pending') {
      comment.status = 'approved'
    }
  }, 700)
}

function likePost(postId: number) {
  const post = posts.value.find((item) => item.id === postId)
  if (!post || post.status !== 'approved') {
    return
  }
}

function sensePost(postId: number) {
  const post = posts.value.find((item) => item.id === postId)
  if (!post || post.status !== 'approved') {
    return
  }
}

function triggerPulse(postId: number, type: 'hug' | 'sense') {
  if (!activeState[postId]) {
    activeState[postId] = { hug: false, sense: false }
  }
  activeState[postId][type] = true
}

const approvedPosts = computed(() => posts.value.filter((item) => item.status === 'approved'))

function approvedComments(post: PostItem) {
  return post.comments.filter((item) => item.status === 'approved')
}

function pendingCount(post: PostItem) {
  return post.comments.filter((item) => item.status === 'pending').length
}

const hotPosts = computed(() => {
  return [...approvedPosts.value]
    .sort((a, b) => timeScore(b.createdAt) - timeScore(a.createdAt))
    .slice(0, 10)
})

function timeScore(createdAt: string) {
  if (createdAt.includes('刚刚')) {
    return Date.now()
  }
  const match = createdAt.match(/(\d{1,2}):(\d{2})/)
  if (!match) {
    return 0
  }
  const hours = Number(match[1] || 0)
  const minutes = Number(match[2] || 0)
  return hours * 60 + minutes
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
          <textarea v-model="postDraft" placeholder="匿名写下你的心声，提交后进入审核..." />
          <button class="submit-btn" type="button" @click="submitPost">匿名发布</button>
        </section>
      </aside>

      <main class="center-feed">
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
              @click="likePost(post.id); triggerPulse(post.id, 'hug')"
            >
              <img class="metric-icon" :class="{ active: activeState[post.id]?.hug }" src="/assets/hug.png" alt="抱抱" />
              <span>抱抱</span>
            </button>
            <button class="metric center" type="button" @click="toggleComments(post.id)">
              <img class="metric-icon" src="/assets/comments.png" alt="评论" />
              <span>评论</span>
            </button>
            <button
              class="metric right"
              type="button"
              @click="sensePost(post.id); triggerPulse(post.id, 'sense')"
            >
              <img class="metric-icon" :class="{ active: activeState[post.id]?.sense }" src="/assets/sense.png" alt="同感" />
              <span>同感</span>
            </button>
          </footer>

          <div v-if="isCommentsOpen(post.id)" class="comment-list">
            <p v-for="comment in approvedComments(post)" :key="comment.id" class="comment">{{ comment.content }}</p>
            <p v-if="pendingCount(post) > 0" class="pending">还有 {{ pendingCount(post) }} 条评论待审核</p>
            <div class="comment-editor">
              <input v-model="commentDrafts[post.id]" placeholder="匿名评论（需审核）" />
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
