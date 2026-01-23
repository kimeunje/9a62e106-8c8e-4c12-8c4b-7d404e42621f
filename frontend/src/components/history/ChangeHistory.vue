<template>
  <div class="history-content">
    <h2>변경 이력</h2>
    
    <div class="filter-box">
      <select v-model="filter.entity_type">
        <option value="">전체 유형</option>
        <option value="equipment">장비</option>
        <option value="user">사용자</option>
        <option value="assignment">할당</option>
        <option value="security_seal">보안씰</option>
      </select>
      <input v-model="filter.changed_by" placeholder="변경자" />
      <input type="date" v-model="filter.start_date" />
      <span>~</span>
      <input type="date" v-model="filter.end_date" />
      <button @click="loadHistory" class="btn-search">검색</button>
    </div>
    
    <!-- 로딩 표시 -->
    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p class="loading-text">변경 이력을 불러오는 중...</p>
    </div>
    
    <div v-else class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th>변경일시</th>
            <th>유형</th>
            <th>변경항목</th>
            <th>변경전</th>
            <th>변경후</th>
            <th>변경자</th>
            <th>사유</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in historyList" :key="item.id">
            <td>{{ formatDateTime(item.change_date) }}</td>
            <td>
              <span :class="'type-badge type-' + item.entity_type">
                {{ getEntityTypeName(item.entity_type) }}
              </span>
            </td>
            <td>{{ item.field_name }}</td>
            <td>{{ item.old_value || '-' }}</td>
            <td>{{ item.new_value }}</td>
            <td>{{ item.changed_by || '-' }}</td>
            <td>{{ item.reason || '-' }}</td>
          </tr>
          <tr v-if="historyList.length === 0">
            <td colspan="7" class="empty-message">이력이 없습니다.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import { historyApi } from '../../api'

export default {
  name: 'ChangeHistory',
  data() {
    return {
      historyList: [],
      filter: {
        entity_type: '',
        changed_by: '',
        start_date: '',
        end_date: ''
      },
      loading: false  // 로딩 상태 추가
    }
  },
  mounted() {
    this.loadHistory()
  },
  methods: {
    async loadHistory() {
      this.loading = true  // 로딩 시작
      try {
        const params = {}
        if (this.filter.entity_type) params.entity_type = this.filter.entity_type
        if (this.filter.changed_by) params.changed_by = this.filter.changed_by
        if (this.filter.start_date) params.start_date = this.filter.start_date
        if (this.filter.end_date) params.end_date = this.filter.end_date
        
        const response = await historyApi.getChangeLogs(params)
        this.historyList = response.data
      } catch (error) {
        console.error('변경 이력 로드 실패:', error)
      } finally {
        this.loading = false  // 로딩 완료
      }
    },
    
    formatDateTime(dateString) {
      if (!dateString) return '-'
      return dateString.replace('T', ' ').split('.')[0]
    },
    
    getEntityTypeName(entityType) {
      const typeNames = {
        'equipment': '장비',
        'user': '사용자',
        'assignment': '할당',
        'security_seal': '보안씰'
      }
      return typeNames[entityType] || entityType
    }
  }
}
</script>

<style scoped>
/* 로딩 컨테이너 스타일 */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  background: #f8f9fa;
  border-radius: 8px;
  margin-top: 1rem;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #e0e0e0;
  border-top-color: #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading-text {
  margin-top: 1rem;
  color: #7f8c8d;
  font-size: 0.95rem;
}
</style>
