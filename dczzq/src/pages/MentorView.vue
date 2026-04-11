<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useMindIsland } from '../composables/useMindIsland'

interface MentorSlot {
  id: string
  teacher: string
  dateText: string
  time: string
  location: string
  intro: string
  avatar: string
  booked: number
}

interface AppointmentRecord {
  id: string
  teacher: string
  dateText: string
  time: string
  location: string
}

const selectedDate = ref(new Date())
const calendarCursor = ref(new Date(selectedDate.value.getFullYear(), selectedDate.value.getMonth(), 1))

const searchName = ref('')
const searchLocation = ref('')
const appliedSearchName = ref('')
const appliedSearchLocation = ref('')
const showMyAppointments = ref(false)

const fixedTimes = ['8:00-9:30', '10:00-11:30', '14:00-15:30', '16:00-17:30']
const avatars = ['/assets/doctor1.png', '/assets/doctor2.png', '/assets/doctor3.png', '/assets/doctor4.png']
const teacherPool = [
  { name: '林溪导师', intro: '温和倾听，擅长焦虑减压与情绪稳定。' },
  { name: '顾南导师', intro: '聚焦关系沟通与家庭冲突修复。' },
  { name: '程乔导师', intro: '帮助成长规划与学习节奏重建。' },
  { name: '沈禾导师', intro: '善于压力管理与自我接纳训练。' },
  { name: '白言导师', intro: '关注青少年支持与考试焦虑辅导。' },
  { name: '周棠导师', intro: '擅长睡眠困扰和日常作息调节。' },
]
const locationPool = ['A302 咨询室', 'B105 心理室', 'C201 安静室', '线上视频室', 'D101 团辅室']
const bookedStore = reactive<Record<string, number>>({})
const reservedStore = reactive<Record<string, boolean>>({})
const myAppointments = ref<AppointmentRecord[]>([])

const { currentUser, showMessage } = useMindIsland()

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

const daySlots = computed<MentorSlot[]>(() => {
  const date = selectedDate.value
  const dateText = `${date.getMonth() + 1}月${date.getDate()}日`
  const daySeed = date.getFullYear() * 10000 + (date.getMonth() + 1) * 100 + date.getDate()

  return fixedTimes.map((time, index) => {
    const teacher = teacherPool[(daySeed + index) % teacherPool.length] || teacherPool[0] || { name: '导师', intro: '' }
    const location = locationPool[(daySeed + index * 2) % locationPool.length] || locationPool[0] || 'A302 咨询室'
    const avatar = avatars[index] || '/assets/doctor1.png'
    const id = `${date.toDateString()}-${teacher.name}-${time}`
    if (bookedStore[id] === undefined) {
      bookedStore[id] = ((daySeed + index * 3) % 4) + 1
    }
    return {
      id,
      teacher: teacher.name,
      dateText,
      time,
      location,
      intro: teacher.intro,
      avatar,
      booked: bookedStore[id] ?? 1,
    }
  })
})

const filteredSlots = computed(() => {
  const nameKeyword = appliedSearchName.value.trim()
  const locationKeyword = appliedSearchLocation.value.trim()
  return daySlots.value.filter((slot) => {
    const passName = !nameKeyword || slot.teacher.includes(nameKeyword)
    const passLocation = !locationKeyword || slot.location.includes(locationKeyword)
    return passName && passLocation
  })
})

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

function pickDate(date: Date) {
  selectedDate.value = new Date(date)
  appliedSearchName.value = ''
  appliedSearchLocation.value = ''
  searchName.value = ''
  searchLocation.value = ''
  debugLog('pick_date', { date: selectedDate.value.toDateString() })
}

function previousMonth() {
  calendarCursor.value = new Date(calendarCursor.value.getFullYear(), calendarCursor.value.getMonth() - 1, 1)
}

function nextMonth() {
  calendarCursor.value = new Date(calendarCursor.value.getFullYear(), calendarCursor.value.getMonth() + 1, 1)
}

function reserveSlot(slot: MentorSlot) {
  debugLog('reserve_click', { slotId: slot.id, booked: slot.booked, reserved: !!reservedStore[slot.id] })
  if (!currentUser.value) {
    showMessage('error', '请先登录再预约导师')
    debugLog('reserve_blocked_not_login', { slotId: slot.id })
    return
  }
  if (reservedStore[slot.id]) {
    debugLog('reserve_blocked_already_reserved', { slotId: slot.id })
    return
  }
  const current = bookedStore[slot.id] ?? slot.booked
  bookedStore[slot.id] = Math.min(5, current + 1)
  reservedStore[slot.id] = true
  if (!myAppointments.value.some((record) => record.id === slot.id)) {
    myAppointments.value.unshift({
      id: slot.id,
      teacher: slot.teacher,
      dateText: slot.dateText,
      time: slot.time,
      location: slot.location,
    })
  }
  showMessage('success', '预约成功')
  debugLog('reserve_success', { slotId: slot.id, newBooked: bookedStore[slot.id] })
}

function applySearch() {
  const name = searchName.value.trim()
  const location = searchLocation.value.trim()
  if (!name && !location) {
    appliedSearchName.value = ''
    appliedSearchLocation.value = ''
    return
  }
  appliedSearchName.value = name
  appliedSearchLocation.value = location
  debugLog('search_apply', { name, location })
}

function openMyAppointments() {
  if (!currentUser.value) {
    showMessage('error', '请先登录再查看我的预约')
    debugLog('open_my_appointments_blocked_not_login')
    return
  }
  showMyAppointments.value = true
  debugLog('open_my_appointments', { count: myAppointments.value.length })
}
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
          <h3>当日排班</h3>
          <p>{{ selectedDateText }}</p>
        </div>
        <div class="schedule-list">
          <article v-for="slot in filteredSlots" :key="slot.id" class="slot-item">
            <div class="slot-left">
              <h4>{{ slot.teacher }}</h4>
              <p>排班时间：{{ slot.dateText }} {{ slot.time }}</p>
              <p>地点：{{ slot.location }}</p>
              <p>导师介绍：{{ slot.intro }}</p>
              <p class="booked-line">预约人数：{{ slot.booked }}/5</p>
            </div>
            <div class="slot-right">
              <img :src="slot.avatar" :alt="slot.teacher" class="doctor-avatar" />
              <button class="reserve-btn" :disabled="slot.booked >= 5 || reservedStore[slot.id]" @click="reserveSlot(slot)">
                {{ reservedStore[slot.id] ? '已预约' : slot.booked >= 5 ? '已满额' : '预约' }}
              </button>
            </div>
          </article>
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
              <p>{{ item.location }}</p>
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
