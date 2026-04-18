import { computed, reactive, ref } from 'vue'

export type NavKey = '首页' | '心理分析' | '心理百科' | '联系导师' | '放松一下' | '秘密树洞'

interface CurrentUser {
  id?: number
  account: string
  nickname: string
  avatar: string
}

interface BackendUser {
  id: number
  account: string
  nickname: string
  avatar: string | null
  xhs_url: string | null
  email: string | null
  gender: string | null
  phone: string | null
  signature: string | null
}

interface AuthResponse {
  access_token: string
  token_type: string
  user: BackendUser
}

interface AnalysisResponse {
  user_id: number
  post_count: number
  health_score: number
  prediction: {
    pred_label: number
    pred_name: string
    prob_non_clinical: number
    prob_clinical: number
  }
  source: string
}

export type EncyclopediaCategory = '情绪压力' | '行为习惯' | '自我成长';
interface EncyclopediaItem {
  title: string;
  emoji: string;
  intro: string;
  tips: string[];
  category: EncyclopediaCategory;
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

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim() || 'http://127.0.0.1:8000'
const TOKEN_KEY = 'mind_island_token'
const USER_KEY = 'mind_island_user'

function readStorage(key: string): string {
  if (typeof window === 'undefined') {
    return ''
  }
  return window.localStorage.getItem(key) || ''
}

function readStoredUser(): CurrentUser | null {
  const raw = readStorage(USER_KEY)
  if (!raw) {
    return null
  }
  try {
    const parsed = JSON.parse(raw) as CurrentUser
    if (!parsed.account) {
      return null
    }
    return parsed
  } catch {
    return null
  }
}

const accessToken = ref(readStorage(TOKEN_KEY))
const currentUser = ref<CurrentUser | null>(readStoredUser())
const currentUserId = ref<number | null>(currentUser.value?.id ?? null)

const loginForm = reactive({
  account: '',
  password: '',
  captchaInput: '',
})

const registerForm = reactive({
  account: '',
  nickname: '',
  password: '',
  confirmPassword: '',
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
const analysisScore = ref<number | null>(null)
const analysisRiskLabel = ref('')
let analysisTimer: number | null = null
let demoCarouselTimer: number | null = null

const analysisDemoMode = ref(false)
const analysisDemoImages = [
  '/show_example/68baacff000000001d014377_1.jpg',
  '/show_example/68d3f984000000001203dc25_1.jpg',
  '/show_example/68f2109f00000000070340e7_1.jpg',
  '/show_example/695620b2000000001e02754a_1.jpg',
  '/show_example/6958d726000000001f009eb2_1.jpg',
  '/show_example/69749875000000000b0111b8_1.jpg',
  '/show_example/69aeeabc000000002602ef1d_1.jpg',
  '/show_example/69b2231b000000002202f34c_1.jpg',
  '/show_example/69ba8ac6000000001b003151_1.jpg',
  '/show_example/69ba8d76000000001d01bff6_1.jpg',
  '/show_example/69be9a96000000001a02cb2a_1.jpg',
  '/show_example/69df5a4c0000000023011bcf_1.jpg',
]
const analysisDemoImageIndex = ref(0)
const analysisDemoWordcloudVisible = ref(false)
const analysisDemoResultVisible = ref(false)

const encyclopediaItems: EncyclopediaItem[] = [
  // 情绪压力
  { title: '抑郁情绪', emoji: '🌤️', intro: '长期低落、兴趣减退并不等于“矫情”，它可能是心灵在求助。', tips: ['每日固定起床与散步节律', '把任务拆成5分钟小目标', '主动联系一位可信任的人'], category: '情绪压力' },
  { title: '焦虑紧张', emoji: '🍃', intro: '担忧未来、身体紧绷是焦虑常见表现，可通过训练逐步降低强度。', tips: ['执行4-7-8呼吸法', '写下可控与不可控事项', '减少晚间信息过载'], category: '情绪压力' },
  { title: '社交压力', emoji: '🤝', intro: '在人际互动中感到紧张和被评价，是校园阶段常见的心理负担。', tips: ['先从低压力场景开始沟通', '练习表达边界与拒绝', '用事实替代自我否定想法'], category: '情绪压力' },
  { title: '情绪失控', emoji: '🌊', intro: '情绪突然上涌并不代表你脆弱，往往是长期压力累积后的信号。', tips: ['先暂停争执再做回应', '用呼吸和冷水降低唤醒', '事后记录触发点与身体反应'], category: '情绪压力' },
  // 行为习惯
  { title: '睡眠困扰', emoji: '🌙', intro: '睡不着并非意志力问题，常与压力、作息和环境刺激相关。', tips: ['固定睡前仪式30分钟', '下午后减少咖啡因', '卧室只保留睡眠相关活动'], category: '行为习惯' },
  { title: '内耗反刍', emoji: '🧩', intro: '反复自责与过度复盘会消耗心理能量，需要把注意力拉回当下。', tips: ['给担忧设置15分钟时段', '记录已完成而非未完成', '用身体活动打断反刍循环'], category: '行为习惯' },
  { title: '拖延行为', emoji: '⏳', intro: '拖延常和焦虑与完美主义相伴，不是懒惰，而是回避不适感。', tips: ['任务拆解为10分钟起步', '先做最小可完成动作', '完成后立刻给自己小奖励'], category: '行为习惯' },
  { title: '考试焦虑', emoji: '📝', intro: '备考期紧张是正常反应，关键在于把焦虑转化为可执行的行动。', tips: ['制定周计划与复盘节点', '模拟考试训练时间感', '考前避免通宵和信息过载'], category: '行为习惯' },
  // 自我成长
  { title: '自我否定', emoji: '🪞', intro: '长期否定自己会压低自我效能感，需要重建更真实的自我评价。', tips: ['每天记录三件做成的小事', '区分结果差与人不好', '用成长型语言替代标签化语言'], category: '自我成长' },
  { title: '关系边界', emoji: '🧱', intro: '健康关系需要边界，边界不是冷漠，而是保护彼此与关系质量。', tips: ['明确可接受与不可接受行为', '先说感受再说需求', '重复表达并保持一致性'], category: '自我成长' },
  { title: '习得无助', emoji: '🕯️', intro: '多次失败后容易产生无力感，可通过小胜利逐步恢复掌控感。', tips: ['选择可控目标先行动', '缩短反馈周期提升信心', '把失败改写为策略调整'], category: '自我成长' },
  { title: '职业迷茫', emoji: '🧭', intro: '对未来方向感到迷茫很常见，探索过程本身就是成长的一部分。', tips: ['先做兴趣与能力盘点', '通过实习访谈收集信息', '用季度目标替代一次性定终局'], category: '自我成长' },
];

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
  registerForm.confirmPassword = ''
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

function saveSession(token: string, user: CurrentUser) {
  accessToken.value = token
  currentUser.value = user
  currentUserId.value = user.id ?? null
  if (typeof window !== 'undefined') {
    window.localStorage.setItem(TOKEN_KEY, token)
    window.localStorage.setItem(USER_KEY, JSON.stringify(user))
  }
}

function clearSession() {
  accessToken.value = ''
  currentUser.value = null
  currentUserId.value = null
  if (typeof window !== 'undefined') {
    window.localStorage.removeItem(TOKEN_KEY)
    window.localStorage.removeItem(USER_KEY)
  }
}

function applyBackendUser(user: BackendUser) {
  currentUser.value = {
    id: user.id,
    account: user.account,
    nickname: user.nickname,
    avatar: user.avatar || '',
  }
  currentUserId.value = user.id
  profileForm.avatar = user.avatar || ''
  profileForm.nickname = user.nickname || ''
  profileForm.email = user.email || ''
  profileForm.gender = user.gender || ''
  profileForm.phone = user.phone || ''
  profileForm.signature = user.signature || ''
  profileForm.xhsUrl = user.xhs_url || ''

  if (typeof window !== 'undefined' && currentUser.value) {
    window.localStorage.setItem(USER_KEY, JSON.stringify(currentUser.value))
  }
}

async function requestApi<T>(path: string, init?: RequestInit, withAuth = false): Promise<T> {
  const headers = new Headers(init?.headers || {})
  if (!headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }
  if (withAuth && accessToken.value) {
    headers.set('Authorization', `Bearer ${accessToken.value}`)
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

async function syncProfileFromCurrentUser() {
  if (!accessToken.value) {
    return
  }

  try {
    const user = await requestApi<BackendUser>('/api/profile/me', { method: 'GET' }, true)
    applyBackendUser(user)
  } catch (error) {
    const message = error instanceof Error ? error.message : '获取个人资料失败'
    if (message.includes('401') || message.includes('credentials')) {
      clearSession()
    }
    console.info('[AuthDebug]', JSON.stringify({ action: 'sync_profile_failed', message }))
  }
}

void syncProfileFromCurrentUser()

function openAuth() {
  authMode.value = 'login'
  authMessage.value = ''
  refreshCaptcha()
  isAuthOpen.value = true
}

function closeAuth() {
  isAuthOpen.value = false
}

async function submitLogin() {
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

  try {
    const result = await requestApi<AuthResponse>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ account, password }),
    })

    saveSession(result.access_token, {
      id: result.user.id,
      account: result.user.account,
      nickname: result.user.nickname,
      avatar: result.user.avatar || '',
    })
    applyBackendUser(result.user)

    authMessage.value = '登录成功，欢迎回来。'
    showMessage('success', '登录成功')
    window.setTimeout(() => {
      isAuthOpen.value = false
      authMessage.value = ''
      resetAuthForm()
    }, 300)
    return true
  } catch (error) {
    const message = error instanceof Error ? error.message : '登录失败'
    authMessage.value = message
    showMessage('error', message)
    refreshCaptcha()
    return
  }
  return false
}

async function submitRegister() {
  const account = registerForm.account.trim()
  const nickname = registerForm.nickname.trim()
  const password = registerForm.password.trim()
  const confirmPassword = registerForm.confirmPassword.trim()
  const xhsUrl = registerForm.xhsUrl.trim()
  if (!account || !nickname || !password) {
    authMessage.value = '账号、密码和昵称为必填项。'
    showMessage('error', authMessage.value)
    return false
  }
  if (password.length < 6 || !/[A-Za-z]/.test(password) || !/\d/.test(password)) {
    authMessage.value = '密码需至少6位，且必须包含字母和数字。'
    showMessage('error', authMessage.value)
    return false
  }
  if (password !== confirmPassword) {
    authMessage.value = '两次输入的密码不一致。'
    showMessage('error', authMessage.value)
    return false
  }
  try {
    const result = await requestApi<AuthResponse>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ account, nickname, password, xhs_url: xhsUrl || null }),
    })

    saveSession(result.access_token, {
      id: result.user.id,
      account: result.user.account,
      nickname: result.user.nickname,
      avatar: result.user.avatar || '',
    })
    applyBackendUser(result.user)

    authMessage.value = '注册成功，已自动登录。'
    showMessage('success', '注册成功')
    window.setTimeout(() => {
      isAuthOpen.value = false
      authMessage.value = ''
      resetAuthForm()
    }, 300)
    return true
  } catch (error) {
    const message = error instanceof Error ? error.message : '注册失败'
    authMessage.value = message
    showMessage('error', message)
    return false
  }
}

