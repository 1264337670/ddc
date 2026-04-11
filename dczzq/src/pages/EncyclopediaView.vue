<script setup lang="ts">
import { useMindIsland } from '../composables/useMindIsland'

const { encyclopediaItems } = useMindIsland()

const cardImages = {
  '抑郁情绪': '/assets/youyu.jpg',
  '焦虑紧张': '/assets/jiaolv.jpg',
  '睡眠困扰': '/assets/sleep.jpg',
  '内耗反刍': '/assets/neihao.jpg',
} as const
</script>

<template>
  <section class="grid-section reveal">
    <h2>心理百科</h2>
    <div class="card-grid">
      <article v-for="item in encyclopediaItems" :key="item.title" class="ency-card glass">
        <div class="card-copy">
          <h3>{{ item.emoji }} {{ item.title }}</h3>
          <p>{{ item.intro }}</p>
          <ul>
            <li v-for="tip in item.tips" :key="tip">{{ tip }}</li>
          </ul>
        </div>
        <div class="card-image-shell">
          <img class="card-image" :src="cardImages[item.title as keyof typeof cardImages]" :alt="item.title" />
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

.card-grid {
  margin-top: 14px;
  display: grid;
  gap: 14px;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}

.ency-card {
  border-radius: 18px;
  padding: 16px;
  display: grid;
  grid-template-rows: auto 1fr;
  gap: 12px;
  overflow: hidden;
}

.card-copy {
  align-self: start;
}

.card-copy h3 {
  margin: 0;
  font-family: 'STKaiti', 'KaiTi', serif;
  font-size: 1.5rem;
  font-weight: 700;
  letter-spacing: 0.5px;
  color: #2e4a74;
}

.card-copy p {
  margin-top: 10px;
  color: #4e668d;
  line-height: 1.75;
  font-family: 'FangSong', serif;
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
  height: 560px;
  overflow: hidden;
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
