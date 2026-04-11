import { computed, reactive, ref } from 'vue'

export type NavKey = '首页' | '心理分析' | '心理百科' | '联系导师' | '放松一下' | '秘密树洞'

interface UserAuthRecord {
  account: string
  nickname: string
  password: string
  xhsUrl: string
  avatar: string
  email: string
  gender: string
  phone: string
  signature: string
}

interface CurrentUser {
  account: string
  nickname: string
  avatar: string
}

interface EncyclopediaItem {
  title: string
  emoji: string
  intro: string
  tips: string[]
}

interface MentorItem {
  name: string
  focus: string
  style: string
}

interface TreePost {
  id: number
  from: 'user' | 'ai'
  text: string
}

interface ToastMessage {
  id: number
  type: 'success' | 'error'
  text: string
}

const navItems: NavKey[] = ['首页', '心理分析', '心理百科', '联系导师', '放松一下', '秘密树洞']

const routeMap: Record<NavKey, string> = {
  首页: '/',
  心理分析: '/analysis',
  心理百科: '/encyclopedia',
  联系导师: '/mentor',
  放松一下: '/relax',
  秘密树洞: '/tree-hole',
}

const isAuthOpen = ref(false)
const authMode = ref<'login' | 'register'>('login')
const currentUser = ref<CurrentUser | null>(null)
const userStore = reactive<Record<string, UserAuthRecord>>({})

userStore['test001'] = {
  account: 'test001',
  nickname: '测试用户',
  password: '123456',
  xhsUrl: '',
  avatar: '',
  email: '',
  gender: '',
  phone: '',
  signature: '今天也要对自己温柔一点。',
}

const loginForm = reactive({
  account: '',
  password: '',
  captchaInput: '',
})

const registerForm = reactive({
  account: '',
  nickname: '',
  password: '',
  xhsUrl: '',
})

const profileForm = reactive({
  avatar: '',
  nickname: '',
  email: '',
  gender: '',
  phone: '',
  signature: '',
  xhsUrl: '',
})

const captchaQuestion = ref('')
const captchaAnswer = ref('')

const authMessage = ref('')
const messageQueue = ref<ToastMessage[]>([])

const analysisOpen = ref(false)
const analyzing = ref(false)
const analysisProgress = ref(0)
const analysisAdvice = ref('')
let analysisTimer: number | null = null

const encyclopediaItems: EncyclopediaItem[] = [
  {
    title: '抑郁情绪',
    emoji: '🌤️',
    intro: '长期低落、兴趣减退并不等于“矫情”，它可能是心灵在求助。',
    tips: ['每日固定起床与散步节律', '把任务拆成5分钟小目标', '主动联系一位可信任的人'],
  },
  {
    title: '焦虑紧张',
    emoji: '🍃',
    intro: '担忧未来、身体紧绷是焦虑常见表现，可通过训练逐步降低强度。',
    tips: ['执行4-7-8呼吸法', '写下可控与不可控事项', '减少晚间信息过载'],
  },
  {
    title: '睡眠困扰',
    emoji: '🌙',
    intro: '睡不着并非意志力问题，常与压力、作息和环境刺激相关。',
    tips: ['固定睡前仪式30分钟', '下午后减少咖啡因', '卧室只保留睡眠相关活动'],
  },
  {
    title: '内耗反刍',
    emoji: '🧩',
    intro: '反复自责与过度复盘会消耗心理能量，需要把注意力拉回当下。',
    tips: ['给担忧设置15分钟时段', '记录已完成而非未完成', '用身体活动打断反刍循环'],
  },
]

const mentors: MentorItem[] = [
  { name: '林溪导师', focus: '情绪陪伴', style: '温和倾听，擅长焦虑减压与日常支持' },
  { name: '顾南导师', focus: '关系沟通', style: '聚焦亲密关系与家庭冲突修复' },
  { name: '程乔导师', focus: '成长规划', style: '帮助重建自信与学习职业节奏' },
]

