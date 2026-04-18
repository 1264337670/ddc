<script setup lang="ts">
import { computed, ref } from 'vue'
import { useMindIsland } from '../composables/useMindIsland'

const { encyclopediaItems } = useMindIsland()

const categoryColors: Record<string, [string, string]> = {
  情绪压力: ['#5d94d8', '#3f6db5'],
  行为习惯: ['#f7b267', '#f4845f'],
  自我成长: ['#7ed957', '#3bb273'],
}

function getCategoryColors(category: string): [string, string] {
  return categoryColors[category] ?? ['#5d94d8', '#3f6db5']
}

const categories = ['全部', '情绪压力', '行为习惯', '自我成长']
const selectedCategory = ref('全部')
const searchText = ref('')
const expandedTitles = ref<string[]>([])

const cardImages = {
  抑郁情绪: '/assets/youyu.jpg',
  焦虑紧张: '/assets/jiaolv.jpg',
  睡眠困扰: '/assets/sleep.jpg',
  内耗反刍: '/assets/neihao.jpg',
  社交压力: '/assets/social.jpg',
  情绪失控: '/assets/shikong.png',
  拖延行为: '/assets/tuoyan.jpg',
  考试焦虑: '/assets/kaoshi.jpg',
  自我否定: '/assets/fouding.jpg',
  关系边界: '/assets/bianjie.jpg',
  习得无助: '/assets/wuzhu.png',
  职业迷茫: '/assets/mimang.jpg',
} as const

const filteredItems = computed(() => {
  let items = encyclopediaItems
  if (selectedCategory.value !== '全部') {
    items = items.filter((i) => i.category === selectedCategory.value)
  }
  const keyword = searchText.value.trim()
  if (keyword) {
    items = items.filter((i) => i.title.includes(keyword))
  }
  return items
})

function selectCategory(category: string) {
  selectedCategory.value = category
}

function isExpanded(title: string) {
  return expandedTitles.value.includes(title)
}

function toggleCard(title: string) {
  if (isExpanded(title)) {
    expandedTitles.value = expandedTitles.value.filter((t) => t !== title)
    return
  }
  expandedTitles.value.push(title)
}

function hasCardImage(title: string) {
  return Boolean(cardImages[title as keyof typeof cardImages])
}
</script>

<template>
  <section class="grid-section reveal">
    <h2>心理百科</h2>

    <div class="ency-toolbar">
      <input v-model="searchText" class="ency-search" placeholder="搜索标题..." />
      <div class="ency-categories">
        <button
          v-for="cat in categories"
          :key="cat"
          type="button"
          :class="['ency-cat-btn', { active: selectedCategory === cat }]"
          @click="selectCategory(cat)"
        >
          {{ cat }}
        </button>
      </div>
    </div>

    <div class="card-grid">
      <article v-for="(item, idx) in filteredItems" :key="item.title" class="ency-card glass" :data-title="item.title">
        <div class="card-head" @click="toggleCard(item.title)">
          <h3>
            <span class="emoji-mask">
              <svg v-if="item.emoji" width="36" height="36" viewBox="0 0 36 36" aria-hidden="true">
                <defs>
                  <linearGradient :id="`emoji-circle-grad-${item.category}-${idx}`" x1="0" y1="0" x2="1" y2="1">
                    <stop offset="0%" :stop-color="getCategoryColors(item.category)[0]" />
                    <stop offset="100%" :stop-color="getCategoryColors(item.category)[1]" />
                  </linearGradient>
                </defs>
                <circle cx="18" cy="18" r="16" :fill="`url(#emoji-circle-grad-${item.category}-${idx})`" />
                <circle cx="18" cy="18" r="16" fill="none" stroke="#2d4f83" stroke-opacity="0.45" stroke-width="1" />
                <text
                  x="50%"
                  y="58%"
                  text-anchor="middle"
                  dominant-baseline="middle"
                  font-size="20"
                  fill="#ffffff"
                  font-family="Segoe UI Emoji, Noto Color Emoji, sans-serif"
                >
                  {{ item.emoji }}
                </text>
              </svg>
            </span>
            {{ item.title }}
          </h3>
          <button type="button" class="toggle-btn" :aria-expanded="isExpanded(item.title)">
            {{ isExpanded(item.title) ? '收起' : '展开' }}
          </button>
        </div>

        <transition name="fold">
          <div v-show="isExpanded(item.title)" class="card-body">
            <div class="card-copy">
              <p>{{ item.intro }}</p>
              <ul>
                <li v-for="tip in item.tips" :key="tip">{{ tip }}</li>
              </ul>
            </div>
            <div v-if="hasCardImage(item.title)" class="card-image-shell">
              <img class="card-image" :src="cardImages[item.title as keyof typeof cardImages]" :alt="item.title" />
            </div>
          </div>
        </transition>

        <div v-show="!isExpanded(item.title)" class="card-preview">
          <p>{{ item.intro }}</p>
        </div>
      </article>
    </div>
  </section>
