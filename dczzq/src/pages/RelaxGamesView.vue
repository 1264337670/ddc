<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, reactive, ref, watch } from 'vue'

type GameTab = '呼吸泡泡' | '贪吃蛇' | '填色盘' | '小鸟过柱'

interface GameCard {
  title: GameTab
  subtitle: string
  color: string
  preview: string
}

interface SnakePoint {
  x: number
  y: number
}

interface FlappyPipe {
  x: number
  y: number
  passed: boolean
}

interface ColoringArtwork {
  key: string
  name: string
  lineArt: string
  original: string
}

const snakeCanvasWidth = 620
const snakeCanvasHeight = 420
const snakeCell = 20
const snakeCols = Math.floor(snakeCanvasWidth / snakeCell)
const snakeRows = Math.floor(snakeCanvasHeight / snakeCell)
const flappyCanvasWidth = 620
const flappyCanvasHeight = 420
const paintCanvasSize = 560

const activeGame = ref<GameTab>('呼吸泡泡')
const showingGame = ref(false)

const gameCards: GameCard[] = [
  {
    title: '呼吸泡泡',
    subtitle: '点击进入呼吸泡泡房间，跟着节律慢慢放松。',
    color: 'linear-gradient(135deg, #a8e3ff, #c1f8df)',
    preview: '/assets/paopao.png',
  },
  {
    title: '贪吃蛇',
    subtitle: '键盘控制方向，专注每一步，找回节奏感。',
    color: 'linear-gradient(135deg, #b5e8b9, #e3f8a5)',
    preview: '/assets/snake.png',
  },
  {
    title: '填色盘',
    subtitle: '给多肉植物填色，把心情画成温暖的颜色。',
    color: 'linear-gradient(135deg, #ffd8b3, #ffe3f4)',
    preview: '/assets/color.png',
  },
  {
    title: '小鸟过柱',
    subtitle: '点击起飞穿越障碍，释放紧绷与压力。',
    color: 'linear-gradient(135deg, #b7ccff, #caedff)',
    preview: '/assets/bird.jpg',
  },
]

function enterGame(game: GameTab) {
  activeGame.value = game
  showingGame.value = true
  if (game === '贪吃蛇') {
    initSnake()
  }
  if (game === '小鸟过柱') {
    initFlappy()
  }
}

function switchGame(game: GameTab) {
  activeGame.value = game
  if (game === '贪吃蛇') {
    initSnake()
  }
  if (game === '小鸟过柱') {
    initFlappy()
  }
}

function backToCards() {
  showingGame.value = false
}

const bState = ref<'idle' | 'breathe-inhale' | 'breathe-exhale'>('idle')
const bHint = ref('点击下方按钮，深呼吸放松身心。')
let bLoop: number | null = null

function startBreathing() {
  if (bLoop) {
    window.clearInterval(bLoop)
    bLoop = null
  }
  bHint.value = '准备... 慢慢吸气...'
  bState.value = 'breathe-inhale'
  bLoop = window.setInterval(() => {
    if (bState.value === 'breathe-inhale') {
      bState.value = 'breathe-exhale'
      bHint.value = '缓缓呼气... 放松...'
    } else {
      bState.value = 'breathe-inhale'
      bHint.value = '慢慢吸气... 内心平静...'
    }
  }, 4000)
}

function stopBreathing() {
  if (bLoop) {
    window.clearInterval(bLoop)
    bLoop = null
  }
  bState.value = 'idle'
  bHint.value = '已停止放松。'
}

const colors = ['#FF0000', '#00AA00', '#0066FF', '#FFD700', '#FF7F00', '#8000FF', '#00CED1', '#FF69B4', '#8B4513', '#111111', '#FFFFFF']
const currentColor = ref('#00AA00')
const mixColors = ref<string[]>([])
const activeArtIndex = ref(0)
const coloringArtworks: ColoringArtwork[] = [
  { key: 'kitty', name: 'Hello Kitty', lineArt: '/assets/kitty1.png', original: '/assets/kitty_ori.jpg' },
  { key: 'melody', name: '美乐蒂', lineArt: '/assets/melody.png', original: '/assets/melody_ori.jpg' },
  { key: 'atm', name: '奥特曼', lineArt: '/assets/atm.png', original: '/assets/atm_ori.jpg' },
  { key: 'lion', name: '小狮子', lineArt: '/assets/lion.png', original: '/assets/lion_ori.jpg' },
  { key: 'car', name: '变形金刚', lineArt: '/assets/car.png', original: '/assets/car_ori.png' },
]
const fallbackArtwork: ColoringArtwork = {
  key: 'fallback',
  name: '填色画',
  lineArt: '/assets/kitty1.png',
  original: '/assets/kitty_ori.jpg',
}
const totalArtCount = computed(() => coloringArtworks.length)
const activeArtwork = computed<ColoringArtwork>(() => coloringArtworks[activeArtIndex.value] ?? coloringArtworks[0] ?? fallbackArtwork)
const mixedColor = computed(() => {
  if (!mixColors.value.length) {
    return currentColor.value
  }
  let totalR = 0
  let totalG = 0
  let totalB = 0
  mixColors.value.forEach((hex) => {
    const rgb = hexToRgb(hex)
    totalR += rgb.r
    totalG += rgb.g
    totalB += rgb.b
  })
  const count = mixColors.value.length
  const r = Math.round(totalR / count)
  const g = Math.round(totalG / count)
  const b = Math.round(totalB / count)
  return `rgb(${r}, ${g}, ${b})`
})

