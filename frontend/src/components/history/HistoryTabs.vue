<template>
  <div class="history-management">
    <div class="history-tabs">
      <button 
        @click="activeTab = 'assignment'" 
        :class="{ active: activeTab === 'assignment' }"
      >
        할당 이력
      </button>
      <button 
        @click="activeTab = 'change'" 
        :class="{ active: activeTab === 'change' }"
      >
        변경 이력
      </button>
      <button 
        @click="activeTab = 'maintenance'" 
        :class="{ active: activeTab === 'maintenance' }"
      >
        수리/점검 이력
      </button>
    </div>

    <AssignmentHistory v-if="activeTab === 'assignment'" />
    <ChangeHistory v-if="activeTab === 'change'" />
    <MaintenanceHistory v-if="activeTab === 'maintenance'" />
  </div>
</template>

<script>
import AssignmentHistory from './AssignmentHistory.vue'
import ChangeHistory from './ChangeHistory.vue'
import MaintenanceHistory from './MaintenanceHistory.vue'

export default {
  name: 'HistoryTabs',
  components: {
    AssignmentHistory,
    ChangeHistory,
    MaintenanceHistory
  },
  data() {
    return {
      activeTab: 'assignment'
    }
  }
}
</script>