<script setup lang="ts">
import { computed } from 'vue'
import { useMindIsland } from '../composables/useMindIsland'

const {
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
  analysisWordcloudImageUrl,
  analysisTitle,
  showAnalysisWordcloud,
  showAnalysisResult,
  exportAnalysisReportPdf,
  closeAnalysis,
} = useMindIsland()

const ringRadius = 54
const ringCircumference = 2 * Math.PI * ringRadius

const scoreDisplay = computed(() => {
  const raw = Number(analysisScore.value ?? 0)
  const normalized = raw <= 1 ? raw * 100 : raw
  const percent = Math.max(0, Math.min(100, normalized))
  const offset = ringCircumference * (1 - percent / 100)
  return {
    percent: Math.round(percent),
    offset,
  }
})
</script>

<template>
  <div v-if="analysisOpen" class="modal-mask">
    <div class="modal glass" :class="{ 'demo-modal': analysisDemoMode }">
      <div class="modal-head">
        <h3>心理分析中枢</h3>
        <button type="button" class="close-btn" @click="closeAnalysis">关闭</button>
      </div>
      <p v-if="analyzing">正在导入情绪数据与行为节律...</p>
      <div v-if="analyzing && analysisDemoMode && analysisDemoImages.length" class="demo-carousel">
        <div class="demo-carousel-bg"></div>
        <img :src="analysisDemoImages[analysisDemoImageIndex]" alt="分析演示轮播" />
      </div>
      <div class="progress-track">
        <div class="progress-bar" :style="{ width: `${analysisProgress}%` }"></div>
      </div>
      <div v-if="!analyzing" class="analysis-result">
        <div v-if="analysisDemoMode" class="demo-actions">
          <button v-if="analysisWordcloudImageUrl" type="button" class="action-btn" @click="showAnalysisWordcloud">查看分析词云</button>
          <button type="button" class="action-btn" @click="showAnalysisResult">查看分析结果</button>
        </div>

        <div v-if="analysisDemoMode && analysisDemoWordcloudVisible" class="wordcloud-wrap">
          <img :src="analysisWordcloudImageUrl" alt="分析词云" class="wordcloud" />
          <p class="wordcloud-note">基于小红书文本生成的高频词云</p>
        </div>

        <template v-if="!analysisDemoMode || analysisDemoResultVisible">
          <div id="analysis-report-export">
          <h4>{{ analysisTitle }}</h4>
          <div v-if="analysisScore !== null" class="score-gauge-wrap">
            <div class="score-gauge-card">
              <svg class="score-gauge" viewBox="0 0 140 140" role="img" aria-label="心理健康分图表">
                <circle class="gauge-track" cx="70" cy="70" :r="ringRadius" />
                <circle
                  class="gauge-progress"
                  cx="70"
                  cy="70"
                  :r="ringRadius"
                  :stroke-dasharray="ringCircumference"
                  :stroke-dashoffset="scoreDisplay.offset"
                />
              </svg>
              <div class="gauge-center">
                <p class="gauge-percent">{{ scoreDisplay.percent }}%</p>
              </div>
            </div>

            <div class="score-side">
              <div class="score-level-legend" aria-label="分数区间图例">
                <div class="legend-row">
                  <span class="legend-color red"></span>
                  <span class="legend-label">0-49 风险高</span>
                </div>
                <div class="legend-row">
                  <span class="legend-color orange"></span>
                  <span class="legend-label">50-59 需关注</span>
                </div>
                <div class="legend-row">
                  <span class="legend-color blue"></span>
                  <span class="legend-label">60-79 较稳定</span>
                </div>
                <div class="legend-row">
                  <span class="legend-color green"></span>
                  <span class="legend-label">80-100 状态好</span>
                </div>
              </div>

              <div v-if="analysisDemoMode" class="user-avatar-card">
                <img src="/ava.png" alt="用户头像" class="user-avatar" />
                <p class="user-name">小林</p>
              </div>
            </div>
          </div>
          <p v-if="analysisRiskLabel" class="risk-line">风险判断：{{ analysisRiskLabel === 'Clinical' ? '存在抑郁风险' : '心理较健康' }}</p>
          <p>{{ analysisAdvice }}</p>
          <p class="warm">温馨寄语：你值得被温柔对待，也值得慢慢成长。</p>
          </div>
          <button type="button" class="export-report-btn" @click="exportAnalysisReportPdf">导出心理健康分析报告</button>
        </template>
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
  position: relative;
  width: min(92vw, 480px);
  border-radius: 18px;
  padding: 18px;
  overflow: hidden;
}