function hexToRgb(hex: string) {
  const normalized = hex.replace('#', '')
  const full = normalized.length === 3 ? normalized.split('').map((char) => char + char).join('') : normalized
  const number = Number.parseInt(full, 16)
  return {
    r: (number >> 16) & 255,
    g: (number >> 8) & 255,
    b: number & 255,
  }
}

function applyMixedColor() {
  currentColor.value = mixedColor.value
}

function clearMix() {
  mixColors.value = []
}

function prevArt() {
  activeArtIndex.value = (activeArtIndex.value - 1 + totalArtCount.value) % totalArtCount.value
}

function nextArt() {
  activeArtIndex.value = (activeArtIndex.value + 1) % totalArtCount.value
}

function startDragColor(event: DragEvent, color: string) {
  if (!event.dataTransfer) {
    return
  }
  event.dataTransfer.setData('text/plain', color)
}

function dropOnMixer(event: DragEvent) {
  const color = event.dataTransfer?.getData('text/plain')
  if (!color) {
    return
  }
  if (!colors.includes(color)) {
    return
  }
  mixColors.value.push(color)
}

const paintCanvas = ref<HTMLCanvasElement | null>(null)
let paintCtx: CanvasRenderingContext2D | null = null
const sourceImageCache = new Map<string, HTMLImageElement>()
const canvasStateCache = new Map<string, ImageData>()
let paintDrawRect = { x: 0, y: 0, width: paintCanvasSize, height: paintCanvasSize }

function parseColorToRgb(color: string) {
  const hexMatch = color.match(/^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/)
  if (hexMatch) {
    const normalized = color.replace('#', '')
    const full = normalized.length === 3 ? normalized.split('').map((char) => char + char).join('') : normalized
    const number = Number.parseInt(full, 16)
    return {
      r: (number >> 16) & 255,
      g: (number >> 8) & 255,
      b: number & 255,
    }
  }

  const rgbMatch = color.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/i)
  if (rgbMatch) {
    return {
      r: Number(rgbMatch[1] ?? 0),
      g: Number(rgbMatch[2] ?? 0),
      b: Number(rgbMatch[3] ?? 0),
    }
  }

  return { r: 0, g: 170, b: 0 }
}

function drawContainedImage(context: CanvasRenderingContext2D, image: HTMLImageElement) {
  const canvasWidth = context.canvas.width
  const canvasHeight = context.canvas.height
  context.clearRect(0, 0, canvasWidth, canvasHeight)
  context.fillStyle = '#ffffff'
  context.fillRect(0, 0, canvasWidth, canvasHeight)

  const ratio = Math.min(canvasWidth / image.width, canvasHeight / image.height)
  const drawWidth = image.width * ratio
  const drawHeight = image.height * ratio
  const drawX = (canvasWidth - drawWidth) / 2
  const drawY = (canvasHeight - drawHeight) / 2
  paintDrawRect = { x: drawX, y: drawY, width: drawWidth, height: drawHeight }
  context.drawImage(image, drawX, drawY, drawWidth, drawHeight)
}

function setupPaintCanvas() {
  nextTick(() => {
    const canvas = paintCanvas.value
    if (!canvas) {
      return
    }
    paintCtx = canvas.getContext('2d')
    if (!paintCtx) {
      return
    }

    const artwork = activeArtwork.value
    if (!artwork) {
      return
    }
    const cachedState = canvasStateCache.get(artwork.key)
    if (cachedState) {
      paintCtx.putImageData(cachedState, 0, 0)
      return
    }

    const cachedImage = sourceImageCache.get(artwork.lineArt)
    if (cachedImage && cachedImage.complete) {
      drawContainedImage(paintCtx, cachedImage)
      return
    }

    const image = new Image()
    image.onload = () => {
      sourceImageCache.set(artwork.lineArt, image)
      if (!paintCtx) {
        return
      }
      drawContainedImage(paintCtx, image)
    }
    image.src = artwork.lineArt
  })
}

