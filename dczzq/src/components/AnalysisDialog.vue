<script setup lang="ts">
import { useMindIsland } from '../composables/useMindIsland'

const {
  analysisOpen,
  analyzing,
  analysisProgress,
  analysisAdvice,
  analysisScore,
  analysisRiskLabel,
  analysisTitle,
  closeAnalysis,
} = useMindIsland()
</script>

<template>
  <div v-if="analysisOpen" class="modal-mask">
    <div class="modal glass">
      <div class="modal-head">
        <h3>心理分析中枢</h3>
        <button type="button" class="close-btn" @click="closeAnalysis">关闭</button>
      </div>
      <p v-if="analyzing">正在导入情绪数据与行为节律...</p>
      <div class="progress-track">
        <div class="progress-bar" :style="{ width: `${analysisProgress}%` }"></div>
      </div>
      <div v-if="!analyzing" class="analysis-result">
        <h4>{{ analysisTitle }}</h4>
        <p v-if="analysisScore !== null" class="score-line">心理健康分：{{ analysisScore }}</p>
        <p v-if="analysisRiskLabel" class="risk-line">风险判断：{{ analysisRiskLabel === 'Clinical' ? '存在抑郁风险' : '心理较健康' }}</p>
        <p>{{ analysisAdvice }}</p>
        <p class="warm">温馨寄语：你值得被温柔对待，也值得慢慢成长。</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(15, 20, 43, 0.35);
  display: grid;
  place-items: center;
  z-index: 20;
}

.modal {
  width: min(92vw, 480px);
  border-radius: 18px;
  padding: 18px;
}

.modal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.modal-head h3 {
  margin: 0;
}

.close-btn {
  border: 0;
  border-radius: 999px;
  padding: 6px 12px;
  background: rgba(255, 163, 175, 0.3);
  color: #7a3f53;
  cursor: pointer;
}

.glass {
  background: rgba(255, 255, 255, 0.52);
  border: 1px solid rgba(255, 255, 255, 0.7);
  box-shadow: 0 10px 30px rgba(55, 78, 120, 0.12);
  backdrop-filter: blur(14px);
}

.progress-track {
  width: 100%;
  height: 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.55);
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(120deg, #ff8ea8, #84baff);
  transition: width 0.2s ease;
}

.analysis-result {
  margin-top: 10px;
}

.score-line {
  color: #2f4f79;
  font-weight: 700;
}

.risk-line {
  color: #3e618f;
}

.warm {
  color: #4d648f;
}
</style>
