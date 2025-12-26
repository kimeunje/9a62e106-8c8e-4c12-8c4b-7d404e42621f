<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal">
      <h2>{{ isEdit ? '수리/점검 이력 수정' : '수리/점검 이력 등록' }}</h2>
      <form @submit.prevent="save">
        <div class="form-group">
          <label>장비 선택 *</label>
          <select v-model="form.equipment_id" required>
            <option value="">선택하세요</option>
            <option v-for="eq in equipmentList" :key="eq.id" :value="eq.id">
              {{ eq.asset_number }} - {{ eq.model_name }}
            </option>
          </select>
        </div>
        
        <div class="form-grid">
          <div class="form-group">
            <label>작업일자 *</label>
            <input type="date" v-model="form.maintenance_date" required />
          </div>
          <div class="form-group">
            <label>유형 *</label>
            <select v-model="form.maintenance_type" required>
              <option value="수리">수리</option>
              <option value="점검">점검</option>
              <option value="청소">청소</option>
              <option value="업그레이드">업그레이드</option>
              <option value="기타">기타</option>
            </select>
          </div>
          <div class="form-group">
            <label>작업자</label>
            <input v-model="form.technician" placeholder="작업자명" />
          </div>
          <div class="form-group">
            <label>비용</label>
            <input type="number" v-model="form.cost" placeholder="비용 (원)" />
          </div>
          <div class="form-group">
            <label>상태 *</label>
            <select v-model="form.status" required>
              <option value="완료">완료</option>
              <option value="진행중">진행중</option>
              <option value="예정">예정</option>
            </select>
          </div>
          <div class="form-group">
            <label>등록자</label>
            <input v-model="form.created_by" placeholder="등록자명" />
          </div>
        </div>
        
        <div class="form-group">
          <label>작업 내용 *</label>
          <textarea v-model="form.description" rows="3" required placeholder="수행한 작업 내용을 입력하세요"></textarea>
        </div>
        
        <div class="form-group">
          <label>비고</label>
          <textarea v-model="form.notes" rows="2" placeholder="추가 메모"></textarea>
        </div>
        
        <div class="modal-buttons">
          <button type="submit" class="btn-primary" :disabled="saving">
            {{ saving ? '저장 중...' : '저장' }}
          </button>
          <button type="button" @click="$emit('close')" class="btn-secondary">취소</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import { maintenanceApi } from '../../api'

export default {
  name: 'MaintenanceForm',
  props: {
    log: {
      type: Object,
      default: null
    },
    isEdit: {
      type: Boolean,
      default: false
    },
    equipmentList: {
      type: Array,
      default: () => []
    }
  },
  emits: ['close', 'saved'],
  data() {
    return {
      form: {
        id: null,
        equipment_id: '',
        maintenance_date: new Date().toISOString().split('T')[0],
        maintenance_type: '점검',
        description: '',
        technician: '',
        cost: null,
        status: '완료',
        notes: '',
        created_by: ''
      },
      saving: false
    }
  },
  mounted() {
    if (this.log) {
      this.form = { ...this.log }
    }
  },
  methods: {
    async save() {
      this.saving = true
      try {
        if (this.isEdit) {
          await maintenanceApi.update(this.form.id, this.form)
          alert('수리/점검 이력이 수정되었습니다.')
        } else {
          await maintenanceApi.create(this.form)
          alert('수리/점검 이력이 등록되었습니다.')
        }
        this.$emit('saved')
      } catch (error) {
        alert('저장에 실패했습니다: ' + (error.response?.data?.error || error.message))
      } finally {
        this.saving = false
      }
    }
  }
}
</script>