function isDarkLine(data: Uint8ClampedArray, index: number) {
  const r = data[index] ?? 255
  const g = data[index + 1] ?? 255
  const b = data[index + 2] ?? 255
  const a = data[index + 3] ?? 255
  return a > 20 && r < 70 && g < 70 && b < 70
}

function matchesTargetColor(data: Uint8ClampedArray, index: number, target: { r: number; g: number; b: number; a: number }) {
  const r = data[index] ?? 0
  const g = data[index + 1] ?? 0
  const b = data[index + 2] ?? 0
  const a = data[index + 3] ?? 0
  const tolerance = 24
  return (
    Math.abs(r - target.r) <= tolerance
    && Math.abs(g - target.g) <= tolerance
    && Math.abs(b - target.b) <= tolerance
    && Math.abs(a - target.a) <= tolerance
  )
}

function fillPaintArea(event: MouseEvent) {
  const canvas = paintCanvas.value
  if (!canvas || !paintCtx) {
    return
  }

  const rect = canvas.getBoundingClientRect()
  const x = Math.floor((event.clientX - rect.left) * (canvas.width / rect.width))
  const y = Math.floor((event.clientY - rect.top) * (canvas.height / rect.height))
  if (x < 0 || y < 0 || x >= canvas.width || y >= canvas.height) {
    return
  }
  if (
    x < paintDrawRect.x
    || x > paintDrawRect.x + paintDrawRect.width
    || y < paintDrawRect.y
    || y > paintDrawRect.y + paintDrawRect.height
  ) {
    return
  }

  const imageData = paintCtx.getImageData(0, 0, canvas.width, canvas.height)
  const data = imageData.data
  const startIndex = (y * canvas.width + x) * 4
  if (isDarkLine(data, startIndex)) {
    return
  }

  const target = {
    r: data[startIndex] ?? 0,
    g: data[startIndex + 1] ?? 0,
    b: data[startIndex + 2] ?? 0,
    a: data[startIndex + 3] ?? 255,
  }
  const fill = parseColorToRgb(currentColor.value)
  if (Math.abs(target.r - fill.r) < 8 && Math.abs(target.g - fill.g) < 8 && Math.abs(target.b - fill.b) < 8) {
    return
  }

  const stack: Array<[number, number]> = [[x, y]]
  while (stack.length) {
    const point = stack.pop()
    if (!point) {
      continue
    }
    const [px, py] = point
    if (px < 0 || py < 0 || px >= canvas.width || py >= canvas.height) {
      continue
    }

    const idx = (py * canvas.width + px) * 4
    if (isDarkLine(data, idx) || !matchesTargetColor(data, idx, target)) {
      continue
    }

    data[idx] = fill.r
    data[idx + 1] = fill.g
    data[idx + 2] = fill.b
    data[idx + 3] = 255

    stack.push([px + 1, py])
    stack.push([px - 1, py])
    stack.push([px, py + 1])
    stack.push([px, py - 1])
  }

  paintCtx.putImageData(imageData, 0, 0)
  const artwork = activeArtwork.value
  if (artwork) {
    canvasStateCache.set(artwork.key, imageData)
  }
}

watch(
  () => [activeGame.value, activeArtIndex.value],
  () => {
    if (activeGame.value === '填色盘') {
      setupPaintCanvas()
    }
  },
)

const snakeCanvas = ref<HTMLCanvasElement | null>(null)
const snakeScore = ref(0)
const snakePlaying = ref(false)
let snakeCtx: CanvasRenderingContext2D | null = null
let snake: SnakePoint[] = []
let food: SnakePoint = { x: 0, y: 0 }
let direction: 'left' | 'right' | 'up' | 'down' = 'right'
let snakeLoop: number | null = null

function initSnake() {
  nextTick(() => {
    snakeCtx = snakeCanvas.value?.getContext('2d') ?? null
    drawSnakeBoard()
  })
}

function drawSnakeBoard() {
  if (!snakeCtx) {
    return
  }
  snakeCtx.fillStyle = '#FFFaf2'
  snakeCtx.fillRect(0, 0, snakeCanvasWidth, snakeCanvasHeight)
  snakeCtx.font = '22px Arial'
  snakeCtx.fillStyle = '#A38C80'
  snakeCtx.fillText('准备好了就可以点开始哦 ⭐', 130, 210)
}

