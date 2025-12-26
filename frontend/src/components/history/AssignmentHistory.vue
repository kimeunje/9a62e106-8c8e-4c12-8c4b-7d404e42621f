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
    
    <div class="table-container">
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
      }
    }
  },
  mounted() {
    this.loadHistory()
  },
  methods: {
    async loadHistory() {
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
      }
    },
    
    formatDate(dateString) {
      if (!dateString) return '-'
      return dateString.split('T')[0]
    }
  }
}
</script>