<template>
  <div class="modal-overlay">
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

          <!-- 보안씰 섹션 (인라인 수정 가능) -->
          <div class="detail-section seal-section">
            <div class="section-header-inline">
              <h4>보안씰</h4>
              <button 
                v-if="!isSealEditing" 
                @click="startSealEdit" 
                class="btn-tiny"
                title="보안씰 수정"
              >
                ✏️ 수정
              </button>
            </div>
            
            <!-- 보안씰 보기 모드 -->
            <div v-if="!isSealEditing">
              <div v-if="localSeals.length > 0" class="seal-list">
                <div v-for="seal in localSeals" :key="seal.id" class="seal-item">
                  <span class="seal-number">{{ seal.seal_number }}</span>
                  <span :class="'seal-status seal-status-' + seal.status">{{ seal.status }}</span>
                  <span v-if="seal.attached_location" class="seal-location">{{ seal.attached_location }}</span>
                </div>
              </div>
              <div v-else class="detail-value empty-seal">등록된 보안씰 없음</div>
            </div>
            
            <!-- 보안씰 수정 모드 -->
            <div v-else class="seal-edit-mode">
              <div v-for="(seal, index) in editingSeals" :key="index" class="seal-edit-row">
                <input 
                  v-model="seal.seal_number" 
                  placeholder="씰번호"
                  class="seal-input seal-number-input"
                  @blur="formatSealNumber(index)"
                />
                <select v-model="seal.status" class="seal-input seal-status-select">
                  <option value="정상">정상</option>
                  <option value="파손">파손</option>
                  <option value="분실">분실</option>
                  <option value="교체필요">교체필요</option>
                </select>
                <input 
                  v-model="seal.attached_location" 
                  placeholder="부착위치"
                  class="seal-input seal-location-input"
                />
                <button @click="removeSeal(index)" class="btn-tiny btn-danger" title="삭제">✕</button>
              </div>
              
              <button @click="addSeal" class="btn-add-seal">+ 보안씰 추가</button>
              
              <div class="seal-edit-actions">
                <button @click="saveSeals" :disabled="savingSeals" class="btn-primary btn-sm">
                  {{ savingSeals ? '저장 중...' : '저장' }}
                </button>
                <button @click="cancelSealEdit" class="btn-secondary btn-sm">취소</button>
              </div>
            </div>
          </div>

          <div class="detail-section full-width" v-if="equipment.notes">
            <h4>비고</h4>
            <div class="detail-notes">{{ equipment.notes }}</div>
          </div>
        </div>

        <div class="modal-buttons">
          <button @click="$emit('close')" class="btn-secondary">닫기</button>
        </div>
      </div>

      <!-- 수정 모드 (전체 수정) -->
      <form v-else @submit.prevent="save" class="equipment-edit-form">
        <div class="form-grid">
          <div class="form-group">
            <label>자산번호 *</label>
            <input v-model="form.asset_number" required @blur="formatAssetNumber" />
          </div>
          <div class="form-group">
            <label>구분 *</label>
            <select v-model="form.category" required>
              <option value="">선택</option>
              <option value="데스크탑">데스크탑</option>
              <option value="노트북">노트북</option>
              <option value="모니터">모니터</option>
              <option value="미니PC">미니PC</option>
              <option value="프린터">프린터</option>
              <option value="기타">기타</option>
            </select>
          </div>
          <div class="form-group">
            <label>모델명 *</label>
            <input v-model="form.model_name" required />
          </div>
          <div class="form-group">
            <label>상태 *</label>
            <select v-model="form.status" required>
              <option value="사용가능">사용가능</option>
              <option value="사용중">사용중</option>
              <option value="수리중">수리중</option>
              <option value="폐기">폐기</option>
            </select>
          </div>
          <div class="form-group">
            <label>취득일자</label>
            <input type="date" v-model="form.acquisition_date" />
          </div>
          <div class="form-group">
            <label>IP 주소</label>
            <input v-model="form.ip_address" placeholder="예: 192.168.0.1" />
          </div>
          <div class="form-group">
            <label>망분리</label>
            <select v-model="form.network_type">
              <option value="">선택</option>
              <option value="업무망">업무망</option>
              <option value="인터넷망">인터넷망</option>
              <option value="내부망">내부망</option>
              <option value="외부망">외부망</option>
            </select>
          </div>
          <div class="form-group">
            <label>윈도우 버전</label>
            <input v-model="form.windows_version" placeholder="예: Windows 11 Pro" />
          </div>
          <div class="form-group full-width">
            <label>보안씰 (쉼표로 구분)</label>
            <input v-model="form.seal_numbers" placeholder="예: 0001, 0002" @blur="formatSealNumbers" />
            <span class="form-hint">여러 개의 보안씰 번호를 쉼표(,)로 구분하여 입력하세요</span>
          </div>
          <div class="form-group full-width">
            <label>비고</label>
            <textarea v-model="form.notes" rows="3"></textarea>
          </div>
          <div class="form-group">
            <label>변경자</label>
            <input v-model="form.changed_by" placeholder="이름 입력" />
          </div>
          <div class="form-group">
            <label>변경사유</label>
            <input v-model="form.reason" placeholder="변경 사유 입력" />
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
import { equipmentApi, sealApi } from '../../api'

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
      // 보안씰 인라인 수정 관련
      isSealEditing: false,
      savingSeals: false,
      localSeals: [],
      editingSeals: [],
      // 전체 수정 폼
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
    this.initLocalSeals()
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
    
    initLocalSeals() {
      this.localSeals = this.equipment.security_seals 
        ? [...this.equipment.security_seals] 
        : []
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
    
    // ===== 보안씰 인라인 수정 =====
    startSealEdit() {
      this.editingSeals = this.localSeals.map(seal => ({
        id: seal.id,
        seal_number: seal.seal_number,
        status: seal.status || '정상',
        attached_location: seal.attached_location || '',
        isNew: false
      }))
      this.isSealEditing = true
    },
    
    cancelSealEdit() {
      this.isSealEditing = false
      this.editingSeals = []
    },
    
    addSeal() {
      this.editingSeals.push({
        id: null,
        seal_number: '',
        status: '정상',
        attached_location: '',
        isNew: true
      })
    },
    
    removeSeal(index) {
      this.editingSeals.splice(index, 1)
    },
    
    formatSealNumber(index) {
      const seal = this.editingSeals[index]
      if (seal && seal.seal_number) {
        seal.seal_number = this.formatPaddedNumber(seal.seal_number)
      }
    },
    
    async saveSeals() {
      // 유효성 검사
      const validSeals = this.editingSeals.filter(s => s.seal_number.trim())
      
      // 중복 검사 (입력된 씰번호 간)
      const sealNumbers = validSeals.map(s => s.seal_number)
      const duplicates = sealNumbers.filter((num, idx) => sealNumbers.indexOf(num) !== idx)
      if (duplicates.length > 0) {
        alert(`중복된 보안씰 번호가 있습니다: ${duplicates.join(', ')}`)
        return
      }
      
      this.savingSeals = true
      
      try {
        const currentSealIds = this.localSeals.map(s => s.id)
        const editingSealIds = validSeals.filter(s => s.id).map(s => s.id)
        
        // 삭제할 보안씰 (기존에 있었지만 수정 목록에 없는 것)
        const sealsToDelete = currentSealIds.filter(id => !editingSealIds.includes(id))
        
        // 삭제 처리
        for (const sealId of sealsToDelete) {
          await sealApi.delete(sealId, { changed_by: '' })
        }
        
        // 수정/추가 처리
        for (const seal of validSeals) {
          if (seal.id) {
            // 기존 보안씰 수정
            await sealApi.update(seal.id, {
              seal_number: seal.seal_number,
              status: seal.status,
              attached_location: seal.attached_location,
              equipment_id: this.equipment.id
            })
          } else {
            // 새 보안씰 추가
            await sealApi.create({
              seal_number: seal.seal_number,
              status: seal.status,
              attached_location: seal.attached_location,
              equipment_id: this.equipment.id,
              attached_date: new Date().toISOString().split('T')[0]
            })
          }
        }
        
        // 로컬 상태 업데이트
        this.localSeals = validSeals.map(s => ({
          ...s,
          id: s.id || Date.now() // 임시 ID (실제로는 서버에서 받아와야 함)
        }))
        
        this.isSealEditing = false
        this.editingSeals = []
        
        alert('보안씰 정보가 저장되었습니다.')
        this.$emit('updated')
        
      } catch (error) {
        alert('보안씰 저장에 실패했습니다: ' + (error.response?.data?.error || error.message))
      } finally {
        this.savingSeals = false
      }
    },
    
    // ===== 전체 수정 =====
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

/* 보안씰 섹션 스타일 */
.seal-section {
  grid-column: 1 / -1;
}

.section-header-inline {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #ecf0f1;
}

.section-header-inline h4 {
  margin: 0;
  padding: 0;
  border: none;
}

.btn-tiny {
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
  border: 1px solid #ddd;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-tiny:hover {
  background: #f8f9fa;
  border-color: #3498db;
}

.btn-tiny.btn-danger {
  color: #e74c3c;
  border-color: #e74c3c;
}

.btn-tiny.btn-danger:hover {
  background: #e74c3c;
  color: white;
}

.seal-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.seal-item {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  background: #ebf5fb;
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  border: 1px solid #d4edfc;
}

.seal-number {
  font-family: monospace;
  color: #3498db;
  font-weight: 600;
  font-size: 0.95rem;
}

.seal-status {
  font-size: 0.7rem;
  padding: 0.15rem 0.4rem;
  border-radius: 3px;
  font-weight: 500;
}

.seal-status-정상 { background: #27ae60; color: white; }
.seal-status-파손 { background: #e74c3c; color: white; }
.seal-status-분실 { background: #95a5a6; color: white; }
.seal-status-교체필요 { background: #e67e22; color: white; }

.seal-location {
  font-size: 0.8rem;
  color: #7f8c8d;
  padding-left: 0.5rem;
  border-left: 1px solid #bdc3c7;
}

.empty-seal {
  color: #95a5a6;
  font-style: italic;
}

/* 보안씰 수정 모드 */
.seal-edit-mode {
  background: #fff;
  border: 1px solid #3498db;
  border-radius: 6px;
  padding: 1rem;
}

.seal-edit-row {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
  align-items: center;
}

.seal-input {
  padding: 0.4rem 0.6rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
}

.seal-input:focus {
  outline: none;
  border-color: #3498db;
}

.seal-number-input {
  width: 120px;
  font-family: monospace;
}

.seal-status-select {
  width: 100px;
}

.seal-location-input {
  flex: 1;
  min-width: 100px;
}

.btn-add-seal {
  width: 100%;
  padding: 0.5rem;
  border: 2px dashed #bdc3c7;
  background: transparent;
  color: #7f8c8d;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s;
  margin-bottom: 1rem;
}

.btn-add-seal:hover {
  border-color: #3498db;
  color: #3498db;
  background: #ebf5fb;
}

.seal-edit-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
  padding-top: 0.75rem;
  border-top: 1px solid #ecf0f1;
}

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

/* 폼 스타일 */
.equipment-edit-form .form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.equipment-edit-form .form-group.full-width {
  grid-column: 1 / -1;
}

.form-hint {
  display: block;
  margin-top: 0.25rem;
  font-size: 0.8rem;
  color: #7f8c8d;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@media (max-width: 768px) {
  .detail-grid {
    grid-template-columns: 1fr;
  }
  
  .seal-edit-row {
    flex-wrap: wrap;
  }
  
  .seal-number-input,
  .seal-status-select {
    width: calc(50% - 0.25rem);
  }
  
  .seal-location-input {
    width: 100%;
  }
}
</style>