function changeDirection(event: KeyboardEvent) {
  const key = event.keyCode
  if (key === 37 && direction !== 'right') direction = 'left'
  else if (key === 38 && direction !== 'down') direction = 'up'
  else if (key === 39 && direction !== 'left') direction = 'right'
  else if (key === 40 && direction !== 'up') direction = 'down'

  if ([37, 38, 39, 40].includes(key)) {
    event.preventDefault()
  }
}

function spawnFood() {
  food = {
    x: Math.floor(Math.random() * (snakeCols - 1)) * snakeCell,
    y: Math.floor(Math.random() * (snakeRows - 1)) * snakeCell,
  }
}

function gameOver(message: string) {
  if (snakeLoop) {
    window.clearInterval(snakeLoop)
    snakeLoop = null
  }
  window.removeEventListener('keydown', changeDirection)
  snakePlaying.value = false
  if (!snakeCtx) {
    return
  }
  snakeCtx.fillStyle = 'rgba(255, 250, 242, 0.7)'
  snakeCtx.fillRect(0, 0, snakeCanvasWidth, snakeCanvasHeight)
  snakeCtx.fillStyle = '#5C4B41'
  snakeCtx.font = 'bold 24px Arial'
  snakeCtx.fillText(message, 40, 240)
}

function startSnake() {
  if (snakePlaying.value) {
    return
  }
  snakePlaying.value = true
  snakeScore.value = 0
  direction = 'right'
  snake = [
    { x: 300, y: 220 },
    { x: 280, y: 220 },
    { x: 260, y: 220 },
  ]
  spawnFood()
  window.addEventListener('keydown', changeDirection)
  if (snakeLoop) {
    window.clearInterval(snakeLoop)
  }
  snakeLoop = window.setInterval(gameLoop, 150)
}

function stopSnake() {
  gameOver(`休息一下吧，得分: ${snakeScore.value}`)
}

function gameLoop() {
  if (!snakeCtx) {
    return
  }
  const head: SnakePoint = { x: snake[0]?.x ?? 0, y: snake[0]?.y ?? 0 }
  if (direction === 'right') head.x += snakeCell
  if (direction === 'left') head.x -= snakeCell
  if (direction === 'up') head.y -= snakeCell
  if (direction === 'down') head.y += snakeCell

  if (head.x < 0 || head.x >= snakeCanvasWidth || head.y < 0 || head.y >= snakeCanvasHeight) {
    gameOver(`撞到了墙墙~ 得分: ${snakeScore.value}`)
    return
  }

  for (let index = 0; index < snake.length; index += 1) {
    if (head.x === snake[index]?.x && head.y === snake[index]?.y) {
      gameOver('咬到自己的小尾巴了~')
      return
    }
  }

  snake.unshift(head)
  if (head.x === food.x && head.y === food.y) {
    snakeScore.value += 10
    spawnFood()
  } else {
    snake.pop()
  }

  snakeCtx.fillStyle = '#FFFaf2'
  snakeCtx.fillRect(0, 0, snakeCanvasWidth, snakeCanvasHeight)

  snakeCtx.fillStyle = '#FF9A5A'
  snakeCtx.beginPath()
  snakeCtx.arc(food.x + 10, food.y + 10, 9, 0, Math.PI * 2)
  snakeCtx.fill()

  for (let index = 0; index < snake.length; index += 1) {
    snakeCtx.fillStyle = index === 0 ? '#57C783' : '#6BCB77'
    const part = snake[index]
    if (!part) {
      continue
    }
    if (typeof snakeCtx.roundRect === 'function') {
      snakeCtx.beginPath()
      snakeCtx.roundRect(part.x + 1, part.y + 1, 18, 18, 4)
      snakeCtx.fill()
    } else {
      snakeCtx.fillRect(part.x + 1, part.y + 1, 18, 18)
    }
  }
}

const flappyCanvas = ref<HTMLCanvasElement | null>(null)
const flappyScore = ref(0)
let flappyCtx: CanvasRenderingContext2D | null = null
let flappyLoop: number | null = null
const flappyState = reactive({
  birdY: 150,
  velocity: 0,
  pipes: [] as FlappyPipe[],
  frame: 0,
  playing: false,
})

function initFlappy() {
  nextTick(() => {
    flappyCtx = flappyCanvas.value?.getContext('2d') ?? null
    flappyState.playing = false
    if (!flappyCtx) {
      return
    }
    flappyCtx.fillStyle = '#70c5ce'
    flappyCtx.fillRect(0, 0, flappyCanvasWidth, flappyCanvasHeight)
    flappyCtx.fillStyle = '#f4d03f'
    flappyCtx.beginPath()
    flappyCtx.arc(160, 200, 18, 0, Math.PI * 2)
    flappyCtx.fill()
    flappyCtx.fillStyle = '#333'
    flappyCtx.font = '20px Arial'
    flappyCtx.fillText('点击画面开始起飞', 220, 250)
  })
}

