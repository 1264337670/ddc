<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useMindIsland } from '../composables/useMindIsland'

const { currentUser, profileForm, uploadAvatar, updateProfile, syncProfileFromCurrentUser } = useMindIsland()
const layoutRef = ref<HTMLElement | null>(null)
const leftCardRef = ref<HTMLElement | null>(null)
const rightCardRef = ref<HTMLElement | null>(null)

const avatarSrc = computed(() => profileForm.avatar || currentUser.value?.avatar || '')

function onAvatarFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) {
    return
  }
  const reader = new FileReader()
  reader.onload = () => {
    const result = typeof reader.result === 'string' ? reader.result : ''
    if (!result) {
      return
    }
    uploadAvatar(result)
  }
  reader.readAsDataURL(file)
}

function logProfileLayout(reason: string) {
  const wrapperRect = layoutRef.value?.getBoundingClientRect()
  const leftRect = leftCardRef.value?.getBoundingClientRect()
  const rightRect = rightCardRef.value?.getBoundingClientRect()
  const overlap = !!(leftRect && rightRect && leftRect.right > rightRect.left)
  const gap = leftRect && rightRect ? Number((rightRect.left - leftRect.right).toFixed(2)) : null

  console.info('[ProfileLayoutDebug]', JSON.stringify({
    reason,
    viewport: { width: window.innerWidth, height: window.innerHeight },
    wrapper: wrapperRect ? { left: wrapperRect.left, right: wrapperRect.right, width: wrapperRect.width } : null,
    left: leftRect ? { left: leftRect.left, right: leftRect.right, width: leftRect.width } : null,
    right: rightRect ? { left: rightRect.left, right: rightRect.right, width: rightRect.width } : null,
    gap,
    overlap,
    timestamp: new Date().toISOString(),
  }))
}

function onResize() {
  logProfileLayout('window_resize')
}

onMounted(() => {
  syncProfileFromCurrentUser()
  nextTick(() => logProfileLayout('mounted'))
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
})
</script>

<template>
  <section class="profile-page reveal">
    <h2>个人主页</h2>
    <div ref="layoutRef" class="profile-layout">
      <article ref="leftCardRef" class="left-card glass">
        <h3>个人资料</h3>
        <label>
          昵称
          <input v-model="profileForm.nickname" placeholder="请输入昵称" />
        </label>
        <label>
          邮箱
          <input v-model="profileForm.email" placeholder="请输入邮箱" />
        </label>
        <label>
          性别
          <select v-model="profileForm.gender">
            <option value="">请选择</option>
            <option value="女">女</option>
            <option value="男">男</option>
            <option value="其他">其他</option>
          </select>
        </label>
        <label>
          电话号码
          <input v-model="profileForm.phone" placeholder="请输入电话号码" />
        </label>
        <label>
          个性签名
          <textarea v-model="profileForm.signature" rows="4" placeholder="写一句介绍自己吧"></textarea>
        </label>
        <label>
          小红书账号url
          <input v-model="profileForm.xhsUrl" placeholder="可选" />
        </label>
        <button class="primary" @click="updateProfile">保存资料</button>
      </article>

      <article ref="rightCardRef" class="right-card glass">
        <div class="avatar-wrap">
          <img v-if="avatarSrc" :src="avatarSrc" alt="头像" class="avatar" />
          <div v-else class="avatar fallback">心</div>
          <label class="upload-btn">
            上传头像
            <input type="file" accept="image/*" @change="onAvatarFileChange" />
          </label>
        </div>
        <div class="meta">
          <h3>{{ profileForm.nickname || currentUser?.nickname || '未设置昵称' }}</h3>
          <p>账号：{{ currentUser?.account || '未登录' }}</p>
        </div>
      </article>
    </div>
  </section>
</template>

<style scoped>
.profile-page {
  border-radius: 26px;
  padding: 20px;
}

.profile-layout {
  --avatar-card-offset-x: 50px;
  margin: 12px auto 0;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(280px, 320px);
  gap: 18px;
  width: min(100%, 1300px);
  align-items: start;
}

.glass {
  background: rgba(255, 255, 255, 0.52);
  border: 1px solid rgba(255, 255, 255, 0.7);
  box-shadow: 0 10px 30px rgba(55, 78, 120, 0.12);
  backdrop-filter: blur(14px);
}

.left-card,
.right-card {
  border-radius: 18px;
  padding: 16px;
}

.left-card {
  display: grid;
  gap: 12px;
  justify-items: center;
  width: 100%;
  min-width: 0;
}

.left-card label {
  display: grid;
  gap: 6px;
  color: #355179;
  width: 78%;
}

.left-card input,
.left-card select,
.left-card textarea {
  border: 0;
  border-radius: 10px;
  padding: 14px 12px;
  font-size: 1.02rem;
  background: rgba(255, 255, 255, 0.82);
}

.right-card {
  display: grid;
  align-content: start;
  gap: 12px;
  width: 100%;
  max-width: 320px;
  box-sizing: border-box;
  justify-self: end;
  align-self: start;
  padding: 24px;
  transform: translateX(var(--avatar-card-offset-x));
}

.avatar-wrap {
  display: grid;
  gap: 14px;
  justify-items: center;
}

.avatar {
  width: 132px;
  height: 132px;
  border-radius: 50%;
  object-fit: cover;
  border: 3px solid rgba(255, 255, 255, 0.85);
}

.avatar.fallback {
  display: grid;
  place-items: center;
  font-size: 2rem;
  color: #fff;
  background: linear-gradient(120deg, #ff8ea8, #84baff);
}

.upload-btn {
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.82);
  padding: 8px 14px;
  cursor: pointer;
}

.upload-btn input {
  display: none;
}

.meta h3 {
  margin: 0;
  font-size: 1.7rem;
}

.meta p {
  margin: 6px 0 0;
  color: #506d96;
  font-size: 1.15rem;
}

.primary {
  border: 0;
  border-radius: 999px;
  padding: 10px 16px;
  cursor: pointer;
  background: linear-gradient(120deg, #ff8ea8, #ffb27a);
  color: #fff;
  box-shadow: 0 10px 20px rgba(255, 141, 136, 0.32);
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

@media (max-width: 860px) {
  .profile-layout {
    grid-template-columns: 1fr;
    gap: 14px;
  }

  .right-card {
    width: 100%;
    transform: none;
  }

  .left-card label {
    width: 88%;
  }
}
</style>
