<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal">
      <h2>{{ isEdit ? '장비 수정' : '장비 등록' }}</h2>
      <form @submit.prevent="save">
        <div class="form-grid">
          <div class="form-group">
            <label>자산번호 *</label>
            <input 
              v-model="form.asset_number" 
              @blur="formatAssetNumber" 
              placeholder="예: 5 → 0005" 
              required 
            />
          </div>
          <div class="form-group">
            <label>구분 *</label>
            <select v-model="form.category" required>
              <option value="데스크탑">데스크탑</option>
              <option value="미니PC">미니PC</option>
              <option value="노트북">노트북</option>
              <option value="모니터">모니터</option>
              <option value="프린터">프린터</option>
            </select>
          </div>
          <div class="form-group">
            <label>모델명 *</label>
            <input v-model="form.model_name" required />
          </div>
          <div class="form-group">
            <label>취득일자 *</label>
            <input type="date" v-model="form.acquisition_date" required />
          </div>
          <div class="form-group">
            <label>IP 주소</label>
            <input v-model="form.ip_address" placeholder="예: 145.23.13.52" />
          </div>
          <div class="form-group">
            <label>망분리</label>
            <select v-model="form.network_type">
              <option value="">선택 안함</option>
              <option value="내부망">내부망</option>
              <option value="인터넷망">인터넷망</option>
            </select>
          </div>
          <div class="form-group">
            <label>윈도우 버전</label>
            <select v-model="form.windows_version">
              <option value="">선택 안함</option>
              <option value="윈도우10">윈도우10</option>
              <option value="윈도우11">윈도우11</option>
            </select>
          </div>
          <div class="form-group" v-if="isEdit">
            <label>상태</label>
            <select v-model="form.status">
              <option value="사용가능">사용가능</option>
              <option value="사용중">사용중</option>
              <option value="수리중">수리중</option>
              <option value="폐기">폐기</option>
            </select>
          </div>
        </div>
        
        <div class="form-group">
          <label>보안씰 번호 (쉼표로 구분)</label>
          <input 
            v-model="form.seal_numbers" 
            @blur="formatSealNumbers" 
            placeholder="예: 5, 35 → 0005, 0035" 
          />
          <small class="form-hint">* 이미 다른 장비에 할당된 보안씰은 사용할 수 없습니다.</small>
        </div>
        
        <div class="form-group">
          <label>비고</label>
          <textarea v-model="form.notes" rows="3"></textarea>
        </div>
        
        <div v-if="isEdit" class="form-grid">
          <div class="form-group">
            <label>변경자</label>
            <input v-model="form.changed_by" placeholder="변경자명" />
          </div>
          <div class="form-group">
            <label>변경 사유</label>
            <input v-model="form.reason" placeholder="변경 사유" />
          </div>
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
import { equipmentApi } from '../../api'

export default {
  name: 'EquipmentForm',
  props: {
    equipment: {
      type: Object,
      default: null
    },
    isEdit: {
      type: Boolean,
      default: false
    }
  },
  emits: ['close', 'saved'],
  data() {
    return {
      form: {
        id: null,
        asset_number: '',
        category: '',
        model_name: '',
        acquisition_date: '',
        ip_address: '',
        network_type: '',
        windows_version: '',
        status: '사용가능',
        notes: '',
        seal_numbers: '',
        changed_by: '',
        reason: ''
      },
      saving: false
    }
  },
  mounted() {
    if (this.equipment) {
      this.form = {
        ...this.equipment,
        seal_numbers: this.equipment.security_seals 
          ? this.equipment.security_seals.map(s => s.seal_number).join(', ') 
          : '',
        changed_by: '',
        reason: ''
      }
    }
  },
  methods: {
    formatPaddedNumber(value, length = 4) {
      if (!value) return value
      value = String(value).trim()
      if (/^\d+$/.test(value)) return value.padStart(length, '0')
      const match = value.match(/^([A-Za-z가-힣]+-?)(\d+)$/)
      if (match) return match[1] + match[2].padStart(length, '0')
      return value
    },
    
    formatAssetNumber() {
      if (this.form.asset_number) {
        this.form.asset_number = this.formatPaddedNumber(this.form.asset_number)
      }
    },
    
    formatSealNumbers() {
      if (this.form.seal_numbers) {
        const seals = this.form.seal_numbers.split(',')
        const formatted = seals.map(s => this.formatPaddedNumber(s.trim())).filter(s => s)
        this.form.seal_numbers = formatted.join(', ')
      }
    },
    
    async save() {
      this.saving = true
      try {
        if (this.isEdit) {
          await equipmentApi.update(this.form.id, this.form)
          alert('장비 정보가 수정되었습니다.')
        } else {
          await equipmentApi.create(this.form)
          alert('장비가 등록되었습니다.')
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