const treeInput = ref('')
const treePosts = ref<TreePost[]>([
  {
    id: 1,
    from: 'ai',
    text: '欢迎来到秘密树洞，你可以匿名说出心事，我会认真听你说。',
  },
])

const aiReplies = [
  '谢谢你愿意说出来，你已经很勇敢了。先慢慢呼吸，我们一起把今天过好。',
  '你的感受是被允许的，不需要马上变好。给自己一点时间，你并不孤单。',
  '此刻的你已经在努力了，试着喝一口温水，给身体一个放松信号。',
]

function resetAuthForm() {
  loginForm.account = ''
  loginForm.password = ''
  loginForm.captchaInput = ''
  registerForm.account = ''
  registerForm.nickname = ''
  registerForm.password = ''
  registerForm.xhsUrl = ''
}

function refreshCaptcha() {
  const left = Math.floor(Math.random() * 8) + 1
  const right = Math.floor(Math.random() * 8) + 1
  captchaQuestion.value = `${left} + ${right} = ?`
  captchaAnswer.value = String(left + right)
  loginForm.captchaInput = ''
}

function showMessage(type: 'success' | 'error', text: string) {
  const id = Date.now() + Math.floor(Math.random() * 1000)
  console.info('[MessageDebug]', JSON.stringify({ type, text, id, timestamp: new Date().toISOString() }))
  messageQueue.value.push({ id, type, text })
  window.setTimeout(() => {
    messageQueue.value = messageQueue.value.filter((item) => item.id !== id)
  }, 2200)
}

function fillProfileFromAccount(record: UserAuthRecord) {
  profileForm.avatar = record.avatar
  profileForm.nickname = record.nickname
  profileForm.email = record.email
  profileForm.gender = record.gender
  profileForm.phone = record.phone
  profileForm.signature = record.signature
  profileForm.xhsUrl = record.xhsUrl
}

function syncProfileFromCurrentUser() {
  const account = currentUser.value?.account
  if (!account) {
    return
  }
  const record = userStore[account]
  if (!record) {
    return
  }
  fillProfileFromAccount(record)
}

function openAuth() {
  authMode.value = 'login'
  authMessage.value = ''
  refreshCaptcha()
  isAuthOpen.value = true
}

function closeAuth() {
  isAuthOpen.value = false
}

function submitLogin() {
  const account = loginForm.account.trim()
  const password = loginForm.password.trim()
  const captchaInput = loginForm.captchaInput.trim()
  if (!account || !password || !captchaInput) {
    authMessage.value = '请输入账号、密码和验证码。'
    showMessage('error', authMessage.value)
    return false
  }
  if (captchaInput !== captchaAnswer.value) {
    authMessage.value = '验证码错误，请重试。'
    showMessage('error', authMessage.value)
    refreshCaptcha()
    return false
  }
  const saved = userStore[account]
  if (!saved || saved.password !== password) {
    authMessage.value = '账号不存在或密码错误。'
    showMessage('error', authMessage.value)
    refreshCaptcha()
    return false
  }
  currentUser.value = {
    account,
    nickname: saved.nickname,
    avatar: saved.avatar,
  }
  fillProfileFromAccount(saved)
  authMessage.value = '登录成功，欢迎回来。'
  showMessage('success', '登录成功')
  window.setTimeout(() => {
    isAuthOpen.value = false
    authMessage.value = ''
    resetAuthForm()
  }, 500)
  return true
}

function submitRegister() {
  const account = registerForm.account.trim()
  const nickname = registerForm.nickname.trim()
  const password = registerForm.password.trim()
  const xhsUrl = registerForm.xhsUrl.trim()
  if (!account || !nickname || !password) {
    authMessage.value = '账号、密码和昵称为必填项。'
    showMessage('error', authMessage.value)
    return false
  }
  if (userStore[account]) {
    authMessage.value = '该账号已存在，请更换。'
    showMessage('error', authMessage.value)
    return false
  }
  userStore[account] = {
    account,
    nickname,
    password,
    xhsUrl,
    avatar: '',
    email: '',
    gender: '',
    phone: '',
    signature: '',
  }
  authMessage.value = '注册成功，请登录。'
  showMessage('success', '注册成功')
  authMode.value = 'login'
  loginForm.account = account
  loginForm.password = ''
  refreshCaptcha()
  return true
}

