<template>
  <div class="dashboard">
    <h2>장비 현황</h2>
    <div class="stats-grid">
      <div class="stat-card">
        <h3>전체 장비</h3>
        <p class="stat-number">{{ statistics.total_equipment }}</p>
      </div>
      <div class="stat-card">
        <h3>전체 사용자</h3>
        <p class="stat-number">{{ statistics.total_users }}</p>
      </div>
      <div class="stat-card">
        <h3>사용중인 장비</h3>
        <p class="stat-number">{{ statistics.active_assignments }}</p>
      </div>
      <div class="stat-card">
        <h3>전체 보안씰</h3>
        <p class="stat-number">{{ statistics.total_seals }}</p>
      </div>
      <div class="stat-card" v-for="(count, status) in statistics.by_status" :key="status">
        <h3>{{ status }}</h3>
        <p class="stat-number">{{ count }}</p>
      </div>
    </div>

    <h3>구분별 현황</h3>
    <div class="department-stats">
      <div v-for="(count, category) in statistics.by_category" :key="category" class="dept-item">
        <span>{{ category }}</span>
        <span class="count">{{ count }}대</span>
      </div>
    </div>

    <h3>부서별 사용자</h3>
    <div class="department-stats">
      <div v-for="(count, dept) in statistics.by_department" :key="dept" class="dept-item">
        <span>{{ dept }}</span>
        <span class="count">{{ count }}명</span>
      </div>
    </div>

    <h3>보안씰 상태</h3>
    <div class="department-stats">
      <div v-for="(count, status) in statistics.by_seal_status" :key="status" class="dept-item">
        <span>{{ status }}</span>
        <span class="count">{{ count }}개</span>
      </div>
    </div>
  </div>
</template>

<script>
import { statisticsApi } from '../api'

export default {
  name: 'Dashboard',
  data() {
    return {
      statistics: {
        total_equipment: 0,
        total_users: 0,
        total_seals: 0,
        active_assignments: 0,
        by_status: {},
        by_category: {},
        by_department: {},
        by_location: {},
        by_seal_status: {}
      }
    }
  },
  mounted() {
    this.loadStatistics()
  },
  methods: {
    async loadStatistics() {
      try {
        const response = await statisticsApi.get()
        this.statistics = response.data
      } catch (error) {
        console.error('통계 로드 실패:', error)
      }
    }
  }
}
</script>