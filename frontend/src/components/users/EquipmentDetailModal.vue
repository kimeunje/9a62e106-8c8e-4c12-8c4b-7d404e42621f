<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal modal-large">
      <div class="modal-header">
        <h2>{{ isEditing ? '장비 수정' : '장비 상세 정보' }}</h2>
        <div class="modal-header-actions">
          <button v-if="!isEditing" @click="isEditing = true" class="btn-small">✏️ 수정</button>
          <button @click="$emit('close')" class="btn-close">✕</button>
        </div>
      </div>

      <!-- 보기 모드 -->
      <div v-if="!isEditing" class="equipment-detail-view">
        <div class="detail-grid">
          <div class="detail-section">
            <h4>기본 정보</h4>
            <div class="detail-row">
              <span class="detail-label">자산번호</span>
              <span class="detail-value highlight">{{ equipment.asset_number }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">구분</span>
              <span class="detail-value">{{ equipment.category }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">모델명</span>
              <span class="detail-value">{{ equipment.model_name }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">상태</span>
              <span :class="'status-badge status-' + equipment.status">{{ equipment.status }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">취득일자</span>
              <span class="detail-value">{{ equipment.acquisition_date || '-' }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">사용기간</span>
              <span class="detail-value">{{ equipment.usage_years }}년 {{ equipment.usage_months % 12 }}개월</span>
            </div>
          </div>

          <div class="detail-section">
            <h4>네트워크 정보</h4>
            <div class="detail-row">
              <span class="detail-label">IP 주소</span>
              <span class="detail-value">{{ equipment.ip_address || '-' }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">망분리</span>
              <span class="detail-value">
                <span v-if="equipment.network_type" :class="'network-tag network-' + getNetworkClass(equipment.network_type)">
                  {{ equipment.network_type }}
                </span>
                <span v-else>-</span>
              </span>
            </div>
            <div class="detail-row">
              <span class="detail-label">윈도우 버전</span>
              <span class="detail-value">{{ equipment.windows_version || '-' }}</span>
            </div>
          </div>

          <div class="detail-section">
            <h4>보안씰</h4>
            <div v-if="equipment.security_seals && equipment.security_seals.length > 0" class="seal-list">
              <span v-for="seal in equipment.security_seals" :key="seal.id" class="seal-tag">
                {{ seal.seal_number }}
                <span :class="'seal-status seal-status-' + seal.status">{{ seal.status }}</span>
              </span>
            </div>
            <div v-else class="detail-value">등록된 보안씰 없음</div>
          </div>

          <div class="detail-section full-width" v-if="equipment.notes">
            <h4>비고</h4>
            <div class="detail-notes">{{ equipment.notes }}</div>
          </div>
        </div>

        <div class="modal-buttons">
          <button @click="isEditing = true" class="btn-primary">수정하기</button>
          <button @click="$emit('close')" class="btn-secondary">닫기</button>
        </div>
      </div>

      <!-- 수정 모드 -->
      <form v-else @submit.prevent="save">
        <div class="form-grid">
          <div class="form-group">
            <label>자산번호 *</label>
            <input 
              v-model="form.asset_number" 
              @blur="formatAssetNumber" 
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
            <input v-model="form.ip_address" placeholder="예: 10.4.12.53" />
          </div>
          <div class="form-group">
            <label>망분리</label>
            <select v-model="form.network_type">
              <option value="">선택 안함</option>
              <option value="내부망">내부망</option>
              <option value="인터넷망">인터넷망</option>
              <option value="업무망">업무망</option>
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
          <div class="form-group">
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
            placeholder="예: 0005, 0035" 
          />
        </div>
        
        <div class="form-group">
          <label>비고</label>
          <textarea v-model="form.notes" rows="3"></textarea>
        </div>
        
        <div class="form-grid">
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
          <button type="button" @click="cancelEdit" class="btn-secondary">취소</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import { equipmentApi } from '../../api'

export default {
  name: 'EquipmentDetailModal',
  props: {
    equipment: {
      type: Object,
      required: true
    }
  },
  emits: ['close', 'updated'],
  data() {
    return {
      isEditing: false,
      saving: false,
      form: {
        id: null,
        asset_number: '',
        category: '',
        model_name: '',
        acquisition_date: '',
        ip_address: '',
        network_type: '',
        windows_version: '',
        status: '',
        notes: '',
        seal_numbers: '',
        changed_by: '',
        reason: ''
      }
    }
  },
  mounted() {
    this.initForm()
  },
  methods: {
    initForm() {
      this.form = {
        id: this.equipment.id,
        asset_number: this.equipment.asset_number,
        category: this.equipment.category,
        model_name: this.equipment.model_name,
        acquisition_date: this.equipment.acquisition_date || '',
        ip_address: this.equipment.ip_address || '',
        network_type: this.equipment.network_type || '',
        windows_version: this.equipment.windows_version || '',
        status: this.equipment.status,
        notes: this.equipment.notes || '',
        seal_numbers: this.equipment.security_seals 
          ? this.equipment.security_seals.map(s => s.seal_number).join(', ') 
          : '',
        changed_by: '',
        reason: ''
      }
    },
    
    getNetworkClass(networkType) {
      if (!networkType) return ''
      if (networkType.includes('내부') || networkType.includes('업무')) return 'internal'
      if (networkType.includes('인터넷') || networkType.includes('외부')) return 'external'
      return 'default'
    },
    
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
    
    cancelEdit() {
      this.isEditing = false
      this.initForm()
    },
    
    async save() {
      this.saving = true
      try {
        await equipmentApi.update(this.form.id, this.form)
        alert('장비 정보가 수정되었습니다.')
        this.$emit('updated')
      } catch (error) {
        alert('저장에 실패했습니다: ' + (error.response?.data?.error || error.message))
      } finally {
        this.saving = false
      }
    }
  }
}
</script>

<style scoped>
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #ecf0f1;
}

.modal-header h2 {
  margin: 0;
  color: #2c3e50;
}

.modal-header-actions {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.btn-close {
  background: transparent;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #95a5a6;
  padding: 0.25rem 0.5rem;
  line-height: 1;
}

.btn-close:hover {
  color: #2c3e50;
}

.equipment-detail-view {
  animation: fadeIn 0.2s;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

.detail-section {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 1rem;
}

.detail-section.full-width {
  grid-column: 1 / -1;
}

.detail-section h4 {
  margin: 0 0 0.75rem 0;
  color: #2c3e50;
  font-size: 0.95rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #ecf0f1;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0;
  border-bottom: 1px solid #ecf0f1;
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-label {
  color: #7f8c8d;
  font-size: 0.9rem;
}

.detail-value {
  color: #2c3e50;
  font-weight: 500;
}

.detail-value.highlight {
  color: #3498db;
  font-family: monospace;
  font-size: 1.1rem;
}

.detail-notes {
  color: #2c3e50;
  line-height: 1.6;
  white-space: pre-wrap;
}

.seal-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.seal-tag {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  background: #ebf5fb;
  padding: 0.35rem 0.6rem;
  border-radius: 4px;
  font-family: monospace;
  color: #3498db;
  font-weight: 500;
}

.seal-status {
  font-size: 0.7rem;
  padding: 0.1rem 0.3rem;
  border-radius: 3px;
  font-family: sans-serif;
}

.seal-status-정상 { background: #27ae60; color: white; }
.seal-status-파손 { background: #e74c3c; color: white; }
.seal-status-분실 { background: #95a5a6; color: white; }
.seal-status-교체필요 { background: #e67e22; color: white; }

.network-tag {
  font-size: 0.8rem;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-weight: 500;
}

.network-internal {
  background: #3498db;
  color: white;
}

.network-external {
  background: #e74c3c;
  color: white;
}

.network-default {
  background: #9b59b6;
  color: white;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@media (max-width: 768px) {
  .detail-grid {
    grid-template-columns: 1fr;
  }
}
</style>