function logout() {
  clearSession()
  authMessage.value = ''
}

async function updateProfile() {
  if (!accessToken.value) {
    showMessage('error', '请先登录')
    return false
  }

  try {
    const user = await requestApi<BackendUser>(
      '/api/profile/me',
      {
        method: 'PUT',
        body: JSON.stringify({
          nickname: profileForm.nickname.trim() || null,
          avatar: profileForm.avatar.trim() || null,
          xhs_url: profileForm.xhsUrl.trim() || null,
          email: profileForm.email.trim() || null,
          gender: profileForm.gender.trim() || null,
          phone: profileForm.phone.trim() || null,
          signature: profileForm.signature.trim() || null,
        }),
      },
      true,
    )

    applyBackendUser(user)
    showMessage('success', '资料已保存')
    return true
  } catch (error) {
    const message = error instanceof Error ? error.message : '保存失败'
    showMessage('error', message)
    return false
  }
}

function uploadAvatar(dataUrl: string) {
  profileForm.avatar = dataUrl
}

const analysisTitle = computed(() => {
  const name = currentUser.value?.nickname || '访客'
  return `${name} 的心理画像`
})

function getScoreBandFeedback(score: number) {
  const safe = Math.max(0, Math.min(100, Math.round(score)))
  const band = Math.min(9, Math.floor(safe / 10))
  const messages = [
    '当前状态有点脆弱，建议你先暂停高压任务，可以联系专业心理咨询师或导师进行一对一支持。',
    '你正在承受较高心理负荷，请优先保证睡眠与进食，并尽快寻求线下专业帮助。',
    '近期情绪风险偏高，建议减少自我苛责，和可信任的人建立每日一次稳定沟通。',
    '你的身心都在吃力运转，建议把目标缩小到今天可完成的三件小事，并安排放松时段。',
    '目前状态有明显波动，建议建立规律作息，同时尝试呼吸训练和轻运动来缓冲压力。',
    '整体处于中等水平，建议继续记录情绪触发点，逐步优化学习或工作的节奏。',
    '状态正在向稳态靠近，建议保持社交连接和运动习惯，巩固当前恢复趋势。',
    '你的心理韧性表现不错，继续维持规律生活，并给自己留出主动放松时间。',
    '当前状态较好，建议延续有效习惯，同时定期复盘情绪与压力来源。',
    '心理健康分很高，说明你有较强自我调节能力，继续保持并关注长期平衡。',
  ]
  return messages[band]
}

