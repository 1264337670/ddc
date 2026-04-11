<script setup lang="ts">
import { useMindIsland } from '../composables/useMindIsland'

const { messageQueue } = useMindIsland()
</script>

<template>
  <div class="message-wrap">
    <div
      v-for="item in messageQueue"
      :key="item.id"
      class="msg-item"
      :class="item.type"
    >
      <span class="msg-icon" aria-hidden="true">{{ item.type === 'success' ? '✓' : '!' }}</span>
      <div class="msg-content">
        <strong>{{ item.type === 'success' ? '操作成功' : '提示' }}</strong>
        <p>{{ item.text }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.message-wrap {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 9999;
  display: grid;
  gap: 8px;
  pointer-events: none;
}

.msg-item {
  min-width: 260px;
  max-width: min(78vw, 420px);
  padding: 10px 14px;
  border-radius: 12px;
  color: #2b3f57;
  box-shadow: 0 12px 28px rgba(26, 39, 64, 0.16);
  border: 1px solid rgba(255, 255, 255, 0.85);
  display: flex;
  align-items: center;
  gap: 10px;
  backdrop-filter: blur(8px);
}

.msg-item.success {
  background: linear-gradient(180deg, rgba(244, 255, 249, 0.96), rgba(226, 248, 238, 0.96));
  border-left: 4px solid #38b46b;
}

.msg-item.error {
  background: linear-gradient(180deg, rgba(255, 247, 247, 0.96), rgba(255, 232, 232, 0.96));
  border-left: 4px solid #e75b57;
}

.msg-icon {
  width: 22px;
  height: 22px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  flex: 0 0 auto;
}

.msg-item.success .msg-icon {
  background: #38b46b;
  color: #fff;
}

.msg-item.error .msg-icon {
  background: #e75b57;
  color: #fff;
}

.msg-content {
  display: grid;
  gap: 2px;
}

.msg-content strong {
  font-size: 0.92rem;
  letter-spacing: 0.4px;
}

.msg-content p {
  margin: 0;
  font-size: 0.95rem;
}
</style>
