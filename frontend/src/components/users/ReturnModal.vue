<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal modal-small">
      <h2>장비 반납</h2>
      <div class="return-equipment-info">
        <p><strong>장비:</strong> {{ assignment?.equipment?.model_name }}</p>
        <p><strong>자산번호:</strong> {{ assignment?.equipment?.asset_number }}</p>
      </div>
      <form @submit.prevent="returnEquipment">
        <div class="form-group">
          <label>담당자 *</label>
          <input v-model="form.assigned_by" required placeholder="담당자명 입력" />
        </div>
        <div class="form-group">
          <label>반납일</label>
          <input type="date" v-model="form.return_date" />
        </div>
        <div class="form-group">
          <label>반납 사유</label>
          <textarea v-model="form.reason" rows="2" placeholder="반납 사유"></textarea>
        </div>
        <div class="modal-buttons">
          <button type="submit" class="btn-primary" :disabled="returning">
            {{ returning ? '처리 중...' : '반납 처리' }}
          </button>
          <button type="button" @click="$emit('close')" class="btn-secondary">취소</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import { assignmentApi } from '../../api'

export default {
  name: 'ReturnModal',
  props: {
    assignment: {
      type: Object,
      required: true
    }
  },
  emits: ['close', 'returned'],
  data() {
    return {
      form: {
        assigned_by: '',
        return_date: new Date().toISOString().split('T')[0],
        reason: ''
      },
      returning: false
    }
  },
  methods: {
    async returnEquipment() {
      if (!this.form.assigned_by) {
        alert('담당자명을 입력해주세요.')
        return
      }
      
      this.returning = true
      try {
        await assignmentApi.return(this.assignment.id, this.form)
        alert('장비가 반납되었습니다.')
        this.$emit('returned')
      } catch (error) {
        alert('반납에 실패했습니다: ' + (error.response?.data?.error || error.message))
      } finally {
        this.returning = false
      }
    }
  }
}
</script>