function buildAdvice() {
  if (analysisScore.value === null) {
    analysisAdvice.value = '暂无分析结果。'
    return
  }
  const scoreFeedback = getScoreBandFeedback(analysisScore.value)
  const riskText = analysisRiskLabel.value === 'Clinical' ? '模型提示存在风险倾向。' : '模型提示整体偏稳。'
  analysisAdvice.value = `当前心理健康分为 ${analysisScore.value} 分，${riskText}${scoreFeedback}`
}

function runFakeProgress(durationMs: number) {
  return new Promise<void>((resolve) => {
    const start = Date.now()
    if (analysisTimer) {
      window.clearInterval(analysisTimer)
      analysisTimer = null
    }
    analysisTimer = window.setInterval(() => {
      const elapsed = Date.now() - start
      const next = Math.min(100, Math.round((elapsed / durationMs) * 100))
      analysisProgress.value = next
      if (next >= 100) {
        if (analysisTimer) {
          window.clearInterval(analysisTimer)
          analysisTimer = null
        }
        resolve()
      }
    }, 80)
  })
}

function runDemoCarousel(durationMs: number) {
  return new Promise<void>((resolve) => {
    if (demoCarouselTimer) {
      window.clearInterval(demoCarouselTimer)
      demoCarouselTimer = null
    }
    analysisDemoImageIndex.value = 0
    const total = analysisDemoImages.length
    if (!total) {
      resolve()
      return
    }

    const perStep = Math.max(180, Math.floor(durationMs / total))
    let step = 0
    demoCarouselTimer = window.setInterval(() => {
      step += 1
      analysisDemoImageIndex.value = step % total
      if (step >= total) {
        if (demoCarouselTimer) {
          window.clearInterval(demoCarouselTimer)
          demoCarouselTimer = null
        }
        resolve()
      }
    }, perStep)
  })
}