function logout() {
  currentUser.value = null
  authMessage.value = ''
}

function updateProfile() {
  const account = currentUser.value?.account
  if (!account) {
    return
  }
  const record = userStore[account]
  if (!record) {
    return
  }
  record.nickname = profileForm.nickname.trim() || record.nickname
  record.avatar = profileForm.avatar.trim()
  record.email = profileForm.email.trim()
  record.gender = profileForm.gender.trim()
  record.phone = profileForm.phone.trim()
  record.signature = profileForm.signature.trim()
  record.xhsUrl = profileForm.xhsUrl.trim()

  currentUser.value = {
    account,
    nickname: record.nickname,
    avatar: record.avatar,
  }
}

function uploadAvatar(dataUrl: string) {
  profileForm.avatar = dataUrl
}

const analysisTitle = computed(() => {
  const name = currentUser.value?.nickname || '访客'
  return `${name} 的心理画像`
})

function buildAdvice() {
  const traits = ['感受细腻', '恢复力良好', '同理心强', '自省能力突出']
  const focuses = ['睡眠节律', '压力释放', '边界表达', '自我肯定']
  const name = currentUser.value?.nickname || '访客'
  const seed = Array.from(name).reduce((sum, char) => sum + char.charCodeAt(0), 0)
  const trait = traits[seed % traits.length]
  const focus = focuses[(seed + 1) % focuses.length]
  analysisAdvice.value = `你的近期状态呈现“${trait}”特征，建议优先关注${focus}。每天留出15分钟给自己，做呼吸训练或轻运动，你会更稳地找回内在节奏。`
}

function startAnalysis() {
  analysisOpen.value = true
  analyzing.value = true
  analysisProgress.value = 0
  analysisAdvice.value = ''
  if (analysisTimer) {
    window.clearInterval(analysisTimer)
  }
  analysisTimer = window.setInterval(() => {
    analysisProgress.value += 10
    if (analysisProgress.value >= 100) {
      if (analysisTimer) {
        window.clearInterval(analysisTimer)
        analysisTimer = null
      }
      analyzing.value = false
      buildAdvice()
    }
  }, 180)
}

function closeAnalysis() {
  analysisOpen.value = false
  if (analysisTimer) {
    window.clearInterval(analysisTimer)
    analysisTimer = null
  }
}

function submitTreePost() {
  const content = treeInput.value.trim()
  if (!content) {
    return
  }
  treePosts.value.push({ id: Date.now(), from: 'user', text: content })
  treeInput.value = ''
  const reply = aiReplies[Math.floor(Math.random() * aiReplies.length)] || aiReplies[0] || '抱抱你。'
  window.setTimeout(() => {
    treePosts.value.push({ id: Date.now() + 1, from: 'ai', text: reply })
  }, 500)
}

function stopAllTimers() {
  if (analysisTimer) {
    window.clearInterval(analysisTimer)
    analysisTimer = null
  }
}

export function useMindIsland() {
  return {
    navItems,
    routeMap,
    isAuthOpen,
    authMode,
    currentUser,
    loginForm,
    registerForm,
    profileForm,
    captchaQuestion,
    authMessage,
    messageQueue,
    analysisOpen,
    analyzing,
    analysisProgress,
    analysisAdvice,
    analysisTitle,
    encyclopediaItems,
    mentors,
    treeInput,
    treePosts,
    openAuth,
    closeAuth,
    refreshCaptcha,
    showMessage,
    submitLogin,
    submitRegister,
    uploadAvatar,
    updateProfile,
    syncProfileFromCurrentUser,
    logout,
    startAnalysis,
    closeAnalysis,
    submitTreePost,
    stopAllTimers,
  }
}
