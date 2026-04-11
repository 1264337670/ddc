<script setup lang="ts">
import { useRouter } from 'vue-router'

interface TreeItem {
  name: string
  slug: string
  image: string
}

const router = useRouter()

const trees: TreeItem[] = [
  { name: '安绪树', slug: 'anxu', image: '/assets/tree1.png' },
  { name: '百态树', slug: 'baitai', image: '/assets/tree2.png' },
  { name: '暖光树', slug: 'nuanguang', image: '/assets/tree3.png' },
]

function enterTreeForum(tree: TreeItem) {
  router.push(`/tree-hole/${tree.slug}`)
}
</script>

<template>
  <section class="tree-hole reveal">
    <h2>安全树洞</h2>
    <p class="desc">选择一棵树，进入匿名分享与互助社区。内容采用前端 mock 审核流，后续可直接接入后端与数据库。</p>
    <div class="tree-row">
      <button
        v-for="tree in trees"
        :key="tree.slug"
        class="tree-card"
        type="button"
        @click="enterTreeForum(tree)"
      >
        <img class="tree-image" :src="tree.image" :alt="tree.name" />
        <span class="tree-name">{{ tree.name }}</span>
      </button>
    </div>
  </section>
</template>

<style scoped>
.tree-hole {
  border-radius: 28px;
  padding: 28px 28px 22px;
  background: radial-gradient(circle at top, rgba(84, 102, 152, 0.62), rgba(16, 23, 48, 0.92));
  color: #eef3ff;
}

h2 {
  margin: 0;
  font-size: clamp(2rem, 4vw, 2.5rem);
}

.desc {
  margin-top: 12px;
  color: #cfddff;
  font-size: 1.06rem;
}

.tree-row {
  width: min(100%, 1100px);
  margin: 20px auto 8px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 22px;
  align-items: end;
}

.tree-card {
  border: 0;
  background: transparent;
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  transition: transform 0.35s ease;
  padding: 0;
}

.tree-image {
  width: min(100%, 360px);
  height: auto;
  display: block;
  margin: 0 auto;
  filter: drop-shadow(0 10px 28px rgba(112, 196, 159, 0.45));
  transition: transform 0.35s ease, filter 0.35s ease;
}

.tree-name {
  margin-top: 10px;
  color: #f5f8ff;
  font-size: clamp(1.2rem, 2.2vw, 1.55rem);
  font-weight: 800;
  letter-spacing: 1px;
  text-shadow: 0 0 16px rgba(169, 206, 255, 0.5);
}

.tree-row .tree-card:first-child .tree-image {
  transform: translateX(-18px) scale(1.08);
  transform-origin: center bottom;
}

.tree-row .tree-card:nth-child(2) .tree-image {
  transform: scale(1.08);
  transform-origin: center bottom;
}

.tree-row .tree-card:last-child .tree-image {
  transform: translateX(18px) scale(1.08);
  transform-origin: center bottom;
}

.tree-row .tree-card:hover .tree-image {
  transform: translateY(-24px) scale(1.27);
  filter: drop-shadow(0 18px 30px rgba(112, 196, 159, 0.5));
}

.tree-row .tree-card:hover .tree-name {
  color: #ffffff;
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
  .tree-row {
    grid-template-columns: 1fr;
    gap: 16px;
  }

  .tree-row:hover .tree-card .tree-image,
  .tree-row .tree-card:hover .tree-image,
  .tree-row .tree-card:first-child .tree-image,
  .tree-row .tree-card:nth-child(2) .tree-image,
  .tree-row .tree-card:last-child .tree-image {
    transform: scale(1.03);
  }
}
</style>
