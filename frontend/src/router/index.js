import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../components/Dashboard.vue'
import EquipmentList from '../components/equipment/EquipmentList.vue'
import UserList from '../components/users/UserList.vue'
import SealList from '../components/seals/SealList.vue'
import HistoryTabs from '../components/history/HistoryTabs.vue'
import FloorPlan from '../components/floorplan/FloorPlan.vue'

const routes = [
  {
    path: '/',
    name: 'dashboard',
    component: Dashboard,
    meta: { label: '대시보드' }
  },
  {
    path: '/equipment',
    name: 'equipment',
    component: EquipmentList,
    meta: { label: '장비 관리' }
  },
  {
    path: '/users',
    name: 'users',
    component: UserList,
    meta: { label: '사용자 관리' }
  },
  {
    path: '/users/:userId',
    name: 'user-detail',
    component: UserList,
    meta: { label: '사용자 관리' },
    props: true
  },
  {
    path: '/seals',
    name: 'seals',
    component: SealList,
    meta: { label: '보안씰 관리' }
  },
  {
    path: '/history',
    name: 'history',
    component: HistoryTabs,
    meta: { label: '이력 관리' }
  },
  {
    path: '/floorplan',
    name: 'floorplan',
    component: FloorPlan,
    meta: { label: '배치도' }
  },
  {
    // 잘못된 경로는 대시보드로 리다이렉트
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router