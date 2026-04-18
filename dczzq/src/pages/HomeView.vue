<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

type SlideKey = '心理分析' | '心理百科' | '联系导师' | '放松一下' | '秘密树洞'

interface HomeSlide {
  key: SlideKey
  title: string
  subtitle: string
  image: string
  path: string
}

const router = useRouter()
const activeIndex = ref(0)
let autoTimer: number | null = null

const slides: HomeSlide[] = [
  {
    key: '心理百科',
    title: '心理百科',
    subtitle: '阅读常见心理议题，找到适合自己的调节方式。',
    image: '/assets/baike.jpg',
    path: '/encyclopedia',
  },
  {
    key: '秘密树洞',
    title: '秘密树洞',
    subtitle: '在树洞写下心情，安全表达不被打断。',
    image: '/assets/shudong.jpg',
    path: '/tree-hole',
  },
  {
    key: '放松一下',
    title: '放松一下',
    subtitle: '通过互动小游戏，给自己一个轻松出口。',
    image: '/assets/fangsong.jpg',
    path: '/relax',
  },
  {
    key: '联系导师',
    title: '联系导师',
    subtitle: '选择匹配导师，获得更有方向感的支持。',
    image: '/assets/lianxi.jpg',
    path: '/mentor',
  },
  {
    key: '心理分析',
    title: '心理分析',
    subtitle: '一键进入心理分析，快速了解当下状态。',
    image: '/assets/fenxi.jpg',
    path: '/analysis',
  },
]

const defaultSlide: HomeSlide = slides[0] as HomeSlide
const activeSlide = computed<HomeSlide>(() => slides[activeIndex.value] ?? defaultSlide)

function switchSlide(index: number) {
  activeIndex.value = index
  restartAutoPlay()
}

function nextSlide() {
  activeIndex.value = (activeIndex.value + 1) % slides.length
}

function prevSlide() {
  activeIndex.value = (activeIndex.value - 1 + slides.length) % slides.length
}

function startAutoPlay() {
  if (autoTimer) {
    window.clearInterval(autoTimer)
  }
  autoTimer = window.setInterval(() => {
    nextSlide()
  }, 3500)
}

function restartAutoPlay() {
  startAutoPlay()
}

function openSlide() {
  router.push(activeSlide.value.path)
}

onMounted(() => {
  startAutoPlay()
})

onBeforeUnmount(() => {
  if (autoTimer) {
    window.clearInterval(autoTimer)
    autoTimer = null
  }
})
</script>

<template>
  <section class="home-board glass reveal">
    <div class="carousel-layout">
      <div class="slide-panel">
        <img :src="activeSlide.image" :alt="activeSlide.title" class="slide-image" />
        <button class="arrow-btn left" @click.stop="prevSlide">‹</button>
        <button class="arrow-btn right" @click.stop="nextSlide">›</button>
        <div class="slide-mask">
          <h2>{{ activeSlide.title }}</h2>
          <p>{{ activeSlide.subtitle }}</p>
        </div>
        <button class="slide-hit" @click="openSlide" aria-label="打开当前页面"></button>
      </div>
      <aside class="slide-index">
        <button
          v-for="(slide, index) in slides"
          :key="slide.key"
          class="index-item"
          :class="{ active: index === activeIndex }"
          @mouseenter="switchSlide(index)"
          @focus="switchSlide(index)"
          @click="switchSlide(index)"
        >
          {{ slide.title }}
        </button>
      </aside>
    </div>
  </section>
</template>

<style scoped>
.home-board,
.slide-index,
.index-item {
  font-family: 'Ma Shan Zheng', 'STKaiti', 'KaiTi', cursive;
}

.home-board {
  border-radius: 28px;
  padding: 22px;
}

.glass {
  background: rgba(255, 255, 255, 0.52);
  border: 1px solid rgba(255, 255, 255, 0.7);
  box-shadow: 0 10px 30px rgba(55, 78, 120, 0.12);
  backdrop-filter: blur(14px);
}

.carousel-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 360px;
  gap: 8px;
  height: 72vh;
  min-height: 620px;
  max-width: 1240px;
  margin: 0 auto;
}

.slide-panel {
  border: 0;
  border-radius: 20px 0 0 20px;
  overflow: hidden;
  padding: 0;
  position: relative;
  transform: translateX(-24px);
}

.slide-hit {
  position: absolute;
  inset: 0;
  background: transparent;
  border: 0;
  cursor: pointer;
}

.arrow-btn {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  z-index: 3;
  width: 42px;
  height: 42px;
  border-radius: 999px;
  border: 0;
  cursor: pointer;
  font-size: 1.9rem;
  line-height: 1;
  background: rgba(255, 255, 255, 0.78);
  color: #2b4a74;
}

.arrow-btn.left {
  left: 10px;
}

.arrow-btn.right {
  right: 10px;
}

.slide-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.slide-mask {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 20px;
  color: #fff;
  text-align: left;
  background: linear-gradient(180deg, rgba(26, 41, 68, 0) 0%, rgba(26, 41, 68, 0.68) 100%);
}

.slide-mask h2 {
  margin: 0;
  font-size: 2.2rem;
}

.slide-mask p {
  margin: 10px 0 0;
  font-size: 1.26rem;
}

.slide-index {
  border-radius: 0 20px 20px 0;
  background: rgba(255, 255, 255, 0.48);
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  height: 100%;
  transform: translateX(24px);
  overflow: hidden;
  box-sizing: border-box;
}

.index-item {
  border: 0;
  border-radius: 12px;
  padding: 12px;
  text-align: center;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.64);
  color: #2a456f;
  font-size: 1.65rem;
  letter-spacing: 1px;
  flex: 1 1 0;
  min-height: 0;
  line-height: 1.15;
  display: flex;
  align-items: center;
  justify-content: center;
}

.index-item.active {
  background: linear-gradient(120deg, #ff8ea8, #84baff);
  color: #fff;
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

@media (max-width: 900px) {
  .carousel-layout {
    grid-template-columns: 1fr;
    height: auto;
    min-height: 72vh;
    gap: 10px;
  }

  .slide-panel,
  .slide-index {
    border-radius: 16px;
    transform: none;
  }

  .slide-index {
    height: auto;
  }
}
</style>
