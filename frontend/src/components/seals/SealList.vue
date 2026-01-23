<template>
  <div class="seal-management">
    <div class="toolbar">
      <h2>보안씰 관리</h2>
      <button @click="openAddModal" class="btn-primary">보안씰 등록</button>
    </div>

    <!-- 검색 박스 -->
    <div class="search-box">
      <input v-model="search.seal_number" placeholder="보안씰 번호" @keyup.enter="searchSeals" />
      <input v-model="search.asset_number" placeholder="장비 자산번호" @keyup.enter="searchSeals" />
      <select v-model="search.status">
        <option value="">전체 상태</option>
        <option value="정상">정상</option>
        <option value="파손">파손</option>
        <option value="분실">분실</option>
        <option value="교체필요">교체필요</option>
        <option value="폐기">폐기</option>  <!-- 추가 -->
      </select>
      <button @click="searchSeals" class="btn-search">검색</button>
      <button @click="resetSearch" class="btn-reset">초기화</button>
    </div>

    <!-- 로딩 표시 -->
    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p class="loading-text">보안씰 목록을 불러오는 중...</p>
    </div>

    <!-- 테이블 -->
    <div v-else class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th>보안씰 번호</th>
            <th>장비 자산번호</th>
            <th>장비 모델명</th>
            <th>부착일</th>
            <th>부착위치</th>
            <th>상태</th>
            <th>점검일</th>
            <th>비고</th>
            <th>관리</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="seal in sealList" :key="seal.id">
            <td>{{ seal.seal_number }}</td>
            <td>{{ getEquipmentAssetNumber(seal) }}</td>
            <td>{{ getEquipmentModelName(seal) }}</td>
            <td>{{ formatDate(seal.attached_date) }}</td>
            <td>{{ seal.attached_location || '-' }}</td>
            <td>
              <span :class="'seal-status-badge seal-status-' + seal.status">{{ seal.status }}</span>
            </td>
            <td>{{ formatDate(seal.inspection_date) }}</td>
            <td>{{ seal.notes || '-' }}</td>
            <td>
              <button @click="openEditModal(seal)" class="btn-small">수정</button>
              <button @click="deleteSeal(seal.id)" class="btn-small btn-danger">삭제</button>
            </td>
          </tr>
          <tr v-if="sealList.length === 0">
            <td colspan="9" class="empty-message">등록된 보안씰이 없습니다.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 보안씰 등록/수정 모달 -->
    <SealForm
      v-if="showModal"
      :seal="selectedSeal"
      :is-edit="isEdit"
      :equipment-list="equipmentList"
      @close="closeModal"
      @saved="onSaved"
    />
  </div>
</template>

<script>
import { sealApi, equipmentApi } from '../../api'
import SealForm from './SealForm.vue'

export default {
  name: 'SealList',
  components: {
    SealForm
  },
  data() {
    return {
      sealList: [],
      equipmentList: [],
      equipmentMap: {},
      search: {
        seal_number: '',
        asset_number: '',
        status: ''
      },
      showModal: false,
      isEdit: false,
      selectedSeal: null,
      loading: false  // 로딩 상태 추가
    }
  },
  mounted() {
    this.loadSeals()
    this.loadEquipment()
  },
  methods: {
    async loadSeals() {
      this.loading = true  // 로딩 시작
      try {
        const response = await sealApi.getAll()
        this.sealList = response.data
      } catch (error) {
        console.error('보안씰 목록 로드 실패:', error)
      } finally {
        this.loading = false  // 로딩 완료
      }
    },
    
    async loadEquipment() {
      try {
        const response = await equipmentApi.getAll({ per_page: 10000 })
        this.equipmentList = response.data.items || response.data
        
        // 장비 맵 생성 (빠른 조회용)
        this.equipmentMap = {}
        this.equipmentList.forEach(eq => {
          this.equipmentMap[eq.id] = eq
        })
      } catch (error) {
        console.error('장비 목록 로드 실패:', error)
      }
    },
    
    // 장비 자산번호 가져오기 (seal.equipment가 없을 경우 equipmentMap에서 조회)
    getEquipmentAssetNumber(seal) {
      if (seal.equipment?.asset_number) {
        return seal.equipment.asset_number
      }
      if (seal.equipment_id && this.equipmentMap[seal.equipment_id]) {
        return this.equipmentMap[seal.equipment_id].asset_number
      }
      return '-'
    },
    
    // 장비 모델명 가져오기
    getEquipmentModelName(seal) {
      if (seal.equipment?.model_name) {
        return seal.equipment.model_name
      }
      if (seal.equipment_id && this.equipmentMap[seal.equipment_id]) {
        return this.equipmentMap[seal.equipment_id].model_name
      }
      return '-'
    },
    
    async searchSeals() {
      this.loading = true  // 검색 시에도 로딩 표시
      try {
        const params = {}
        if (this.search.seal_number) params.seal_number = this.search.seal_number
        if (this.search.asset_number) params.asset_number = this.search.asset_number
        if (this.search.status) params.status = this.search.status
        
        const response = await sealApi.search(params)
        this.sealList = response.data
      } catch (error) {
        alert('검색에 실패했습니다.')
      } finally {
        this.loading = false  // 로딩 완료
      }
    },
    
    resetSearch() {
      this.search = {
        seal_number: '',
        asset_number: '',
        status: ''
      }
      this.loadSeals()
    },
    
    openAddModal() {
      this.selectedSeal = null
      this.isEdit = false
      this.showModal = true
    },
    
    openEditModal(seal) {
      // 수정 모달을 열 때 equipment 정보가 없으면 equipmentMap에서 가져옴
      const sealCopy = { ...seal }
      if (!sealCopy.equipment && sealCopy.equipment_id && this.equipmentMap[sealCopy.equipment_id]) {
        sealCopy.equipment = this.equipmentMap[sealCopy.equipment_id]
      }
      this.selectedSeal = sealCopy
      this.isEdit = true
      this.showModal = true
    },
    
    closeModal() {
      this.showModal = false
      this.selectedSeal = null
    },
    
    onSaved() {
      this.closeModal()
      this.loadSeals()
    },
    
    async deleteSeal(id) {
      if (!confirm('이 보안씰을 삭제하시겠습니까?')) return
      
      try {
        await sealApi.delete(id, { changed_by: '' })
        alert('삭제되었습니다.')
        this.loadSeals()
      } catch (error) {
        alert('삭제에 실패했습니다: ' + (error.response?.data?.error || error.message))
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
