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
      <UserList v-if="currentView === 'users'" />
      <SealList v-if="currentView === 'seals'" />
      <HistoryTabs v-if="currentView === 'history'" />
    </main>
  </div>
</template>

<script>
import Dashboard from './components/Dashboard.vue'
import EquipmentList from './components/equipment/EquipmentList.vue'
import UserList from './components/users/UserList.vue'
import SealList from './components/seals/SealList.vue'
import HistoryTabs from './components/history/HistoryTabs.vue'

export default {
  name: 'App',
  components: {
    Dashboard,
    EquipmentList,
    UserList,
    SealList,
    HistoryTabs
  },
  data() {
    return {
      currentView: 'dashboard',
      menus: [
        { key: 'dashboard', label: '대시보드' },
        { key: 'equipment', label: '장비 관리' },
        { key: 'users', label: '사용자 관리' },
        { key: 'seals', label: '보안씰 관리' },
        { key: 'history', label: '이력 관리' }
      ]
    }
  }
}
</script>

<style>
@import './assets/styles.css';
</style>