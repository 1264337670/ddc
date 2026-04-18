import { createRouter, createWebHistory } from 'vue-router'
import EncyclopediaView from '../pages/EncyclopediaView.vue'
import AdminView from '../pages/AdminView.vue'
import HomeView from '../pages/HomeView.vue'
import MentorView from '../pages/MentorView.vue'
import ProfileView from '../pages/ProfileView.vue'
import PsychologyAnalysisView from '../pages/PsychologyAnalysisView.vue'
import RelaxGamesView from '../pages/RelaxGamesView.vue'
import TreeHoleView from '../pages/TreeHoleView.vue'
import TreeWallView from '../pages/TreeWallView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'home', component: HomeView },
    { path: '/analysis', name: 'analysis', component: PsychologyAnalysisView },
    { path: '/encyclopedia', name: 'encyclopedia', component: EncyclopediaView },
    { path: '/mentor', name: 'mentor', component: MentorView },
    { path: '/relax', name: 'relax', component: RelaxGamesView },
    { path: '/tree-hole', name: 'tree-hole', component: TreeHoleView },
    { path: '/tree-hole/:treeSlug', name: 'tree-wall', component: TreeWallView },
    { path: '/profile', name: 'profile', component: ProfileView },
    { path: '/admin', name: 'admin', component: AdminView },
  ],
})

export default router
