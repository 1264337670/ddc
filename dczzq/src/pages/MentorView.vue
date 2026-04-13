<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useMindIsland } from '../composables/useMindIsland'

interface MentorSlot {
  slotId: string
  mentorId: number
  teacher: string
  dateText: string
  dateIso: string
  time: string
  location: string
  intro: string
  avatar: string
  booked: number
  reservedByMe: boolean
}

interface AppointmentRecord {
  id: number
  mentorId: number
  teacher: string
  dateText: string
  dateIso: string
  time: string
  location: string
}

const selectedDate = ref(new Date())
const calendarCursor = ref(new Date(selectedDate.value.getFullYear(), selectedDate.value.getMonth(), 1))
const loadingSlots = ref(false)

const searchName = ref('')
const searchLocation = ref('')
const appliedSearchName = ref('')
const appliedSearchLocation = ref('')
const showMyAppointments = ref(false)
const isSearchMode = ref(false)

const slots = ref<MentorSlot[]>([])
const myAppointments = ref<AppointmentRecord[]>([])

const { currentUser, showMessage } = useMindIsland()
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

  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers,
    })
  } catch {
    throw new Error('后端不可用或网络异常，请确认 FastAPI 服务和数据库已启动')
  }

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

interface BackendSlot {
  slot_id: string
  mentor_id: number
  teacher: string
  date_text: string
  date_iso: string
  time: string
  location: string
  intro: string
  avatar: string
  booked: number
  reserved_by_me: boolean
}

interface BackendAppointment {
  id: number
  mentor_id: number
  teacher: string
  date_text: string
  date_iso: string
  time: string
  location: string
}

function formatDateISO(date: Date) {
  const y = date.getFullYear()
  const m = `${date.getMonth() + 1}`.padStart(2, '0')
  const d = `${date.getDate()}`.padStart(2, '0')
  return `${y}-${m}-${d}`
}

function mapSlot(item: BackendSlot): MentorSlot {
  return {
    slotId: item.slot_id,
    mentorId: item.mentor_id,
    teacher: item.teacher,
    dateText: item.date_text,
    dateIso: item.date_iso,
    time: item.time,
    location: item.location,
    intro: item.intro,
    avatar: item.avatar,
    booked: item.booked,
    reservedByMe: item.reserved_by_me,
  }
}

function mapAppointment(item: BackendAppointment): AppointmentRecord {
  return {
    id: item.id,
    mentorId: item.mentor_id,
    teacher: item.teacher,
    dateText: item.date_text,
    dateIso: item.date_iso,
    time: item.time,
    location: item.location,
  }
}

async function fetchSlots() {
  const dateIso = formatDateISO(selectedDate.value)
  const name = appliedSearchName.value.trim()
  const location = appliedSearchLocation.value.trim()
  const query = new URLSearchParams()
  if (!isSearchMode.value) {
    query.set('date_value', dateIso)
  }
  if (name) {
    query.set('name', name)
  }
  if (location) {
    query.set('location', location)
  }

  loadingSlots.value = true
  try {
    const data = await requestApi<BackendSlot[]>(`/api/mentor/slots?${query.toString()}`, { method: 'GET' }, true)
    slots.value = data.map(mapSlot)
  } catch (error) {
    const message = error instanceof Error ? error.message : '获取导师排班失败'
    showMessage('error', message)
  } finally {
    loadingSlots.value = false
  }
}

async function fetchMyAppointments() {
  const data = await requestApi<BackendAppointment[]>('/api/mentor/appointments/me', { method: 'GET' }, true)
  myAppointments.value = data.map(mapAppointment)
}

function debugLog(action: string, payload: Record<string, unknown> = {}) {
  const info = {
    action,
    account: currentUser.value?.account || null,
    timestamp: new Date().toISOString(),
    ...payload,
  }
  console.info('[MentorDebug]', JSON.stringify(info))
}

const selectedDateText = computed(() => {
  const date = selectedDate.value
  return `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日`
})

const monthTitle = computed(() => {
  const date = calendarCursor.value
  return `${date.getFullYear()}年 ${date.getMonth() + 1}月`
})

