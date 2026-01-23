<template>
  <div class="history-content">
    <h2>할당 이력</h2>
    
    <div class="filter-box">
      <select v-model="filter.status">
        <option value="">전체 상태</option>
        <option value="사용중">사용중</option>
        <option value="반납">반납</option>
      </select>
      <input type="date" v-model="filter.start_date" />
      <span>~</span>
      <input type="date" v-model="filter.end_date" />
      <button @click="loadHistory" class="btn-search">검색</button>
    </div>
    
    <!-- 로딩 표시 -->
    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p class="loading-text">할당 이력을 불러오는 중...</p>
    </div>
    
    <div v-else class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th>할당일</th>
            <th>반납일</th>
            <th>자산번호</th>
            <th>모델명</th>
            <th>사용자</th>
            <th>부서</th>
            <th>위치</th>
            <th>상태</th>
            <th>담당자</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in historyList" :key="item.id">
            <td>{{ formatDate(item.assignment_date) }}</td>
            <td>{{ item.return_date ? formatDate(item.return_date) : '-' }}</td>
            <td>{{ item.equipment.asset_number }}</td>
            <td>{{ item.equipment.model_name }}</td>
            <td>{{ item.user.name }}</td>
            <td>{{ item.user.department }}</td>
            <td>{{ item.user.location }}</td>
            <td>
              <span :class="'status-badge status-' + item.status">{{ item.status }}</span>
            </td>
            <td>{{ item.assigned_by || '-' }}</td>
          </tr>
          <tr v-if="historyList.length === 0">
            <td colspan="9" class="empty-message">이력이 없습니다.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import { assignmentApi } from '../../api'

export default {
  name: 'AssignmentHistory',
  data() {
    return {
      historyList: [],
      filter: {
        status: '',
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
        const response = await assignmentApi.getAll()
        let data = response.data
        
        // 클라이언트 측 필터링
        if (this.filter.status) {
          data = data.filter(item => item.status === this.filter.status)
        }
        if (this.filter.start_date) {
          data = data.filter(item => item.assignment_date >= this.filter.start_date)
        }
        if (this.filter.end_date) {
          data = data.filter(item => item.assignment_date <= this.filter.end_date)
        }
        
        this.historyList = data
      } catch (error) {
        console.error('할당 이력 로드 실패:', error)
      } finally {
        this.loading = false  // 로딩 완료
      }
    },
    
    formatDate(dateString) {
      if (!dateString) return '-'
      return dateString.split('T')[0]
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