</template>

<style scoped>
.grid-section {
  border-radius: 28px;
  padding: 24px;
}

.ency-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  margin: 8px 0 18px;
}

.ency-search {
  padding: 7px 14px;
  border-radius: 8px;
  border: 1px solid #b7c6e0;
  font-size: 15px;
  min-width: 220px;
  outline: none;
}

.ency-categories {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.ency-cat-btn {
  border: none;
  background: #eaf2fb;
  color: #355a88;
  border-radius: 7px;
  padding: 6px 14px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.18s, color 0.18s;
}

.ency-cat-btn.active {
  background: #5d94d8;
  color: #fff;
}

.card-grid {
  margin-top: 14px;
  display: grid;
  gap: 18px;
  grid-template-columns: repeat(4, 1fr);
  align-items: start;
  grid-auto-rows: minmax(144px, auto);
}

.emoji-mask {
  display: inline-block;
  width: 36px;
  height: 36px;
  vertical-align: middle;
  margin-right: 8px;
}

.ency-card {
  border-radius: 18px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow: hidden;
  align-self: start;
  min-height: 144px;
}

.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  cursor: pointer;
}

.card-head h3 {
  margin: 0;
  display: inline-flex;
  align-items: center;
  font-family: 'STKaiti', 'KaiTi', serif;
  font-size: 1.42rem;
  font-weight: 700;
  letter-spacing: 0.3px;
  color: #20385b;
}

.toggle-btn {
  border: 0;
  border-radius: 999px;
  padding: 6px 12px;
  font-size: 12px;
  color: #355a88;
  background: rgba(132, 186, 255, 0.24);
  cursor: pointer;
}

.card-copy {
  align-self: start;
}

.card-copy p {
  margin-top: 10px;
  color: #4e668d;
  line-height: 1.75;
  font-family: 'FangSong', serif;
}

.card-preview p {
  margin: 8px 0 0;
  color: #4e668d;
  line-height: 1.75;
  font-family: 'FangSong', serif;
}

.ency-card[data-title='抑郁情绪'] .card-preview p {
  margin-top: 10px;
}

.glass {
  background: rgba(255, 255, 255, 0.52);
  border: 1px solid rgba(255, 255, 255, 0.7);
  box-shadow: 0 10px 30px rgba(55, 78, 120, 0.12);
  backdrop-filter: blur(14px);
}

.ency-card ul {
  margin: 12px 0 0;
  padding: 0;
  list-style: none;
}

.ency-card li {
  position: relative;
  padding-left: 20px;
  margin-bottom: 8px;
  color: #3f5d89;
}

.ency-card li::before {
  content: '';
  position: absolute;
  left: 0;
  top: 10px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: linear-gradient(120deg, #ff9f95, #86b7ff);
}

.card-image-shell {
  margin: 0 -16px -16px;
  height: 420px;
  overflow: hidden;
}

.card-body {
  display: grid;
  grid-template-rows: auto 1fr;
  gap: 12px;
}

.fold-enter-active,
.fold-leave-active {
  transition: all 0.22s ease;
}

.fold-enter-from,
.fold-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

.card-image {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
  object-position: center top;
}

.reveal {
  animation: reveal 0.45s ease both;
}

@media (max-width: 1320px) {
  .card-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 980px) {
  .card-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 640px) {
  .card-grid {
    grid-template-columns: 1fr;
    grid-auto-rows: auto;
  }

  .ency-card {
    min-height: 0;
  }
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
</style>
