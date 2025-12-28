<template>
  <div id="app">
    <header class="header">
      <h1>전산장비 관리 시스템</h1>
      <nav>
        <button 
          v-for="menu in menus" 
          :key="menu.key"
          @click="currentView = menu.key" 
          :class="{ active: currentView === menu.key }"
        >
          {{ menu.label }}
        </button>
      </nav>
    </header>

    <main class="main-content">
      <Dashboard v-if="currentView === 'dashboard'" />
      <EquipmentList v-if="currentView === 'equipment'" />
      <UserList 
        v-if="currentView === 'users'" 
        ref="userList"
        :initial-user-id="selectedUserId"
      />
      <SealList v-if="currentView === 'seals'" />
      <HistoryTabs v-if="currentView === 'history'" />
      <FloorPlan 
        v-if="currentView === 'floorplan'" 
        @navigate="handleNavigate"
      />
    </main>
  </div>
</template>

<script>
import Dashboard from './components/Dashboard.vue'
import EquipmentList from './components/equipment/EquipmentList.vue'
import UserList from './components/users/UserList.vue'
import SealList from './components/seals/SealList.vue'
import HistoryTabs from './components/history/HistoryTabs.vue'
import FloorPlan from './components/floorplan/FloorPlan.vue'

export default {
  name: 'App',
  components: {
    Dashboard,
    EquipmentList,
    UserList,
    SealList,
    HistoryTabs,
    FloorPlan
  },
  data() {
    return {
      currentView: 'dashboard',
      selectedUserId: null,
      menus: [
        { key: 'dashboard', label: '대시보드' },
        { key: 'equipment', label: '장비 관리' },
        { key: 'users', label: '사용자 관리' },
        { key: 'seals', label: '보안씰 관리' },
        { key: 'history', label: '이력 관리' },
        { key: 'floorplan', label: '배치도' }
      ]
    }
  },
  methods: {
    handleNavigate(view, params) {
      this.currentView = view
      
      // 사용자 관리 페이지로 이동 시 특정 사용자 선택
      if (view === 'users' && params?.userId) {
        this.selectedUserId = params.userId
        // 컴포넌트가 마운트된 후 사용자 선택
        this.$nextTick(() => {
          if (this.$refs.userList) {
            this.$refs.userList.selectUserById(params.userId)
          }
        })
      } else {
        this.selectedUserId = null
      }
    }
  }
}
</script>

<style>
@import './assets/styles.css';
</style>