const filteredSlots = computed(() => slots.value)

const calendarDays = computed(() => {
  const first = new Date(calendarCursor.value.getFullYear(), calendarCursor.value.getMonth(), 1)
  const month = first.getMonth()
  const startDay = first.getDay()
  const cells: Array<{ date: Date; day: number; currentMonth: boolean }> = []

  const startDate = new Date(first)
  startDate.setDate(first.getDate() - startDay)

  for (let i = 0; i < 42; i += 1) {
    const cellDate = new Date(startDate)
    cellDate.setDate(startDate.getDate() + i)
    cells.push({
      date: cellDate,
      day: cellDate.getDate(),
      currentMonth: cellDate.getMonth() === month,
    })
  }
  return cells
})

function sameDate(left: Date, right: Date) {
  return (
    left.getFullYear() === right.getFullYear()
    && left.getMonth() === right.getMonth()
    && left.getDate() === right.getDate()
  )
}

function isSelected(date: Date) {
  return sameDate(date, selectedDate.value)
}

async function pickDate(date: Date) {
  selectedDate.value = new Date(date)
  isSearchMode.value = false
  debugLog('pick_date', { date: selectedDate.value.toDateString() })
  await fetchSlots()
}

function previousMonth() {
  calendarCursor.value = new Date(calendarCursor.value.getFullYear(), calendarCursor.value.getMonth() - 1, 1)
}

function nextMonth() {
  calendarCursor.value = new Date(calendarCursor.value.getFullYear(), calendarCursor.value.getMonth() + 1, 1)
}

