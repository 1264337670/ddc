<script setup lang="ts">
import { onBeforeUnmount } from 'vue'
import AnalysisDialog from './components/AnalysisDialog.vue'
import AuthDialog from './components/AuthDialog.vue'
import GlobalMessage from './components/GlobalMessage.vue'
import TopNavBar from './components/TopNavBar.vue'
import { useMindIsland } from './composables/useMindIsland'

const { stopAllTimers } = useMindIsland()

onBeforeUnmount(() => {
  stopAllTimers()
})
</script>

<template>
  <div class="page-shell">
    <div class="bg-orb orb-a"></div>
    <div class="bg-orb orb-b"></div>
    <TopNavBar />
    <main class="content">
      <RouterView />
    </main>
    <AuthDialog />
    <AnalysisDialog />
    <GlobalMessage />
  </div>
</template>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Ma+Shan+Zheng&family=Noto+Serif+SC:wght@400;600;700&display=swap');

.page-shell {
  min-height: 100vh;
  padding: 20px;
  position: relative;
  overflow: hidden;
  background:
    linear-gradient(rgba(246, 248, 255, 0.76), rgba(246, 248, 255, 0.76)),
    url('/assets/bg1.jpg') center / cover no-repeat;
  font-family: 'Noto Serif SC', serif;
  color: #1f2a44;
}

.bg-orb {
  position: absolute;
  border-radius: 999px;
  filter: blur(24px);
  opacity: 0.55;
  animation: float 7s ease-in-out infinite;
}

.orb-a {
  width: 220px;
  height: 220px;
  background: #ffb2c2;
  top: -40px;
  left: -40px;
}

.orb-b {
  width: 260px;
  height: 260px;
  background: #9dc6ff;
  right: -70px;
  bottom: 18%;
  animation-delay: 0.7s;
}

.content {
  margin-top: 18px;
}

@keyframes float {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}
</style>
