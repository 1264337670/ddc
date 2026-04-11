<script setup lang="ts">
import { ref } from 'vue'
import { useMindIsland } from '../composables/useMindIsland'

const { startAnalysis } = useMindIsland()

const showAuthorizeModal = ref(false)
const agreedDataAuth = ref(false)

function openAuthorizeModal() {
  agreedDataAuth.value = false
  showAuthorizeModal.value = true
}

function closeAuthorizeModal() {
  showAuthorizeModal.value = false
}

function confirmAndStart() {
  if (!agreedDataAuth.value) {
    return
  }
  showAuthorizeModal.value = false
  startAnalysis()
}
</script>

<template>
  <section class="analysis-page glass reveal">
    <h2>心理分析</h2>
    <div class="analysis-main">
      <img src="/assets/bg_fenxi.jpg" alt="心理分析" class="analysis-image" />
      <button class="primary" @click="openAuthorizeModal">一键开始心理分析</button>
    </div>

    <Teleport to="body">
      <div v-if="showAuthorizeModal" class="authorize-mask" @click.self="closeAuthorizeModal">
        <div class="authorize-modal glass">
          <h3>数据授权确认</h3>
          <img src="/assets/logo.png" alt="平台标识" class="authorize-logo" />

          <label class="agree-row">
            <input v-model="agreedDataAuth" type="checkbox" class="agree-check" />
            <span>同意授权数据</span>
          </label>

          <button class="confirm-btn" :disabled="!agreedDataAuth" @click="confirmAndStart">确认分析</button>
        </div>
      </div>
    </Teleport>
  </section>
</template>

<style scoped>
.analysis-page {
  border-radius: 26px;
  padding: 20px;
}

.glass {
  background: rgba(255, 255, 255, 0.52);
  border: 1px solid rgba(255, 255, 255, 0.7);
  box-shadow: 0 10px 30px rgba(55, 78, 120, 0.12);
  backdrop-filter: blur(14px);
}

.analysis-main {
  margin-top: 12px;
  min-height: 74vh;
  display: grid;
  place-items: center;
  gap: 16px;
}

.analysis-image {
  width: min(100%, 980px);
  height: min(62vh, 620px);
  border-radius: 20px;
  object-fit: cover;
  box-shadow: 0 16px 32px rgba(57, 83, 126, 0.18);
}

.primary {
  border: 0;
  border-radius: 999px;
  padding: 12px 20px;
  cursor: pointer;
  background: linear-gradient(120deg, #ff8ea8, #ffb27a);
  color: #fff;
  box-shadow: 0 10px 20px rgba(255, 141, 136, 0.32);
}

.authorize-mask {
  position: fixed;
  inset: 0;
  background: rgba(14, 24, 46, 0.32);
  display: grid;
  place-items: center;
  z-index: 40;
}

.authorize-modal {
  width: min(92vw, 420px);
  border-radius: 18px;
  padding: 20px;
  display: grid;
  justify-items: center;
  gap: 14px;
}

.authorize-modal h3 {
  margin: 0;
  color: #2f4f79;
}

.authorize-logo {
  width: 140px;
  height: 140px;
  object-fit: cover;
  border-radius: 12px;
  box-shadow: 0 10px 24px rgba(46, 68, 109, 0.16);
}

.agree-row {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: #355179;
  font-size: 1rem;
  cursor: pointer;
}

.agree-check {
  appearance: none;
  width: 16px;
  height: 16px;
  border: 2px solid #f29cb4;
  border-radius: 3px;
  background: transparent;
  display: inline-block;
  position: relative;
  cursor: pointer;
}

.agree-check:checked {
  background: #f8c8d6;
}

.agree-check:checked::after {
  content: '';
  position: absolute;
  left: 4px;
  top: 1px;
  width: 4px;
  height: 8px;
  border: solid #8d4d60;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

.confirm-btn {
  border: 0;
  border-radius: 999px;
  padding: 10px 22px;
  background: #f9cdd9;
  color: #8b4a5d;
  cursor: pointer;
  font-size: 1rem;
}

.confirm-btn:disabled {
  background: #f1e3e8;
  color: #b49ca5;
  cursor: not-allowed;
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
