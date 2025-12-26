<template>
  <div class="equipment-management">
    <div class="toolbar">
      <h2>장비 관리</h2>
      <div>
        <button @click="openAddModal" class="btn-primary">장비 등록</button>
        <button @click="openImportModal" class="btn-primary">📥 엑셀 가져오기</button>
        <button @click="exportExcel" class="btn-secondary">엑셀 내보내기</button>
      </div>
    </div>

    <!-- 검색 박스 -->
    <div class="search-box">
      <input v-model="search.asset_number" placeholder="자산번호" @keyup.enter="searchEquipment(1)" />
      <input v-model="search.model_name" placeholder="모델명" @keyup.enter="searchEquipment(1)" />
      <input v-model="search.user_name" placeholder="사용자" @keyup.enter="searchEquipment(1)" />
      <input v-model="search.department" placeholder="부서" @keyup.enter="searchEquipment(1)" />
      <select v-model="search.category">
        <option value="">전체 구분</option>
        <option value="데스크탑">데스크탑</option>
        <option value="미니PC">미니PC</option>
        <option value="모니터">모니터</option>
        <option value="노트북">노트북</option>
      </select>
      <select v-model="search.status">
        <option value="">전체 상태</option>
        <option value="사용가능">사용가능</option>
        <option value="사용중">사용중</option>
        <option value="수리중">수리중</option>
        <option value="폐기">폐기</option>
      </select>
      <button @click="searchEquipment(1)" class="btn-search">검색</button>
      <button @click="resetSearch" class="btn-reset">초기화</button>
    </div>

    <!-- 검색 결과 정보 -->
    <div class="result-info">
      <span>총 <strong>{{ pagination.total }}</strong>건</span>
      <span class="per-page-select">
        페이지당
        <select v-model="pagination.perPage" @change="searchEquipment(1)">
          <option :value="30">30개</option>
          <option :value="50">50개</option>
          <option :value="100">100개</option>
        </select>
      </span>
    </div>

    <!-- 테이블 -->
    <div class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th>자산번호</th>
            <th>구분</th>
            <th>모델명</th>
            <th>상태</th>
            <th>현재 사용자</th>
            <th>부서</th>
            <th>위치</th>
            <th>보안씰</th>
            <th>관리</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="eq in equipmentList" :key="eq.id">
            <td>{{ eq.asset_number }}</td>
            <td>{{ eq.category }}</td>
            <td>{{ eq.model_name }}</td>
            <td>
              <span :class="'status-badge status-' + eq.status">{{ eq.status }}</span>
            </td>
            <td>{{ eq.current_user?.name || '-' }}</td>
            <td>{{ eq.current_user?.department || '-' }}</td>
            <td>{{ eq.current_user?.location || '-' }}</td>
            <td>
              <span v-if="eq.security_seals && eq.security_seals.length > 0">
                {{ eq.security_seals.map(s => s.seal_number).join(', ') }}
              </span>
              <span v-else>-</span>
            </td>
            <td>
              <button @click="viewDetail(eq)" class="btn-small">상세</button>
              <button @click="openEditModal(eq)" class="btn-small">수정</button>
            </td>
          </tr>
          <tr v-if="equipmentList.length === 0">
            <td colspan="9" class="empty-message">
              {{ loading ? '로딩 중...' : '검색 결과가 없습니다.' }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 페이지네이션 -->
    <Pagination 
      v-if="pagination.totalPages > 1"
      :current-page="pagination.page"
      :total-pages="pagination.totalPages"
      @page-change="goToPage"
    />

    <!-- 장비 등록/수정 모달 -->
    <EquipmentForm
      v-if="showModal"
      :equipment="selectedEquipment"
      :is-edit="isEdit"
      @close="closeModal"
      @saved="onSaved"
    />

    <!-- 엑셀 가져오기 모달 -->
    <ImportModal
      v-if="showImportModal"
      @close="showImportModal = false"
      @imported="onImported"
    />
  </div>
</template>

<script>
import { equipmentApi, importApi } from '../../api'
import Pagination from '../common/Pagination.vue'
import EquipmentForm from './EquipmentForm.vue'
import ImportModal from '../import/ImportModal.vue'

export default {
  name: 'EquipmentList',
  components: {
    Pagination,
    EquipmentForm,
    ImportModal
  },
  data() {
    return {
      equipmentList: [],
      loading: false,
      search: {
        asset_number: '',
        category: '',
        status: '',
        model_name: '',
        user_name: '',
        department: ''
      },
      pagination: {
        page: 1,
        perPage: 50,
        total: 0,
        totalPages: 0
      },
      showModal: false,
      showImportModal: false,
      isEdit: false,
      selectedEquipment: null
    }
  },
  mounted() {
    this.searchEquipment(1)
  },
  methods: {
    async searchEquipment(page = 1) {
      this.loading = true
      try {
        const params = {
          page,
          per_page: this.pagination.perPage,
          ...this.search
        }
        
        // 빈 값 제거
        Object.keys(params).forEach(key => {
          if (!params[key]) delete params[key]
        })
        
        const response = await equipmentApi.getAll(params)
        
        this.equipmentList = response.data.items
        this.pagination.page = response.data.page
        this.pagination.total = response.data.total
        this.pagination.totalPages = response.data.total_pages
      } catch (error) {
        console.error('장비 목록 로드 실패:', error)
      } finally {
        this.loading = false
      }
    },
    
    goToPage(page) {
      this.searchEquipment(page)
    },
    
    resetSearch() {
      this.search = {
        asset_number: '',
        category: '',
        status: '',
        model_name: '',
        user_name: '',
        department: ''
      }
      this.searchEquipment(1)
    },
    
    openAddModal() {
      this.selectedEquipment = null
      this.isEdit = false
      this.showModal = true
    },
    
    openEditModal(equipment) {
      this.selectedEquipment = { ...equipment }
      this.isEdit = true
      this.showModal = true
    },
    
    closeModal() {
      this.showModal = false
      this.selectedEquipment = null
    },
    
    onSaved() {
      this.closeModal()
      this.searchEquipment(this.pagination.page)
    },
    
    viewDetail(equipment) {
      let detail = `상세 정보\n\n`
      detail += `자산번호: ${equipment.asset_number}\n`
      detail += `모델명: ${equipment.model_name}\n`
      detail += `구분: ${equipment.category}\n`
      detail += `상태: ${equipment.status}\n`
      detail += `취득일자: ${equipment.acquisition_date || '-'}\n`
      detail += `IP주소: ${equipment.ip_address || '-'}\n`
      detail += `망분리: ${equipment.network_type || '-'}\n`
      detail += `윈도우: ${equipment.windows_version || '-'}`
      
      if (equipment.current_user) {
        detail += `\n\n현재 사용자: ${equipment.current_user.name} (${equipment.current_user.department})`
      }
      
      alert(detail)
    },
    
    openImportModal() {
      this.showImportModal = true
    },
    
    onImported() {
      this.showImportModal = false
      this.searchEquipment(1)
    },
    
    async exportExcel() {
      try {
        const response = await importApi.exportExcel()
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', `전산장비목록_${new Date().toISOString().split('T')[0]}.xlsx`)
        document.body.appendChild(link)
        link.click()
        link.remove()
      } catch (error) {
        alert('엑셀 내보내기에 실패했습니다.')
      }
    }
  }
}
</script>