function resetFlappy() {
  flappyScore.value = 0
  flappyState.birdY = 200
  flappyState.velocity = 0
  flappyState.pipes = []
  flappyState.frame = 0
  flappyState.playing = true
  if (flappyLoop) {
    window.clearInterval(flappyLoop)
  }
  flappyLoop = window.setInterval(flappyUpdate, 24)
}

function flapBird() {
  if (!flappyState.playing) {
    resetFlappy()
    return
  }
  flappyState.velocity = -6.5
}

function flappyGameOver() {
  if (flappyLoop) {
    window.clearInterval(flappyLoop)
    flappyLoop = null
  }
  flappyState.playing = false
  if (!flappyCtx) {
    return
  }
  flappyCtx.fillStyle = 'rgba(0,0,0,0.5)'
  flappyCtx.fillRect(0, 0, flappyCanvasWidth, flappyCanvasHeight)
  flappyCtx.fillStyle = '#fff'
  flappyCtx.font = 'bold 36px Arial'
  flappyCtx.fillText('撞到啦', 250, 190)
  flappyCtx.font = '18px Arial'
  flappyCtx.fillText('点击或触摸画面重试', 225, 240)
}

function flappyUpdate() {
  if (!flappyCtx) {
    return
  }

  flappyState.velocity += 0.4
  flappyState.birdY += flappyState.velocity

  if (flappyState.frame % 100 === 0) {
    const pipeGap = 110
    const pipeY = Math.random() * (flappyCanvasHeight - pipeGap - 80) + 40
    flappyState.pipes.push({ x: flappyCanvasWidth, y: pipeY, passed: false })
  }

  flappyCtx.clearRect(0, 0, flappyCanvasWidth, flappyCanvasHeight)
  flappyCtx.fillStyle = '#70c5ce'
  flappyCtx.fillRect(0, 0, flappyCanvasWidth, flappyCanvasHeight)

  flappyCtx.fillStyle = '#73bf2e'
  for (let index = flappyState.pipes.length - 1; index >= 0; index -= 1) {
    const pipe = flappyState.pipes[index]
    if (!pipe) {
      continue
    }
    pipe.x -= 2.5

    const pipeGap = 110
    const pipeWidth = 50
    flappyCtx.fillRect(pipe.x, 0, pipeWidth, pipe.y)
    flappyCtx.fillRect(pipe.x, pipe.y + pipeGap, pipeWidth, flappyCanvasHeight - pipe.y - pipeGap)

    if (!pipe.passed && pipe.x + pipeWidth < 160) {
      flappyScore.value += 1
      pipe.passed = true
    }

    const birdX = 160
    const birdR = 14
    if (flappyState.birdY + birdR > flappyCanvasHeight || flappyState.birdY - birdR < 0) {
      flappyGameOver()
      return
    }
    if (birdX + birdR > pipe.x && birdX - birdR < pipe.x + pipeWidth) {
      if (flappyState.birdY - birdR < pipe.y || flappyState.birdY + birdR > pipe.y + pipeGap) {
        flappyGameOver()
        return
      }
    }

    if (pipe.x < -60) {
      flappyState.pipes.splice(index, 1)
    }
  }

  flappyCtx.fillStyle = '#f4d03f'
  flappyCtx.beginPath()
  flappyCtx.arc(160, flappyState.birdY, 18, 0, Math.PI * 2)
  flappyCtx.fill()
  flappyCtx.fillStyle = '#333'
  flappyCtx.beginPath()
  flappyCtx.arc(166, flappyState.birdY - 5, 3.5, 0, Math.PI * 2)
  flappyCtx.fill()

  flappyState.frame += 1
}

onBeforeUnmount(() => {
  if (bLoop) window.clearInterval(bLoop)
  if (snakeLoop) window.clearInterval(snakeLoop)
  if (flappyLoop) window.clearInterval(flappyLoop)
  window.removeEventListener('keydown', changeDirection)
})
</script>