async function reserveSlot(slot: MentorSlot) {
  debugLog('reserve_click', { slotId: slot.slotId, booked: slot.booked, reserved: slot.reservedByMe })
  try {
    await requestApi<BackendAppointment>(
      '/api/mentor/appointments',
      {
        method: 'POST',
        body: JSON.stringify({
          mentor_id: slot.mentorId,
          appointment_date: slot.dateIso,
          time_slot: slot.time,
        }),
      },
      true,
    )
    showMessage('success', '预约成功')
    await fetchSlots()
    if (showMyAppointments.value) {
      await fetchMyAppointments()
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : '预约失败'
    showMessage('error', message)
    debugLog('reserve_failed', { slotId: slot.slotId, message })
  }
}

async function applySearch() {
  const name = searchName.value.trim()
  const location = searchLocation.value.trim()
  if (!name && !location) {
    appliedSearchName.value = ''
    appliedSearchLocation.value = ''
    isSearchMode.value = false
    await fetchSlots()
    return
  }
  appliedSearchName.value = name
  appliedSearchLocation.value = location
  debugLog('search_apply', { name, location })
  isSearchMode.value = true
  try {
    await fetchSlots()
  } catch (error) {
    const message = error instanceof Error ? error.message : '搜索导师失败'
    showMessage('error', message)
  }
}

async function openMyAppointments() {
  try {
    await fetchMyAppointments()
    showMyAppointments.value = true
    debugLog('open_my_appointments', { count: myAppointments.value.length })
  } catch (error) {
    const message = error instanceof Error ? error.message : '加载预约记录失败'
    showMessage('error', message)
    debugLog('open_my_appointments_failed', { message })
  }
}

async function cancelAppointment(item: AppointmentRecord) {
  try {
    await requestApi<{ detail: string }>(`/api/mentor/appointments/${item.id}`, { method: 'DELETE' }, true)
    showMessage('success', '取消预约成功')
    await fetchMyAppointments()
    if (!isSearchMode.value) {
      await fetchSlots()
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : '取消预约失败'
    showMessage('error', message)
  }
}

onMounted(async () => {
  await fetchSlots()
})
</script>

<template>
  <section class="mentor-page reveal">
    <div class="top-row">
      <div class="left-top card-font">
        <h2>联系导师</h2>
        <div class="search-bar">
          <input v-model="searchName" placeholder="导师姓名" />
          <input v-model="searchLocation" placeholder="地点" />
          <button @click="applySearch">搜索</button>
        </div>
      </div>
      <button class="mine-btn card-font" @click="openMyAppointments">我的预约</button>
    </div>

    <div class="mentor-layout card-font">
      <article class="schedule-card glass">
        <div class="card-head">
          <h3>{{ isSearchMode ? '搜索结果' : '当日排班' }}</h3>
          <p>{{ isSearchMode ? '当前列表仅按搜索条件过滤（不受日期限制）' : selectedDateText }}</p>
        </div>
        <p v-if="loadingSlots" class="empty-tip">正在加载导师排班...</p>
        <div class="schedule-list">
          <article v-for="slot in filteredSlots" :key="slot.slotId" class="slot-item">
            <div class="slot-left">
              <h4>{{ slot.teacher }}</h4>
              <p>排班时间：{{ slot.dateText }} {{ slot.time }}</p>
              <p>地点：{{ slot.location }}</p>
              <p>导师介绍：{{ slot.intro }}</p>
              <p class="booked-line">预约人数：{{ slot.booked }}/5</p>
            </div>
            <div class="slot-right">
              <img :src="slot.avatar" :alt="slot.teacher" class="doctor-avatar" />
              <button class="reserve-btn" :disabled="slot.booked >= 5 || slot.reservedByMe" @click="reserveSlot(slot)">
                {{ slot.reservedByMe ? '已预约' : slot.booked >= 5 ? '已满额' : '预约' }}
              </button>
            </div>
          </article>
          <p v-if="!filteredSlots.length" class="empty-tip">暂无排班</p>
        </div>
      </article>

      <article class="calendar-card glass">
        <div class="calendar-head">
          <button class="month-btn" @click="previousMonth">◀</button>
          <strong>{{ monthTitle }}</strong>
          <button class="month-btn" @click="nextMonth">▶</button>
        </div>
        <div class="week-row">
          <span>日</span><span>一</span><span>二</span><span>三</span><span>四</span><span>五</span><span>六</span>
        </div>
        <div class="day-grid">
          <button
            v-for="cell in calendarDays"
            :key="cell.date.toISOString()"
            class="day-cell"
            :class="{ muted: !cell.currentMonth, active: isSelected(cell.date) }"
            @click="pickDate(cell.date)"
          >
            {{ cell.day }}
          </button>
        </div>
      </article>
    </div>

    <Teleport to="body">
      <div v-if="showMyAppointments" class="modal-mask" @click.self="showMyAppointments = false">
        <div class="modal-card glass card-font">
          <div class="modal-head">
            <h3>我的预约</h3>
            <button @click="showMyAppointments = false">关闭</button>
          </div>
          <div v-if="myAppointments.length" class="appointment-list">
            <article v-for="item in myAppointments" :key="item.id" class="appointment-item">
              <p>{{ item.teacher }}</p>
              <p>{{ item.dateText }} {{ item.time }}</p>
              <div class="appointment-bottom">
                <p>{{ item.location }}</p>
                <button class="cancel-btn" @click="cancelAppointment(item)">取消预约</button>
              </div>
            </article>
          </div>
          <p v-else class="empty-tip">暂无预约记录</p>
        </div>
      </div>
    </Teleport>
  </section>
</template>

<style scoped>
.mentor-page {
  border-radius: 28px;
  padding: 24px;
}

.card-font,
.card-font * {
  font-family: 'STKaiti', 'KaiTi', serif;
}

.top-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
}

.left-top {
  display: flex;
  align-items: center;
  gap: 16px;
}

.search-bar {
  display: flex;
  gap: 8px;
}

.search-bar input {
  border: 0;
  border-radius: 10px;
  padding: 9px 10px;
  background: rgba(255, 255, 255, 0.8);
}

.search-bar button {
  border: 0;
  border-radius: 999px;
  padding: 9px 14px;
  cursor: pointer;
  background: #f9cdd9;
  color: #8b4a5d;
}

.mine-btn {
  border: 0;
  border-radius: 999px;
  padding: 9px 14px;
  cursor: pointer;
  background: #f9cdd9;
  color: #8b4a5d;
}

.mentor-layout {
  margin-top: 14px;
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(0, 0.6fr);
  gap: 4px;
  align-items: start;
}

.glass {
  background: rgba(255, 255, 255, 0.52);
  border: 1px solid rgba(255, 255, 255, 0.7);
  box-shadow: 0 10px 30px rgba(55, 78, 120, 0.12);
  backdrop-filter: blur(14px);
}

.schedule-card,
.calendar-card {
  border-radius: 18px;
  padding: 16px;
}

.calendar-card {
  max-width: 340px;
  width: 100%;
  justify-self: end;
  align-self: start;
}

.card-head h3 {
  margin: 0;
  color: #2e4a74;
}

.card-head p {
  margin: 6px 0 0;
  color: #45638f;
}

.schedule-list {
  margin-top: 12px;
  display: grid;
  gap: 10px;
}

.slot-item {
  border-radius: 14px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.62);
  display: grid;
  grid-template-columns: 1fr 170px;
  gap: 12px;
  align-items: end;
}

