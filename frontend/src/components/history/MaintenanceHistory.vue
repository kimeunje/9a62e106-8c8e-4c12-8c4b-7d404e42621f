<template>
  <div class="history-content">
    <div class="toolbar">
      <h2>수리/점검 이력</h2>
      <button @click="openModal()" class="btn-primary">이력 등록</button>
    </div>
    
    <div class="filter-box">
      <select v-model="filter.maintenance_type">
        <option value="">전체 유형</option>
        <option value="수리">수리</option>
        <option value="점검">점검</option>
        <option value="청소">청소</option>
        <option value="업그레이드">업그레이드</option>
        <option value="기타">기타</option>
      </select>
      <select v-model="filter.status">
        <option value="">전체 상태</option>
        <option value="완료">완료</option>
        <option value="진행중">진행중</option>
        <option value="예정">예정</option>
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
            <th>일자</th>
            <th>자산번호</th>
            <th>장비명</th>
            <th>유형</th>
            <th>작업내용</th>
            <th>작업자</th>
            <th>비용</th>
            <th>상태</th>
            <th>관리</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in historyList" :key="item.id">
            <td>{{ formatDate(item.maintenance_date) }}</td>
            <td>{{ item.equipment?.asset_number || '-' }}</td>
            <td>{{ item.equipment?.model_name || '-' }}</td>
            <td>
              <span :class="'maintenance-type-' + item.maintenance_type">
                {{ item.maintenance_type }}
              </span>
            </td>
            <td>{{ item.description }}</td>
            <td>{{ item.technician || '-' }}</td>
            <td>{{ item.cost ? item.cost.toLocaleString() + '원' : '-' }}</td>
            <td>
              <span :class="'maintenance-status-' + item.status">{{ item.status }}</span>
            </td>
            <td>
              <button @click="openModal(item)" class="btn-small">수정</button>
              <button @click="deleteLog(item.id)" class="btn-small btn-danger">삭제</button>
            </td>
          </tr>
          <tr v-if="historyList.length === 0">
            <td colspan="9" class="empty-message">이력이 없습니다.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 수리/점검 등록/수정 모달 -->
    <MaintenanceForm
      v-if="showModal"
      :log="selectedLog"
      :is-edit="isEdit"
      :equipment-list="equipmentList"
      @close="closeModal"
      @saved="onSaved"
    />
  </div>
</template>

<script>
import { maintenanceApi, equipmentApi } from '../../api'
import MaintenanceForm from './MaintenanceForm.vue'

export default {
  name: 'MaintenanceHistory',
  components: {
    MaintenanceForm
  },
  data() {
    return {
      historyList: [],
      equipmentList: [],
      filter: {
        maintenance_type: '',
        status: '',
        start_date: '',
        end_date: ''
      },
      showModal: false,
      isEdit: false,
      selectedLog: null
    }
  },
  mounted() {
    this.loadHistory()
    this.loadEquipment()
  },
  methods: {
    async loadHistory() {
      try {
        const params = {}
        if (this.filter.maintenance_type) params.maintenance_type = this.filter.maintenance_type
        if (this.filter.status) params.status = this.filter.status
        if (this.filter.start_date) params.start_date = this.filter.start_date
        if (this.filter.end_date) params.end_date = this.filter.end_date
        
        const response = await maintenanceApi.getAll(params)
        this.historyList = response.data
      } catch (error) {
        console.error('수리/점검 이력 로드 실패:', error)
      }
    },
    
    async loadEquipment() {
      try {
        const response = await equipmentApi.getAll({ per_page: 1000 })
        this.equipmentList = response.data.items || response.data
      } catch (error) {
        console.error('장비 목록 로드 실패:', error)
      }
    },
    
    openModal(log = null) {
      if (log) {
        this.selectedLog = { ...log }
        this.isEdit = true
      } else {
        this.selectedLog = null
        this.isEdit = false
      }
      this.showModal = true
    },
    
    closeModal() {
      this.showModal = false
      this.selectedLog = null
    },
    
    onSaved() {
      this.closeModal()
      this.loadHistory()
    },
    
    async deleteLog(id) {
      if (!confirm('수리/점검 이력을 삭제하시겠습니까?')) return
      
      try {
        await maintenanceApi.delete(id)
        alert('삭제되었습니다.')
        this.loadHistory()
      } catch (error) {
        alert('삭제에 실패했습니다.')
      }
    },
    
    formatDate(dateString) {
      if (!dateString) return '-'
      return dateString.split('T')[0]
    }
  }
}
</script>