<template>
  <section class="game-section reveal">
    <h2>放松小游戏</h2>

    <div v-if="!showingGame" class="game-cards-row">
      <button
        v-for="card in gameCards"
        :key="card.title"
        class="game-entry-card"
        :style="{ background: card.color }"
        @click="enterGame(card.title)"
      >
        <div class="card-preview" :class="`preview-${card.title}`">
          <img class="preview-image" :src="card.preview" :alt="card.title" />
        </div>
        <h3>{{ card.title }}</h3>
        <p>{{ card.subtitle }}</p>
      </button>
    </div>

    <div v-else class="play-wrap">
      <div class="game-tabs">
        <button class="tab-btn" @click="backToCards">返回游戏卡片</button>
        <button
          v-for="tab in ['呼吸泡泡', '贪吃蛇', '填色盘', '小鸟过柱']"
          :key="tab"
          class="tab-btn"
          :class="{ active: activeGame === tab }"
          @click="switchGame(tab as GameTab)"
        >
          {{ tab }}
        </button>
      </div>

      <article v-if="activeGame === '呼吸泡泡'" class="game-card glass breathing-game">
        <div class="breathing-wrap">
          <div class="breathing-head">
            <h3>呼吸泡泡房间</h3>
            <p>{{ bHint }}</p>
          </div>
          <div class="breathing-main">
            <div class="breathing-character" :class="bState">
              <img class="breathing-image" src="/assets/breath.png" alt="呼吸泡泡" />
            </div>
          </div>
          <div class="breathing-actions">
            <button v-if="bState === 'idle'" class="game-btn warm" @click="startBreathing">同我一起呼吸</button>
            <button v-else class="game-btn" @click="stopBreathing">结束深呼吸</button>
          </div>
        </div>
      </article>

      <article v-if="activeGame === '贪吃蛇'" class="game-card glass">
        <h3>暖心贪吃蛇</h3>
        <p>使用键盘方向键控制，吃到星星带来好心情 ⭐ 得分: {{ snakeScore }}</p>
        <canvas
          ref="snakeCanvas"
          :width="snakeCanvasWidth"
          :height="snakeCanvasHeight"
          class="snake-board"
        ></canvas>
        <div class="game-actions">
          <button class="game-btn" @click="startSnake" v-if="!snakePlaying">开始游玩</button>
          <button class="game-btn" @click="stopSnake" v-else>结束游玩</button>
        </div>
      </article>

      <article v-if="activeGame === '填色盘'" class="game-card glass painting-game">
        <h3>色彩治愈馆</h3>
        <p>从底部拖拽基础颜色到中央调色盘，混合后再给填色画上色</p>
        <div class="coloring-layout">
          <section class="mix-panel">
            <div class="mix-board" @dragover.prevent @drop="dropOnMixer">
              <div class="mix-display" :style="{ background: mixedColor }"></div>
              <p>把基础色拖到这里混合（可叠加）</p>
              <div class="mix-chips">
                <span v-for="(mix, index) in mixColors" :key="`${mix}-${index}`" :style="{ background: mix }"></span>
              </div>
            </div>
            <div class="mix-actions">
              <button class="game-btn" @click="applyMixedColor">使用混合色</button>
              <button class="game-btn" @click="clearMix">清空混色</button>
            </div>
            <div class="palette">
              <button
                v-for="color in colors"
                :key="color"
                :class="['color-swatch', { active: currentColor === color }]"
                :style="{ background: color }"
                draggable="true"
                @dragstart="startDragColor($event, color)"
                @click="currentColor = color"
              ></button>
            </div>
          </section>

          <section class="paint-panel">
            <div class="paint-card">
              <button class="nav-btn nav-btn-left" @click="prevArt">◀</button>
              <button class="nav-btn nav-btn-right" @click="nextArt">▶</button>
              <div class="paint-index">画作 {{ activeArtIndex + 1 }} / {{ totalArtCount }}</div>
              <div class="kitty-compare-wrap">
                <div class="kitty-pane">
                  <h4>{{ activeArtwork.name }} 填色画</h4>
                  <canvas
                    ref="paintCanvas"
                    class="kitty-board"
                    :width="paintCanvasSize"
                    :height="paintCanvasSize"
                    @click="fillPaintArea"
                  ></canvas>
                </div>
                <div class="kitty-pane">
                  <h4>原图</h4>
                  <img class="kitty-original" :src="activeArtwork.original" :alt="`${activeArtwork.name} 原图`" />
                </div>
              </div>
            </div>
          </section>
        </div>
      </article>

      <article v-if="activeGame === '小鸟过柱'" class="game-card glass">
        <h3>小鸟过柱</h3>
        <p>点击画面跳跃，跨越每一个障碍！ 目前得分: {{ flappyScore }}</p>
        <canvas
          ref="flappyCanvas"
          :width="flappyCanvasWidth"
          :height="flappyCanvasHeight"
          class="flappy-board"
          @mousedown="flapBird"
          @touchstart.prevent="flapBird"
        ></canvas>
      </article>
    </div>
  </section>
</template>

<style scoped>
.game-section {
  border-radius: 28px;
  padding: 24px;
}