function showAnalysisWordcloud() {
  analysisDemoWordcloudVisible.value = true
  analysisDemoResultVisible.value = false
}

function showAnalysisResult() {
  analysisDemoWordcloudVisible.value = false
  analysisDemoResultVisible.value = true
}

async function exportAnalysisReportPdf() {
  if (typeof window === 'undefined') {
    return
  }
  if (analyzing.value) {
    showMessage('error', '分析尚未完成，请稍后导出')
    return
  }

  const target = window.document.getElementById('analysis-report-export')
  if (!target) {
    showMessage('error', '未找到可导出的报告区域')
    return
  }

  try {
    const html2canvas = (await import('html2canvas')).default
    const { jsPDF } = await import('jspdf')

    const canvas = await html2canvas(target, {
      scale: 2,
      useCORS: true,
      backgroundColor: '#ffffff',
      windowWidth: target.scrollWidth,
      windowHeight: target.scrollHeight,
    })

    const imageData = canvas.toDataURL('image/png')
    const pdf = new jsPDF('p', 'mm', 'a4')

    const pageWidth = pdf.internal.pageSize.getWidth()
    const pageHeight = pdf.internal.pageSize.getHeight()
    const margin = 10
    const imageWidth = pageWidth - margin * 2
    const imageHeight = (canvas.height * imageWidth) / canvas.width

    let heightLeft = imageHeight
    let position = margin

    pdf.addImage(imageData, 'PNG', margin, position, imageWidth, imageHeight)
    heightLeft -= pageHeight - margin * 2

    while (heightLeft > 0) {
      pdf.addPage()
      position = margin - (imageHeight - heightLeft)
      pdf.addImage(imageData, 'PNG', margin, position, imageWidth, imageHeight)
      heightLeft -= pageHeight - margin * 2
    }

    const date = new Date().toISOString().slice(0, 10)
    pdf.save(`心理健康分析报告_${date}.pdf`)
    showMessage('success', 'PDF导出成功')
  } catch (error) {
    const message = error instanceof Error ? error.message : 'PDF导出失败'
    showMessage('error', message)
  }
}

