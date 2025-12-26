<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal">
      <h2>{{ isEdit ? '보안씰 수정' : '보안씰 등록' }}</h2>
      <form @submit.prevent="save">
        <div class="form-grid">
          <div class="form-group">
            <label>보안씰 번호 *</label>
            <input 
              v-model="form.seal_number" 
              @blur="formatSealNumber" 
              placeholder="예: 5 → 0005" 
              required 
            />
          </div>
          <div class="form-group">
            <label>장비 선택 *</label>
            <select v-model="form.equipment_id" required>
              <option value="">선택하세요</option>
              <option v-for="eq in equipmentList" :key="eq.id" :value="eq.id">
                {{ eq.asset_number }} - {{ eq.model_name }}
              </option>
            </select>
          </div>
          <div class="form-group">
            <label>부착일</label>
            <input type="date" v-model="form.attached_date" />
          </div>
          <div class="form-group">
            <label>부착위치</label>
            <input v-model="form.attached_location" placeholder="예: 본체 후면" />
          </div>
          <div class="form-group">
            <label>상태 *</label>
            <select v-model="form.status" required>
              <option value="정상">정상</option>
              <option value="파손">파손</option>
              <option value="분실">분실</option>
              <option value="교체필요">교체필요</option>
            </select>
          </div>
          <div class="form-group">
            <label>점검일</label>
            <input type="date" v-model="form.inspection_date" />
          </div>
        </div>
        
        <div class="form-group">
          <label>비고</label>
          <textarea v-model="form.notes" rows="3" placeholder="추가 메모"></textarea>
        </div>
        
        <div class="form-group">
          <label>변경자</label>
          <input v-model="form.changed_by" placeholder="변경자명" />
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
import { sealApi } from '../../api'

export default {
  name: 'SealForm',
  props: {
    seal: {
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
        seal_number: '',
        equipment_id: '',
        attached_date: new Date().toISOString().split('T')[0],
        attached_location: '',
        status: '정상',
        inspection_date: '',
        notes: '',
        changed_by: ''
      },
      saving: false
    }
  },
  mounted() {
    if (this.seal) {
      this.form = {
        id: this.seal.id,
        seal_number: this.seal.seal_number,
        equipment_id: this.seal.equipment_id,
        attached_date: this.seal.attached_date || '',
        attached_location: this.seal.attached_location || '',
        status: this.seal.status,
        inspection_date: this.seal.inspection_date || '',
        notes: this.seal.notes || '',
        changed_by: ''
      }
    }
  },
  methods: {
    formatSealNumber() {
      if (this.form.seal_number) {
        const value = String(this.form.seal_number).trim()
        if (/^\d+$/.test(value)) {
          this.form.seal_number = value.padStart(4, '0')
        }
      }
    },
    
    async save() {
      this.saving = true
      try {
        if (this.isEdit) {
          await sealApi.update(this.form.id, this.form)
          alert('보안씰 정보가 수정되었습니다.')
        } else {
          await sealApi.create(this.form)
          alert('보안씰이 등록되었습니다.')
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