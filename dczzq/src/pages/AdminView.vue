<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useMindIsland } from '../composables/useMindIsland'

const router = useRouter()
const { currentUser, showMessage } = useMindIsland()
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim() || 'http://127.0.0.1:8000'

type AdminMenu = 'mentor' | 'schedule' | 'tree' | 'xhs'
const activeMenu = ref<AdminMenu>('mentor')

const isAdmin = computed(() => currentUser.value?.role === 'admin')

function getToken() {
  return window.localStorage.getItem('mind_island_token') || ''
}

async function requestApi<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken()
  const headers = new Headers(init?.headers || {})
  if (!headers.has('Content-Type') && !(init?.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
  }
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
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

interface MentorItem {
  id: number
  name: string
  intro: string
  location: string
  avatar: string
  is_active: boolean
}

interface ScheduleItem {
  id: number
  mentor_id: number
  mentor_name: string
  schedule_date: string
  time_slot: string
  capacity: number
  is_active: boolean
}

interface TreePostItem {
  id: number
  tree_slug: string
  content: string
  status: string
  author_account: string | null
  created_at: string
  updated_at: string
}

interface TreeCommentItem {
  id: number
  post_id: number
  content: string
  status: string
  author_account: string | null
  created_at: string
}

interface XhsAuditItem {
  user_id: number
  account: string
  nickname: string
  xhs_url: string
  xhs_audit_status: string
  updated_at: string
}

const mentors = ref<MentorItem[]>([])
const mentorForm = reactive({
  id: 0,
  name: '',
  intro: '',
  location: '',
  avatar: '/assets/doctor1.png',
  is_active: true,
})

const schedules = ref<ScheduleItem[]>([])
const scheduleForm = reactive({
  id: 0,
  mentor_id: 0,
  schedule_date: '',
  time_slot: '8:00-9:30',
  capacity: 5,
  is_active: true,
})

const treePosts = ref<TreePostItem[]>([])
const treeComments = ref<TreeCommentItem[]>([])
const treeStatusFilter = ref('')
const xhsUsers = ref<XhsAuditItem[]>([])
const xhsAuditFilter = ref('')

const TIME_SLOTS = ['8:00-9:30', '10:00-11:30', '14:00-15:30', '16:00-17:30']

function resetMentorForm() {
  mentorForm.id = 0
  mentorForm.name = ''
  mentorForm.intro = ''
  mentorForm.location = ''
  mentorForm.avatar = '/assets/doctor1.png'
  mentorForm.is_active = true
}

function resetScheduleForm() {
  scheduleForm.id = 0
  scheduleForm.mentor_id = 0
  scheduleForm.schedule_date = ''
  scheduleForm.time_slot = '8:00-9:30'
  scheduleForm.capacity = 5
  scheduleForm.is_active = true
}

async function loadMentors() {
  mentors.value = await requestApi<MentorItem[]>('/api/admin/mentors', { method: 'GET' })
  if (!scheduleForm.mentor_id && mentors.value.length) {
    scheduleForm.mentor_id = mentors.value[0]?.id || 0
  }
}

async function saveMentor() {
  try {
    if (!mentorForm.name.trim() || !mentorForm.intro.trim() || !mentorForm.location.trim() || !mentorForm.avatar.trim()) {
      showMessage('error', '导师信息请填写完整')
      return
    }

    const payload = {
      name: mentorForm.name.trim(),
      intro: mentorForm.intro.trim(),
      location: mentorForm.location.trim(),
      avatar: mentorForm.avatar.trim(),
      is_active: mentorForm.is_active,
    }

    if (mentorForm.id > 0) {
      await requestApi(`/api/admin/mentors/${mentorForm.id}`, {
        method: 'PUT',
        body: JSON.stringify(payload),
      })
      showMessage('success', '导师更新成功')
    } else {
      await requestApi('/api/admin/mentors', {
        method: 'POST',
        body: JSON.stringify(payload),
      })
      showMessage('success', '导师创建成功')
    }

    await loadMentors()
    resetMentorForm()
  } catch (error) {
    const msg = error instanceof Error ? error.message : '保存导师失败'
    showMessage('error', msg)
  }
}

function editMentor(item: MentorItem) {
  mentorForm.id = item.id
  mentorForm.name = item.name
  mentorForm.intro = item.intro
  mentorForm.location = item.location
  mentorForm.avatar = item.avatar
  mentorForm.is_active = item.is_active
}

async function deleteMentor(id: number) {
  try {
    await requestApi(`/api/admin/mentors/${id}`, { method: 'DELETE' })
    showMessage('success', '导师删除成功')
    await loadMentors()
  } catch (error) {
    const msg = error instanceof Error ? error.message : '删除导师失败'
    showMessage('error', msg)
  }
}

async function loadSchedules() {
  schedules.value = await requestApi<ScheduleItem[]>('/api/admin/schedules', { method: 'GET' })
}

async function saveSchedule() {
  try {
    if (!scheduleForm.mentor_id || !scheduleForm.schedule_date) {
      showMessage('error', '排班信息请填写完整')
      return
    }

    const payload = {
      mentor_id: scheduleForm.mentor_id,
      schedule_date: scheduleForm.schedule_date,
      time_slot: scheduleForm.time_slot,
      capacity: Number(scheduleForm.capacity),
      is_active: scheduleForm.is_active,
    }

    if (scheduleForm.id > 0) {
      await requestApi(`/api/admin/schedules/${scheduleForm.id}`, {
        method: 'PUT',
        body: JSON.stringify(payload),
      })
      showMessage('success', '排班更新成功')
    } else {
      await requestApi('/api/admin/schedules', {
        method: 'POST',
        body: JSON.stringify(payload),
      })
      showMessage('success', '排班创建成功')
    }

    await loadSchedules()
    resetScheduleForm()
  } catch (error) {
    const msg = error instanceof Error ? error.message : '保存排班失败'
    showMessage('error', msg)
  }
}

function editSchedule(item: ScheduleItem) {
  scheduleForm.id = item.id
  scheduleForm.mentor_id = item.mentor_id
  scheduleForm.schedule_date = item.schedule_date
  scheduleForm.time_slot = item.time_slot
  scheduleForm.capacity = item.capacity
  scheduleForm.is_active = item.is_active
}

async function deleteSchedule(id: number) {
  try {
    await requestApi(`/api/admin/schedules/${id}`, { method: 'DELETE' })
    showMessage('success', '排班删除成功')
    await loadSchedules()
  } catch (error) {
    const msg = error instanceof Error ? error.message : '删除排班失败'
    showMessage('error', msg)
  }
}

async function loadTreeModeration() {
  const suffix = treeStatusFilter.value ? `?status=${encodeURIComponent(treeStatusFilter.value)}` : ''
  treePosts.value = await requestApi<TreePostItem[]>(`/api/admin/tree/posts${suffix}`, { method: 'GET' })
  treeComments.value = await requestApi<TreeCommentItem[]>(`/api/admin/tree/comments${suffix}`, { method: 'GET' })
}

async function loadXhsUsers() {
  const suffix = xhsAuditFilter.value ? `?audit_status=${encodeURIComponent(xhsAuditFilter.value)}` : ''
  xhsUsers.value = await requestApi<XhsAuditItem[]>(`/api/admin/xhs/users${suffix}`, { method: 'GET' })
}

async function auditXhsUser(item: XhsAuditItem, status: 'approved' | 'rejected') {
  try {
    await requestApi(`/api/admin/xhs/users/${item.user_id}/audit`, {
      method: 'PUT',
      body: JSON.stringify({ status }),
    })
    showMessage('success', status === 'approved' ? '已审核通过' : '已标记不通过')
    await loadXhsUsers()
  } catch (error) {
    const msg = error instanceof Error ? error.message : '审核失败'
    showMessage('error', msg)
  }
}

async function togglePostStatus(item: TreePostItem) {
  const nextStatus = item.status === 'approved' ? 'blocked' : 'approved'
  try {
    await requestApi(`/api/admin/tree/posts/${item.id}/status`, {
      method: 'PUT',
      body: JSON.stringify({ status: nextStatus }),
    })
    showMessage('success', nextStatus === 'blocked' ? '帖子已屏蔽' : '帖子已取消屏蔽')
    await loadTreeModeration()
  } catch (error) {
    const msg = error instanceof Error ? error.message : '更新帖子状态失败'
    showMessage('error', msg)
  }
}

async function toggleCommentStatus(item: TreeCommentItem) {
  const nextStatus = item.status === 'approved' ? 'blocked' : 'approved'
  try {
    await requestApi(`/api/admin/tree/comments/${item.id}/status`, {
      method: 'PUT',
      body: JSON.stringify({ status: nextStatus }),
    })
    showMessage('success', nextStatus === 'blocked' ? '评论已屏蔽' : '评论已取消屏蔽')
    await loadTreeModeration()
  } catch (error) {
    const msg = error instanceof Error ? error.message : '更新评论状态失败'
    showMessage('error', msg)
  }
}

function openMenu(menu: AdminMenu) {
  activeMenu.value = menu
  if (menu === 'mentor') {
    void loadMentors()
  }
  if (menu === 'schedule') {
    void Promise.all([loadMentors(), loadSchedules()])
  }
  if (menu === 'tree') {
    void loadTreeModeration()
  }
  if (menu === 'xhs') {
    void loadXhsUsers()
  }
}

onMounted(async () => {
  if (!isAdmin.value) {
    showMessage('error', '仅管理员可访问')
    router.push('/profile')
    return
  }
  await loadMentors()
})
</script>

<template>
  <section class="admin-page reveal">
    <div class="admin-layout">
      <aside class="drawer glass">
        <h3>管理中心</h3>
        <button class="menu-btn" :class="{ active: activeMenu === 'mentor' }" @click="openMenu('mentor')">导师基本信息管理</button>
        <button class="menu-btn" :class="{ active: activeMenu === 'schedule' }" @click="openMenu('schedule')">导师排班信息管理</button>
        <button class="menu-btn" :class="{ active: activeMenu === 'tree' }" @click="openMenu('tree')">树洞管理</button>
        <button class="menu-btn" :class="{ active: activeMenu === 'xhs' }" @click="openMenu('xhs')">小红书信息管理</button>
      </aside>

      <main class="panel glass" v-if="activeMenu === 'mentor'">
        <h3>导师基本信息管理</h3>
        <div class="form-grid">
          <input v-model="mentorForm.name" placeholder="导师姓名" />
          <input v-model="mentorForm.location" placeholder="地点" />
          <input v-model="mentorForm.avatar" placeholder="头像路径，例如 /assets/doctor1.png" />
          <label class="inline-check"><input type="checkbox" v-model="mentorForm.is_active" />启用</label>
          <textarea v-model="mentorForm.intro" rows="3" placeholder="导师简介"></textarea>
        </div>
        <div class="action-row">
          <button class="primary" @click="saveMentor">{{ mentorForm.id > 0 ? '更新导师' : '新增导师' }}</button>
          <button class="ghost" @click="resetMentorForm">重置</button>
        </div>

        <table class="grid-table">
          <thead>
            <tr><th>ID</th><th>姓名</th><th>地点</th><th>状态</th><th>操作</th></tr>
          </thead>
          <tbody>
            <tr v-for="item in mentors" :key="item.id">
              <td>{{ item.id }}</td>
              <td>{{ item.name }}</td>
              <td>{{ item.location }}</td>
              <td>{{ item.is_active ? '在岗可约' : '休整中' }}</td>
              <td class="action-cell">
                <button class="small" @click="editMentor(item)">编辑</button>
                <button class="small danger" @click="deleteMentor(item.id)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </main>

      <main class="panel glass" v-if="activeMenu === 'schedule'">
        <h3>导师排班信息管理</h3>
        <div class="form-grid schedule-grid">
          <select v-model.number="scheduleForm.mentor_id">
            <option :value="0">请选择导师</option>
            <option v-for="mentor in mentors" :key="mentor.id" :value="mentor.id">{{ mentor.name }}</option>
          </select>
          <input v-model="scheduleForm.schedule_date" type="date" />
          <select v-model="scheduleForm.time_slot">
            <option v-for="slot in TIME_SLOTS" :key="slot" :value="slot">{{ slot }}</option>
          </select>
          <input v-model.number="scheduleForm.capacity" type="number" min="1" max="200" placeholder="容量" />
          <label class="inline-check"><input type="checkbox" v-model="scheduleForm.is_active" />启用</label>
        </div>
        <div class="action-row">
          <button class="primary" @click="saveSchedule">{{ scheduleForm.id > 0 ? '更新排班' : '新增排班' }}</button>
          <button class="ghost" @click="resetScheduleForm">重置</button>
        </div>

        <table class="grid-table">
          <thead>
            <tr><th>ID</th><th>导师</th><th>日期</th><th>时段</th><th>容量</th><th>状态</th><th>操作</th></tr>
          </thead>
          <tbody>
            <tr v-for="item in schedules" :key="item.id">
              <td>{{ item.id }}</td>
              <td>{{ item.mentor_name }}</td>
              <td>{{ item.schedule_date }}</td>
              <td>{{ item.time_slot }}</td>
              <td>{{ item.capacity }}</td>
              <td>{{ item.is_active ? '启用' : '停用' }}</td>
              <td class="action-cell">
                <button class="small" @click="editSchedule(item)">编辑</button>
                <button class="small danger" @click="deleteSchedule(item.id)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </main>

      <main class="panel glass" v-if="activeMenu === 'tree'">
        <h3>树洞管理</h3>
        <div class="action-row">
          <select class="nice-select" v-model="treeStatusFilter" @change="loadTreeModeration">
            <option value="">全部状态</option>
            <option value="approved">approved</option>
            <option value="blocked">blocked</option>
          </select>
          <button class="ghost" @click="loadTreeModeration">刷新</button>
        </div>

        <h4>帖子管理</h4>
        <table class="grid-table">
          <thead>
            <tr><th>ID</th><th>分区</th><th>作者</th><th>状态</th><th>内容</th><th>操作</th></tr>
          </thead>
          <tbody>
            <tr v-for="item in treePosts" :key="item.id">
              <td>{{ item.id }}</td>
              <td>{{ item.tree_slug }}</td>
              <td>{{ item.author_account || '匿名' }}</td>
              <td>{{ item.status }}</td>
              <td class="content-cell">{{ item.content }}</td>
              <td>
                <button class="small" @click="togglePostStatus(item)">{{ item.status === 'approved' ? '屏蔽' : '取消屏蔽' }}</button>
              </td>
            </tr>
          </tbody>
        </table>

        <h4>评论管理</h4>
        <table class="grid-table">
          <thead>
            <tr><th>ID</th><th>帖子ID</th><th>作者</th><th>状态</th><th>内容</th><th>操作</th></tr>
          </thead>
          <tbody>
            <tr v-for="item in treeComments" :key="item.id">
              <td>{{ item.id }}</td>
              <td>{{ item.post_id }}</td>
              <td>{{ item.author_account || '匿名' }}</td>
              <td>{{ item.status }}</td>
              <td class="content-cell">{{ item.content }}</td>
              <td>
                <button class="small" @click="toggleCommentStatus(item)">{{ item.status === 'approved' ? '屏蔽' : '取消屏蔽' }}</button>
              </td>
            </tr>
          </tbody>
        </table>
      </main>

      <main class="panel glass" v-if="activeMenu === 'xhs'">
        <h3>小红书信息管理</h3>
        <div class="action-row">
          <select class="nice-select" v-model="xhsAuditFilter" @change="loadXhsUsers">
            <option value="">全部审核状态</option>
            <option value="pending">待审核</option>
            <option value="approved">已通过</option>
            <option value="rejected">未通过</option>
          </select>
          <button class="ghost" @click="loadXhsUsers">刷新</button>
        </div>

        <table class="grid-table">
          <thead>
            <tr><th>用户ID</th><th>账号</th><th>昵称</th><th>小红书主页</th><th>审核状态</th><th>操作</th></tr>
          </thead>
          <tbody>
            <tr v-for="item in xhsUsers" :key="item.user_id">
              <td>{{ item.user_id }}</td>
              <td>{{ item.account }}</td>
              <td>{{ item.nickname }}</td>
              <td class="content-cell"><a :href="item.xhs_url" target="_blank" rel="noopener noreferrer">{{ item.xhs_url }}</a></td>
              <td>{{ item.xhs_audit_status === 'approved' ? '已通过' : item.xhs_audit_status === 'rejected' ? '未通过' : '待审核' }}</td>
              <td class="action-cell">
                <button class="small" @click="auditXhsUser(item, 'approved')">通过</button>
                <button class="small danger" @click="auditXhsUser(item, 'rejected')">不通过</button>
              </td>
            </tr>
          </tbody>
        </table>
      </main>
    </div>
  </section>
</template>

<style scoped>
.admin-page { padding: 18px; }
.admin-layout { display: grid; grid-template-columns: 260px minmax(0, 1fr); gap: 12px; min-height: 72vh; }
.glass { background: rgba(255,255,255,0.55); border: 1px solid rgba(255,255,255,0.7); backdrop-filter: blur(12px); border-radius: 16px; box-shadow: 0 10px 26px rgba(56,79,120,0.12); }
.drawer { padding: 14px; display: grid; gap: 10px; align-content: start; }
.menu-btn { border: 0; border-radius: 10px; padding: 10px 12px; text-align: left; cursor: pointer; background: rgba(255,255,255,0.72); color: #2d4b76; }
.menu-btn.active { background: linear-gradient(120deg, #ffc8dd, #ffdae9); color: #8a3b61; }
.panel { padding: 16px; overflow: auto; }
.form-grid { display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 8px; margin-top: 8px; }
.schedule-grid { grid-template-columns: repeat(3, minmax(0,1fr)); }
.form-grid textarea { grid-column: 1 / -1; }
.form-grid input, .form-grid textarea, .form-grid select { border: 0; border-radius: 10px; padding: 10px 12px; background: rgba(255,255,255,0.85); }
.inline-check { display: inline-flex; align-items: center; gap: 8px; padding: 8px 2px; color: #3c5e8e; }
.action-row { display: flex; gap: 8px; margin: 10px 0; align-items: center; }
.primary, .ghost, .small { border: 0; border-radius: 10px; padding: 8px 12px; cursor: pointer; }
.primary { background: linear-gradient(120deg, #ffbfd7, #ffd5e6); color: #8a3b61; }
.ghost { background: rgba(255,255,255,0.85); color: #315483; }
.small { background: rgba(255,255,255,0.85); color: #315483; }
.small.danger { background: #ffe4e8; color: #9b3249; }
.action-cell { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.nice-select {
  border: 1px solid rgba(128, 162, 207, 0.38);
  border-radius: 10px;
  padding: 8px 30px 8px 12px;
  background: linear-gradient(180deg, rgba(255,255,255,0.95), rgba(238,246,255,0.9));
  color: #2f537f;
  font-weight: 600;
  outline: none;
  appearance: none;
  background-image:
    linear-gradient(45deg, transparent 50%, #5f86b8 50%),
    linear-gradient(135deg, #5f86b8 50%, transparent 50%);
  background-position:
    calc(100% - 14px) calc(50% - 2px),
    calc(100% - 9px) calc(50% - 2px);
  background-size: 5px 5px, 5px 5px;
  background-repeat: no-repeat;
}
.grid-table { width: 100%; border-collapse: collapse; margin-top: 8px; }
.grid-table th, .grid-table td { border-bottom: 1px solid rgba(113,146,189,0.22); padding: 8px; text-align: left; vertical-align: top; }
.content-cell { max-width: 460px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.reveal { animation: reveal 0.35s ease both; }
@keyframes reveal { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
@media (max-width: 980px) {
  .admin-layout { grid-template-columns: 1fr; }
  .form-grid, .schedule-grid { grid-template-columns: 1fr; }
}
</style>
