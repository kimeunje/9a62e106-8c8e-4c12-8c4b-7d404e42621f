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
    
    <div class="table-container">
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
      }
    }
  },
  mounted() {
    this.loadHistory()
  },
  methods: {
    async loadHistory() {
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