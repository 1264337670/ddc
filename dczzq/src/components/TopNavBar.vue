<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMindIsland, type NavKey } from '../composables/useMindIsland'

const route = useRoute()
const router = useRouter()

const { navItems, routeMap, currentUser, openAuth, logout } = useMindIsland()
const menuRef = ref<HTMLElement | null>(null)
const menuOpen = ref(false)

const activeNav = computed<NavKey>(() => {
  const found = navItems.find((item) => {
    const base = routeMap[item]
    if (base === '/') {
      return route.path === '/'
    }
    return route.path === base || route.path.startsWith(`${base}/`)
  })
  return found || '首页'
})

const avatarText = computed(() => currentUser.value?.nickname.slice(0, 1) || '心')
const hasAvatar = computed(() => Boolean(currentUser.value?.avatar))

function navigate(item: NavKey) {
  router.push(routeMap[item])
}

function openProfile() {
  menuOpen.value = false
  router.push('/profile')
}

function toggleUserMenu() {
  if (!currentUser.value) {
    openAuth()
    return
  }
  menuOpen.value = !menuOpen.value
}

function handleLogout() {
  menuOpen.value = false
  logout()
}

function clickOutside(event: MouseEvent) {
  const target = event.target as Node
  if (!menuRef.value || menuRef.value.contains(target)) {
    return
  }
  menuOpen.value = false
}

onMounted(() => {
  document.addEventListener('click', clickOutside)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', clickOutside)
})
</script>

<template>
  <header class="top-nav glass">
    <div class="brand">
      <span class="brand-dot"></span>
      <strong>心屿</strong>
    </div>
    <nav class="menu">
      <button
        v-for="item in navItems"
        :key="item"
        class="nav-btn"
        :class="{ active: activeNav === item }"
        @click="navigate(item)"
      >
        {{ item }}
      </button>
    </nav>
    <div ref="menuRef" class="user-menu">
      <button class="avatar-btn" @click="toggleUserMenu">
        <span v-if="currentUser" class="avatar-circle">
          <img v-if="hasAvatar" :src="currentUser?.avatar" alt="头像" class="avatar-image" />
          <span v-else>{{ avatarText }}</span>
        </span>
        <span>{{ currentUser ? currentUser.nickname : '请登录' }}</span>
      </button>
      <div v-if="currentUser && menuOpen" class="dropdown glass">
        <button class="drop-item" @click="openProfile">个人主页</button>
        <button class="drop-item" @click="handleLogout">退出登录</button>
      </div>
    </div>
  </header>
</template>

<style scoped>
.glass {
  background: rgba(255, 255, 255, 0.52);
  border: 1px solid rgba(255, 255, 255, 0.7);
  box-shadow: 0 10px 30px rgba(55, 78, 120, 0.12);
  backdrop-filter: blur(14px);
}

.top-nav {
  position: sticky;
  top: 0;
  z-index: 10;
  border-radius: 20px;
  padding: 12px;
  display: grid;
  grid-template-columns: 120px 1fr 180px;
  gap: 10px;
  align-items: center;
}

.brand {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: 'Ma Shan Zheng', cursive;
  font-size: 2rem;
}

.brand-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: linear-gradient(120deg, #ff8ea8, #ffb27a);
}

.menu {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
}

.nav-btn,
.avatar-btn {
  border: 0;
  border-radius: 999px;
  padding: 10px 15px;
  cursor: pointer;
  transition: transform 0.25s ease, box-shadow 0.25s ease, background 0.25s ease;
}

.nav-btn {
  background: rgba(255, 255, 255, 0.45);
  color: #1f2a44;
  font-size: 1.03rem;
  font-weight: 600;
}

.nav-btn.active {
  background: linear-gradient(120deg, #ff8ea8, #ffb27a);
  color: #fff;
  box-shadow: 0 8px 16px rgba(255, 142, 168, 0.35);
}

.avatar-btn {
  justify-self: end;
  display: flex;
  align-items: center;
  gap: 10px;
  background: linear-gradient(120deg, rgba(255, 142, 168, 0.86), rgba(132, 186, 255, 0.82));
  color: #fff;
  font-size: 1.02rem;
}

.avatar-circle {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: rgba(255, 255, 255, 0.34);
  overflow: hidden;
}

.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.user-menu {
  justify-self: end;
  position: relative;
}

.dropdown {
  position: absolute;
  right: 0;
  top: calc(100% + 8px);
  min-width: 130px;
  border-radius: 12px;
  padding: 8px;
  display: grid;
  gap: 6px;
}

.drop-item {
  border: 0;
  background: rgba(255, 255, 255, 0.55);
  border-radius: 9px;
  padding: 8px 10px;
  text-align: left;
  cursor: pointer;
  color: #244264;
}

@media (max-width: 860px) {
  .top-nav {
    grid-template-columns: 1fr;
  }

  .brand,
  .user-menu,
  .avatar-btn {
    justify-self: center;
  }
}
</style>