.slot-left h4 {
  margin: 0;
  color: #2b4870;
}

.slot-left p {
  margin: 6px 0 0;
  color: #45638f;
}

.booked-line {
  margin-top: 10px;
}

.slot-right {
  display: grid;
  justify-items: center;
  align-content: end;
  gap: 8px;
}

.doctor-avatar {
  width: 120px;
  height: 120px;
  border-radius: 12px;
  object-fit: cover;
  border: 2px solid rgba(255, 255, 255, 0.86);
}

.reserve-btn {
  border: 0;
  border-radius: 999px;
  padding: 8px 14px;
  cursor: pointer;
  background: #f9cdd9;
  color: #8b4a5d;
}

.reserve-btn:disabled {
  cursor: not-allowed;
  opacity: 1;
  background: #f3dbe2;
  color: #b28a97;
}

.calendar-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.month-btn {
  border: 0;
  border-radius: 999px;
  width: 30px;
  height: 30px;
  background: rgba(255, 255, 255, 0.8);
  cursor: pointer;
}

.week-row,
.day-grid {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 6px;
}

.week-row {
  margin-bottom: 6px;
  text-align: center;
  color: #54739f;
}

.day-cell {
  border: 0;
  border-radius: 8px;
  width: 100%;
  aspect-ratio: 1 / 1;
  background: rgba(255, 255, 255, 0.72);
  cursor: pointer;
  color: #2f4f79;
}

.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(13, 22, 44, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 30;
}

.modal-card {
  width: min(92vw, 520px);
  border-radius: 16px;
  padding: 16px;
}

.modal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.modal-head h3 {
  margin: 0;
  color: #2e4a74;
}

.modal-head button {
  border: 0;
  border-radius: 999px;
  padding: 8px 12px;
  cursor: pointer;
}

.appointment-list {
  margin-top: 10px;
  display: grid;
  gap: 8px;
}

.appointment-item {
  border-radius: 10px;
  padding: 10px;
  background: rgba(255, 255, 255, 0.68);
}

.appointment-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.appointment-bottom p {
  margin: 4px 0;
}

.cancel-btn {
  border: 0;
  border-radius: 999px;
  padding: 6px 12px;
  cursor: pointer;
  background: #f6d7df;
  color: #8b4a5d;
}

.appointment-item p {
  margin: 4px 0;
}

.empty-tip {
  margin-top: 14px;
  color: #4d6c95;
}

.day-cell.muted {
  opacity: 0.45;
}

.day-cell.active {
  background: #f9cdd9;
  color: #8b4a5d;
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

@media (max-width: 1080px) {
  .left-top {
    flex-wrap: wrap;
  }

  .mentor-layout {
    grid-template-columns: 1fr;
  }

  .calendar-card {
    max-width: none;
    justify-self: stretch;
  }

  .search-bar {
    flex-wrap: wrap;
    justify-content: flex-start;
    margin-right: 0;
  }
}

@media (max-width: 760px) {
  .top-row {
    flex-direction: column;
    align-items: stretch;
  }

  .left-top {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }

  .search-bar {
    justify-content: stretch;
  }

  .slot-item {
    grid-template-columns: 1fr;
  }
}
</style>