async function startAnalysis() {
  if (!accessToken.value) {
    showMessage('error', '请先登录后再进行心理分析')
    return
  }
  analysisOpen.value = true
  analyzing.value = true
  analysisProgress.value = 0
  analysisAdvice.value = ''
  analysisScore.value = null
  analysisRiskLabel.value = ''
  analysisDemoMode.value = currentUserId.value === 4
  analysisDemoImageIndex.value = 0
  analysisDemoWordcloudVisible.value = false
  analysisDemoResultVisible.value = false

  try {
    const jobs: Array<Promise<unknown>> = [
      requestApi<AnalysisResponse>('/api/analysis/run', { method: 'POST' }, true),
      runFakeProgress(3000),
    ]
    if (analysisDemoMode.value) {
      jobs.push(runDemoCarousel(3000))
    }

    const [result] = (await Promise.all(jobs)) as [AnalysisResponse, unknown?, unknown?]
    analysisScore.value = result.health_score
    analysisRiskLabel.value = result.prediction.pred_name
    buildAdvice()
    analyzing.value = false
  } catch (error) {
    if (analysisTimer) {
      window.clearInterval(analysisTimer)
      analysisTimer = null
    }
    analysisProgress.value = 100
    analyzing.value = false
    const message = error instanceof Error ? error.message : '心理分析失败'
    analysisAdvice.value = message
    showMessage('error', message)
  }
}

function closeAnalysis() {
  analysisOpen.value = false
  if (analysisTimer) {
    window.clearInterval(analysisTimer)
    analysisTimer = null
  }
  if (demoCarouselTimer) {
    window.clearInterval(demoCarouselTimer)
    demoCarouselTimer = null
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
  if (demoCarouselTimer) {
    window.clearInterval(demoCarouselTimer)
    demoCarouselTimer = null
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
    analysisScore,
    analysisRiskLabel,
    analysisDemoMode,
    analysisDemoImages,
    analysisDemoImageIndex,
    analysisDemoWordcloudVisible,
    analysisDemoResultVisible,
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
    showAnalysisWordcloud,
    showAnalysisResult,
    exportAnalysisReportPdf,
    closeAnalysis,
    submitTreePost,
    stopAllTimers,
  }
}
