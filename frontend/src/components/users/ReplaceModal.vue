<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal">
      <h2>장비 교체 - {{ user?.name }}</h2>
      
      <!-- 현재 장비 정보 -->
      <div class="current-equipment-info">
        <h4>🔄 반납할 장비</h4>
        <div class="equipment-summary">
          <span class="asset-num">{{ currentAssignment?.equipment?.asset_number }}</span>
          <span class="model">{{ currentAssignment?.equipment?.model_name }}</span>
          <span class="category-tag">{{ currentAssignment?.equipment?.category }}</span>
        </div>
      </div>
      
      <form @submit.prevent="replace">
        <div class="form-group">
          <label>교체할 새 장비 선택 *</label>
          
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
              :class="['equipment-option', { selected: form.new_equipment_id === eq.id }]"
              @click="form.new_equipment_id = eq.id"
            >
              <div class="equipment-option-info">
                <span class="asset-num">{{ eq.asset_number }}</span>
                <span class="model">{{ eq.model_name }}</span>
                <span class="category">{{ eq.category }}</span>
                <span v-if="showNetworkType(eq)" class="network-tag">{{ eq.network_type }}</span>
              </div>
              <div class="equipment-option-check" v-if="form.new_equipment_id === eq.id">✔</div>
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
            <label>교체일</label>
            <input type="date" v-model="form.replace_date" />
          </div>
          <div class="form-group">
            <label>담당자</label>
            <input v-model="form.assigned_by" placeholder="담당자명" />
          </div>
        </div>
        
        <div class="form-group">
          <label>교체 사유</label>
          <textarea v-model="form.reason" rows="2" placeholder="교체 사유를 입력하세요 (예: 노후화, 고장, 업그레이드 등)"></textarea>
        </div>
        
        <div class="modal-buttons">
          <button type="submit" class="btn-primary" :disabled="!form.new_equipment_id || replacing">
            {{ replacing ? '교체 중...' : '교체 실행' }}
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
  name: 'ReplaceModal',
  props: {
    user: {
      type: Object,
      required: true
    },
    currentAssignment: {
      type: Object,
      required: true
    }
  },
  emits: ['close', 'replaced'],
  data() {
    return {
      availableEquipment: [],
      search: {
        keyword: '',
        category: ''
      },
      form: {
        new_equipment_id: '',
        replace_date: new Date().toISOString().split('T')[0],
        assigned_by: '',
        reason: ''
      },
      replacing: false
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
    // 현재 장비와 같은 카테고리로 필터 기본값 설정
    if (this.currentAssignment?.equipment?.category) {
      this.search.category = this.currentAssignment.equipment.category
    }
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
      this.form.new_equipment_id = ''
    },
    
    showNetworkType(eq) {
      return (eq.category === '데스크탑' || eq.category === '미니PC') && eq.network_type
    },
    
    async replace() {
      if (!this.form.new_equipment_id) {
        alert('교체할 장비를 선택해주세요.')
        return
      }
      
      const newEquipment = this.availableEquipment.find(eq => eq.id === this.form.new_equipment_id)
      
      this.replacing = true
      try {
        // 1. 기존 장비 반납
        await assignmentApi.return(this.currentAssignment.id, {
          return_date: this.form.replace_date,
          assigned_by: this.form.assigned_by,
          reason: `장비 교체 - ${this.form.reason || '교체'}`
        })
        
        // 2. 새 장비 할당
        await assignmentApi.create({
          asset_number: newEquipment.asset_number,
          user_id: this.user.id,
          assignment_date: this.form.replace_date,
          reason: `장비 교체 (기존: ${this.currentAssignment.equipment.asset_number}) - ${this.form.reason || ''}`,
          assigned_by: this.form.assigned_by
        })
        
        alert(`장비가 교체되었습니다.\n반납: ${this.currentAssignment.equipment.asset_number}\n할당: ${newEquipment.asset_number}`)
        this.$emit('replaced')
      } catch (error) {
        alert('교체에 실패했습니다: ' + (error.response?.data?.error || error.message))
      } finally {
        this.replacing = false
      }
    }
  }
}
</script>

<style scoped>
.current-equipment-info {
  background: #fff3cd;
  border: 1px solid #ffc107;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1.5rem;
}

.current-equipment-info h4 {
  margin: 0 0 0.5rem 0;
  color: #856404;
  font-size: 0.95rem;
}

.equipment-summary {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  flex-wrap: wrap;
}

.equipment-summary .asset-num {
  font-family: monospace;
  color: #3498db;
  font-weight: 600;
  background: #fff;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
}

.equipment-summary .model {
  color: #2c3e50;
  font-weight: 500;
}

.equipment-summary .category-tag {
  font-size: 0.8rem;
  color: #7f8c8d;
  background: #fff;
  padding: 0.15rem 0.4rem;
  border-radius: 3px;
}

.network-tag {
  font-size: 0.75rem;
  color: #fff;
  background: #9b59b6;
  padding: 0.15rem 0.4rem;
  border-radius: 3px;
  margin-left: 0.25rem;
}
</style>
