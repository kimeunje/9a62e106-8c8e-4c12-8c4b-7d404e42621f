<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal">
      <h2>장비 할당 - {{ user?.name }}</h2>
      <form @submit.prevent="assign">
        <div class="form-group">
          <label>할당할 장비 선택 *</label>
          
          <!-- 검색 필터 -->
          <div class="assign-search-box">
            <input 
              v-model="search.keyword" 
              placeholder="자산번호 또는 모델명 검색" 
              class="assign-search-input"
            />
            <select v-model="search.category" class="assign-search-select">
              <option value="">전체 구분</option>
              <option value="데스크탑">데스크탑</option>
              <option value="미니PC">미니PC</option>
              <option value="노트북">노트북</option>
              <option value="모니터">모니터</option>
              <option value="프린터">프린터</option>
            </select>
            <button type="button" @click="resetSearch" class="btn-reset-small">초기화</button>
          </div>
          
          <!-- 검색 결과 카운트 -->
          <div class="search-result-count">
            검색 결과: {{ filteredEquipment.length }}개 / 전체 사용가능: {{ availableEquipment.length }}개
          </div>
          
          <!-- 장비 목록 -->
          <div class="available-equipment-list">
            <div 
              v-for="eq in filteredEquipment" 
              :key="eq.id"
              :class="['equipment-option', { selected: form.equipment_id === eq.id }]"
              @click="form.equipment_id = eq.id"
            >
              <div class="equipment-option-info">
                <span class="asset-num">{{ eq.asset_number }}</span>
                <span class="model">{{ eq.model_name }}</span>
                <span class="category">{{ eq.category }}</span>
              </div>
              <div class="equipment-option-check" v-if="form.equipment_id === eq.id">✔</div>
            </div>
            <div v-if="filteredEquipment.length === 0 && availableEquipment.length > 0" class="empty-equipment-list">
              검색 결과가 없습니다.
            </div>
            <div v-if="availableEquipment.length === 0" class="empty-equipment-list">
              사용 가능한 장비가 없습니다.
            </div>
          </div>
        </div>
        
        <div class="form-grid">
          <div class="form-group">
            <label>할당일</label>
            <input type="date" v-model="form.assignment_date" />
          </div>
          <div class="form-group">
            <label>담당자</label>
            <input v-model="form.assigned_by" placeholder="담당자명" />
          </div>
        </div>
        
        <div class="form-group">
          <label>할당 사유</label>
          <textarea v-model="form.reason" rows="2" placeholder="할당 사유를 입력하세요"></textarea>
        </div>
        
        <div class="modal-buttons">
          <button type="submit" class="btn-primary" :disabled="!form.equipment_id || assigning">
            {{ assigning ? '할당 중...' : '할당' }}
          </button>
          <button type="button" @click="$emit('close')" class="btn-secondary">취소</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import { equipmentApi, assignmentApi } from '../../api'

export default {
  name: 'AssignmentModal',
  props: {
    user: {
      type: Object,
      required: true
    }
  },
  emits: ['close', 'assigned'],
  data() {
    return {
      availableEquipment: [],
      search: {
        keyword: '',
        category: ''
      },
      form: {
        equipment_id: '',
        assignment_date: new Date().toISOString().split('T')[0],
        assigned_by: '',
        reason: ''
      },
      assigning: false
    }
  },
  computed: {
    filteredEquipment() {
      let filtered = this.availableEquipment
      
      if (this.search.keyword) {
        const keyword = this.search.keyword.toLowerCase()
        filtered = filtered.filter(eq => 
          eq.asset_number.toLowerCase().includes(keyword) ||
          eq.model_name.toLowerCase().includes(keyword)
        )
      }
      
      if (this.search.category) {
        filtered = filtered.filter(eq => eq.category === this.search.category)
      }
      
      return filtered
    }
  },
  mounted() {
    this.loadAvailableEquipment()
  },
  methods: {
    async loadAvailableEquipment() {
      try {
        const response = await equipmentApi.getAvailable()
        this.availableEquipment = response.data
      } catch (error) {
        console.error('사용 가능한 장비 로드 실패:', error)
      }
    },
    
    resetSearch() {
      this.search = { keyword: '', category: '' }
      this.form.equipment_id = ''
    },
    
    async assign() {
      if (!this.form.equipment_id) {
        alert('장비를 선택해주세요.')
        return
      }
      
      const equipment = this.availableEquipment.find(eq => eq.id === this.form.equipment_id)
      
      this.assigning = true
      try {
        await assignmentApi.create({
          asset_number: equipment.asset_number,
          user_id: this.user.id,
          assignment_date: this.form.assignment_date,
          reason: this.form.reason,
          assigned_by: this.form.assigned_by
        })
        alert('장비가 할당되었습니다.')
        this.$emit('assigned')
      } catch (error) {
        alert('할당에 실패했습니다: ' + (error.response?.data?.error || error.message))
      } finally {
        this.assigning = false
      }
    }
  }
}
</script>