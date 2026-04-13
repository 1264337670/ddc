<script setup lang="ts">
import { useMindIsland } from '../composables/useMindIsland'

const {
  isAuthOpen,
  authMode,
  loginForm,
  registerForm,
  captchaQuestion,
  authMessage,
  closeAuth,
  refreshCaptcha,
  submitLogin,
  submitRegister,
} = useMindIsland()

async function onLogin() {
  await submitLogin()
}

async function onRegister() {
  await submitRegister()
}
</script>

<template>
  <div v-if="isAuthOpen" class="modal-mask" @click.self="closeAuth">
    <div class="modal glass">
      <div class="switcher">
        <button :class="{ active: authMode === 'login' }" @click="authMode = 'login'">登录</button>
        <button :class="{ active: authMode === 'register' }" @click="authMode = 'register'">注册</button>
      </div>
      <p class="msg">{{ authMessage }}</p>
      <form v-if="authMode === 'login'" class="auth-form" @submit.prevent="onLogin">
        <input v-model="loginForm.account" placeholder="账号" />
        <input v-model="loginForm.password" type="password" placeholder="密码" />
        <div class="captcha-row">
          <input v-model="loginForm.captchaInput" placeholder="请输入验证码" />
          <button class="captcha-btn" type="button" @click="refreshCaptcha">{{ captchaQuestion }}</button>
        </div>
        <div class="action-row">
          <button class="primary" type="submit">进入心屿</button>
        </div>
      </form>
      <form v-else class="auth-form" @submit.prevent="onRegister">
        <input v-model="registerForm.account" placeholder="账号（必填）" />
        <input v-model="registerForm.password" type="password" placeholder="密码（必填，至少6位且含字母+数字）" />
        <input v-model="registerForm.confirmPassword" type="password" placeholder="确认密码（必填）" />
        <p class="password-tip">密码规则：至少6位，必须同时包含字母和数字。</p>
        <input v-model="registerForm.nickname" placeholder="昵称（必填）" />
        <input v-model="registerForm.xhsUrl" placeholder="小红书账号url（选填，用于后续心理分析）" />
        <div class="action-row">
          <button class="primary" type="submit">创建账号</button>
        </div>
      </form>
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
  padding: 20px;
  min-height: 430px;
  display: flex;
  flex-direction: column;
}

.glass {
  background: rgba(255, 255, 255, 0.52);
  border: 1px solid rgba(255, 255, 255, 0.7);
  box-shadow: 0 10px 30px rgba(55, 78, 120, 0.12);
  backdrop-filter: blur(14px);
}

.switcher {
  display: flex;
  gap: 10px;
  margin-bottom: 12px;
}

.switcher button,
.primary {
  border: 0;
  border-radius: 999px;
  padding: 10px 15px;
  cursor: pointer;
}

.switcher button.active {
  background: linear-gradient(120deg, #ff8ea8, #ffb27a);
  color: #fff;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
  flex: 1;
}

.auth-form input {
  border: 0;
  border-radius: 10px;
  padding: 13px;
  font-size: 0.95rem;
}

.primary {
  background: linear-gradient(120deg, #ff8ea8, #ffb27a);
  color: #fff;
  box-shadow: 0 10px 20px rgba(255, 141, 136, 0.32);
}

.captcha-row {
  display: grid;
  grid-template-columns: minmax(120px, 170px) auto;
  gap: 12px;
  justify-content: start;
}

.captcha-btn {
  border: 0;
  border-radius: 10px;
  padding: 0 12px;
  background: rgba(255, 255, 255, 0.7);
  cursor: pointer;
  color: #2f4f7d;
  font-size: 1.1rem;
  font-weight: 700;
}

.action-row {
  margin-top: auto;
  padding-top: 14px;
}

.action-row .primary {
  width: 100%;
}

.msg {
  min-height: 28px;
  margin: 0 0 8px;
  color: #d65b75;
}

.password-tip {
  margin: -8px 2px 0;
  color: #6b7f9f;
  font-size: 0.85rem;
}
</style>