.modal::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image: url('/assets/bg1.jpg');
  background-size: cover;
  background-position: center;
  filter: blur(10px);
  transform: scale(1.08);
  opacity: 0.4;
  z-index: 0;
}

.modal > * {
  position: relative;
  z-index: 1;
}

.demo-modal {
  width: min(96vw, calc(920px - 2cm));
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
  background: rgba(255, 255, 255, 0.42);
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

.demo-carousel {
  position: relative;
  margin: 10px 0;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.75);
  min-height: 240px;
  display: grid;
  place-items: center;
}

.demo-carousel-bg {
  position: absolute;
  inset: 0;
  background-image: url('/assets/bg1.jpg');
  background-size: cover;
  background-position: center;
  filter: blur(10px);
  transform: scale(1.08);
  opacity: 0.72;
}

.demo-carousel img {
  position: relative;
  z-index: 1;
  display: block;
  width: 100%;
  max-height: 62vh;
  height: auto;
  object-fit: contain;
  background: rgba(255, 255, 255, 0.18);
}

.analysis-result {
  margin-top: 10px;
}

.demo-actions {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}

.action-btn {
  border: 0;
  border-radius: 10px;
  padding: 8px 12px;
  cursor: pointer;
  background: linear-gradient(120deg, rgba(255, 142, 168, 0.9), rgba(132, 186, 255, 0.9));
  color: #fff;
  font-weight: 600;
}

.wordcloud-wrap {
  margin-bottom: 10px;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.75);
}

.wordcloud {
  display: block;
  width: 100%;
  height: auto;
}

.wordcloud-note {
  margin: 8px 0 2px;
  font-size: 12px;
  line-height: 1.4;
  color: rgba(88, 96, 112, 0.78);
  text-align: center;
}

.score-gauge-wrap {
  display: flex;
  align-items: center;
  gap: 16px;
  margin: 8px 0 12px;
}

.score-gauge-card {
  position: relative;
  width: 160px;
  height: 160px;
}

.score-gauge {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.gauge-track {
  fill: none;
  stroke: rgba(47, 79, 121, 0.2);
  stroke-width: 16;
}

.gauge-progress {
  fill: none;
  stroke: url(#gaugeGradient);
  stroke-width: 16;
  stroke-linecap: round;
  transition: stroke-dashoffset 0.5s ease;
}

.score-gauge .gauge-progress {
  stroke: #4d8ef7;
}

.gauge-center {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  text-align: center;
}

.gauge-percent {
  margin: 0;
  font-size: 28px;
  line-height: 1;
  color: #2f4f79;
  font-weight: 800;
  transform: translateY(0.1cm);
}

.score-level-legend {
  display: grid;
  gap: 8px;
  margin-top: 0.5cm;
}

.score-side {
  display: flex;
  align-items: flex-start;
  gap: 4cm;
  margin-left: 2cm;
}

.user-avatar-card {
  display: grid;
  justify-items: center;
  gap: 6px;
  margin-left: -1cm;
}

.user-avatar {
  width: 96px;
  height: 96px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid rgba(255, 255, 255, 0.9);
  box-shadow: 0 4px 12px rgba(47, 79, 121, 0.2);
}

.user-name {
  margin: 0;
  text-align: center;
  color: #2f4f79;
  font-size: 14px;
  font-weight: 700;
}

.legend-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.legend-color {
  display: inline-block;
  width: 28px;
  height: 14px;
  border-radius: 999px;
}

.legend-color.red {
  background: #ef4444;
}

.legend-color.orange {
  background: #f59e0b;
}

.legend-color.blue {
  background: #3b82f6;
}

.legend-color.green {
  background: #22c55e;
}

.legend-label {
  color: #3e618f;
  font-size: 13px;
}

.risk-line {
  color: #3e618f;
}

.warm {
  color: #4d648f;
}

.export-report-btn {
  margin-top: 12px;
  width: 100%;
  border: 1px solid rgba(122, 150, 196, 0.4);
  border-radius: 12px;
  padding: 10px 14px;
  background: linear-gradient(120deg, rgba(231, 240, 255, 0.85), rgba(238, 247, 255, 0.9));
  color: #2f4f79;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.export-report-btn:hover {
  background: linear-gradient(120deg, rgba(222, 234, 255, 0.9), rgba(232, 244, 255, 0.95));
  border-color: rgba(122, 150, 196, 0.55);
}
</style>
