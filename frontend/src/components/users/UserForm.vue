<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal modal-small">
      <h2>{{ isEdit ? '사용자 수정' : '사용자 등록' }}</h2>
      <form @submit.prevent="save">
        <div class="form-group">
          <label>이름 *</label>
          <input v-model="form.name" required />
        </div>
        <div class="form-group">
          <label>부서 *</label>
          <input v-model="form.department" required />
        </div>
        <div class="form-group">
          <label>위치 *</label>
          <input v-model="form.location" required placeholder="예: 15층" />
        </div>
        <div class="form-group">
          <label>전화번호</label>
          <input v-model="form.phone" placeholder="예: 010-1234-5678" />
        </div>
        <div class="form-group">
          <label>이메일</label>
          <input v-model="form.email" type="email" placeholder="예: user@company.com" />
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
import { userApi } from '../../api'

export default {
  name: 'UserForm',
  props: {
    user: {
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
        name: '',
        department: '',
        location: '',
        phone: '',
        email: ''
      },
      saving: false
    }
  },
  mounted() {
    if (this.user) {
      this.form = { ...this.user }
    }
  },
  methods: {
    async save() {
      this.saving = true
      try {
        let savedUser
        if (this.isEdit) {
          const response = await userApi.update(this.form.id, this.form)
          savedUser = response.data
          alert('사용자 정보가 수정되었습니다.')
        } else {
          const response = await userApi.create(this.form)
          savedUser = response.data
          alert('사용자가 등록되었습니다.')
        }
        this.$emit('saved', savedUser)
      } catch (error) {
        alert('저장에 실패했습니다: ' + (error.response?.data?.error || error.message))
      } finally {
        this.saving = false
      }
    }
  }
}
</script>