.game-cards-row {
  margin-top: 14px;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.game-entry-card {
  border: 0;
  border-radius: 22px;
  padding: 26px 18px;
  min-height: 78vh;
  text-align: left;
  cursor: pointer;
  box-shadow: 0 14px 26px rgba(58, 86, 132, 0.16);
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}

.game-entry-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 20px 36px rgba(58, 86, 132, 0.22);
}

.game-entry-card h3 {
  margin: 0;
  font-size: 1.58rem;
  color: #2d436a;
}

.game-entry-card p {
  margin-top: 12px;
  color: #4a648f;
  line-height: 1.75;
  font-size: 1rem;
}

.play-wrap {
  margin-top: 10px;
}

.card-preview {
  height: 210px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.08);
  margin-bottom: 18px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.preview-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center center;
}

.mini-bubble {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: radial-gradient(circle at 28% 28%, #fff, #6fd7ff);
  margin: 44px auto 0;
  animation: previewBubble 2.4s ease-in-out infinite;
}

.mini-snake-track {
  position: absolute;
  inset: 18px;
  border-radius: 12px;
  background: rgba(219, 232, 255, 0.9);
}

.mini-snake-track span {
  position: absolute;
  width: 34px;
  height: 14px;
  border-radius: 12px;
  background: linear-gradient(90deg, #69c2ec, #66d6a0);
  top: 50%;
  transform: translateY(-50%);
  animation: snakeMove 3s linear infinite;
}

.mini-palette {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  padding: 22px;
}

.mini-palette span {
  height: 70px;
  border-radius: 12px;
}

.mini-palette span:nth-child(1) { background: #ffb48f; }
.mini-palette span:nth-child(2) { background: #7cc8ff; }
.mini-palette span:nth-child(3) { background: #96df9f; }
.mini-palette span:nth-child(4) { background: #ffd46f; }

.mini-flappy {
  position: absolute;
  inset: 0;
}

.mini-flappy .pipe-l,
.mini-flappy .pipe-r {
  position: absolute;
  width: 24px;
  background: linear-gradient(180deg, #7dcc8b, #4ea75f);
}

.mini-flappy .pipe-l {
  left: 18%;
  top: 0;
  height: 65%;
}

.mini-flappy .pipe-r {
  right: 16%;
  bottom: 0;
  height: 60%;
}

.mini-flappy .bird-dot {
  position: absolute;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #f4d03f;
  left: 42%;
  top: 55%;
  animation: birdBob 1.6s ease-in-out infinite;
}

.game-tabs {
  margin: 12px 0;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tab-btn,
.game-btn {
  border: 0;
  border-radius: 999px;
  padding: 10px 16px;
  cursor: pointer;
}

.tab-btn {
  background: rgba(255, 255, 255, 0.45);
}

.tab-btn.active {
  background: linear-gradient(120deg, #ff8ea8, #ffb27a);
  color: #fff;
}

.game-card {
  position: relative;
  isolation: isolate;
  overflow: hidden;
  border-radius: 18px;
  padding: 18px;
  min-height: 74vh;
  display: flex;
  flex-direction: column;
}

.game-card::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image: linear-gradient(rgba(255, 255, 255, 0.48), rgba(255, 255, 255, 0.48)), url('/assets/game_bg.jpg');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  opacity: 0.62;
  z-index: 0;
  pointer-events: none;
}

.game-card > * {
  position: relative;
  z-index: 1;
}

.painting-game {
  min-height: 86vh;
}

.breathing-game {
  padding-bottom: 150px;
}

.glass {
  background: rgba(255, 255, 255, 0.24);
  border: 1px solid rgba(255, 255, 255, 0.7);
  box-shadow: 0 10px 30px rgba(55, 78, 120, 0.12);
  backdrop-filter: blur(14px);
}

.breathing-wrap {
  position: relative;
  height: 100%;
  flex: 1;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: stretch;
}

.breathing-head {
  width: 100%;
  text-align: center;
  z-index: 2;
}

.breathing-main {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
  z-index: 1;
}

.breathing-actions {
  margin-top: auto;
  padding-bottom: 0;
  align-self: stretch;
  display: flex;
  justify-content: center;
  z-index: 2;
}

.breathing-wrap p {
  color: #4b638b;
}

.breathing-character {
  width: 250px;
  height: 250px;
  margin: 18px auto 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  transition: transform 4s ease-in-out;
  pointer-events: auto;
}

.breathing-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
  transition: transform 4s ease-in-out, filter 4s ease-in-out;
}

.breathe-inhale {
  transform: scale(1.52);
}

.breathe-exhale {
  transform: scale(0.9);
}

.breathe-inhale .breathing-image,
.breathe-exhale .breathing-image {
  transform-origin: center center;
}

.game-btn {
  background: #fff;
  color: #2e5c31;
  font-size: 16px;
  font-weight: 700;
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
}

.game-btn.warm {
  background: #ff8c42;
  color: #fff;
}

.snake-board,
.flappy-board {
  display: block;
  margin: 14px auto;
  border-radius: 16px;
  border: 4px solid #fff;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  width: min(100%, 620px);
  max-width: 100%;
  height: auto;
}

.flappy-board {
  background: linear-gradient(#70c5ce, #def2f4);
  cursor: pointer;
}

.game-actions {
  display: flex;
  justify-content: center;
  gap: 10px;
}

.color-svg {
  width: 340px;
  height: 340px;
  flex: 0 0 auto;
}

.kitty-board {
  width: min(100%, 420px);
  height: auto;
  aspect-ratio: 1 / 1;
  border-radius: 12px;
  border: 2px solid rgba(255, 255, 255, 0.8);
  background: #fff;
  cursor: crosshair;
}

.kitty-original {
  width: min(100%, 420px);
  height: auto;
  max-height: 420px;
  object-fit: contain;
  border-radius: 12px;
  border: 2px solid rgba(255, 255, 255, 0.8);
  background: #fff;
  display: block;
}

.color-svg path {
  cursor: pointer;
  transition: fill 0.3s, opacity 0.2s;
  stroke: #3b5b4a;
  stroke-width: 2px;
}

.color-svg path:hover {
  opacity: 0.7;
}

.palette {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-top: 12px;
  flex-wrap: wrap;
}

.mix-board {
  border: 1px dashed rgba(76, 115, 167, 0.35);
  border-radius: 14px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.5);
}

.coloring-layout {
  margin-top: 14px;
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  gap: 16px;
  align-items: stretch;
}

.mix-panel,
.paint-panel {
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.42);
  border: 1px solid rgba(255, 255, 255, 0.7);
  padding: 14px;
}

.paint-card {
  position: relative;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14px;
  padding: 10px 52px;
}

.paint-index {
  margin-bottom: 4px;
  color: #44638f;
  font-weight: 700;
}

.nav-btn {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  border: 0;
  border-radius: 999px;
  width: 38px;
  height: 38px;
  background: #fff;
  cursor: pointer;
  box-shadow: 0 6px 16px rgba(40, 64, 92, 0.15);
  z-index: 2;
}

.nav-btn-left {
  left: 6px;
}

.nav-btn-right {
  right: 6px;
}

.kitty-compare-wrap {
  width: 100%;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  align-items: start;
}

.kitty-pane {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.kitty-pane h4 {
  margin: 0;
  color: #3f608f;
  font-size: 0.98rem;
}

.mix-display {
  width: 180px;
  height: 180px;
  margin: 0 auto;
  border-radius: 50%;
  border: 4px solid rgba(255, 255, 255, 0.85);
  box-shadow: inset 0 8px 24px rgba(0, 0, 0, 0.08);
}

.mix-board p {
  margin: 10px 0 8px;
  color: #3f608f;
}

.mix-chips {
  min-height: 28px;
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
}

.mix-chips span {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  border: 2px solid rgba(255, 255, 255, 0.9);
}

.mix-actions {
  margin-top: 10px;
  display: flex;
  justify-content: center;
  gap: 8px;
}

.color-swatch {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  cursor: pointer;
  border: 3px solid #fff;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.color-swatch.active {
  transform: scale(1.2);
  border-color: #555;
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

@keyframes previewBubble {
  0%,
  100% { transform: scale(0.9); }
  50% { transform: scale(1.1); }
}

@keyframes snakeMove {
  0% { left: 8%; }
  50% { left: 68%; }
  100% { left: 8%; }
}

@keyframes birdBob {
  0%,
  100% { transform: translateY(0); }
  50% { transform: translateY(-14px); }
}

@media (max-width: 1280px) {
  .game-cards-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .game-entry-card {
    min-height: 54vh;
  }

  .game-card {
    min-height: 68vh;
  }

  .painting-game {
    min-height: 82vh;
  }
}

@media (max-width: 760px) {
  .game-cards-row {
    grid-template-columns: 1fr;
  }

  .game-entry-card {
    min-height: 46vh;
  }

  .game-card {
    min-height: 62vh;
  }

  .painting-game {
    min-height: 86vh;
  }

  .coloring-layout {
    grid-template-columns: 1fr;
  }

  .kitty-compare-wrap {
    grid-template-columns: 1fr;
  }
}
</style>
