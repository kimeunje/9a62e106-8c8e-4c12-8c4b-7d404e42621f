<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal modal-large">
      <h2>📥 엑셀 데이터 가져오기</h2>
      
      <!-- Step 1: 파일 선택 -->
      <div v-if="step === 1" class="import-step">
        <div class="import-info-box">
          <h4>📋 지원하는 엑셀 형식</h4>
          <p>기존 전산장비 관리 엑셀 파일을 그대로 업로드하세요.</p>
          <div class="column-info">
            <span class="column-tag">구분</span>
            <span class="column-tag">규격</span>
            <span class="column-tag">모델 명</span>
            <span class="column-tag">번호</span>
            <span class="column-tag">취득일자</span>
            <span class="column-tag">IP</span>
            <span class="column-tag">위치</span>
            <span class="column-tag">사용자</span>
            <span class="column-tag">부서</span>
            <span class="column-tag">보안씰1~3</span>
            <span class="column-tag">망분리</span>
            <span class="column-tag">win버전</span>
          </div>
        </div>
        
        <div 
          class="file-upload-area" 
          @drop.prevent="handleFileDrop" 
          @dragover.prevent="dragOver = true" 
          @dragleave="dragOver = false" 
          :class="{ 'drag-over': dragOver }"
        >
          <input 
            type="file" 
            ref="fileInput" 
            @change="handleFileSelect" 
            accept=".xlsx,.xls" 
            style="display: none" 
          />
          <div v-if="!file" class="upload-placeholder" @click="$refs.fileInput.click()">
            <div class="upload-icon">📁</div>
            <p>클릭하거나 파일을 드래그하세요</p>
            <span class="file-hint">.xlsx, .xls 파일 지원</span>
          </div>
          <div v-else class="selected-file">
            <div class="file-icon">📄</div>
            <div class="file-info">
              <span class="file-name">{{ file.name }}</span>
              <span class="file-size">{{ formatFileSize(file.size) }}</span>
            </div>
            <button type="button" @click="clearFile" class="btn-remove">✕</button>
          </div>
        </div>
        
        <div class="import-actions">
          <button @click="downloadTemplate" class="btn-secondary">📥 템플릿 다운로드</button>
          <div>
            <button @click="$emit('close')" class="btn-secondary">취소</button>
            <button @click="previewImport" class="btn-primary" :disabled="!file || loading">
              {{ loading ? '분석 중...' : '다음 →' }}
            </button>
          </div>
        </div>
      </div>
      
      <!-- Step 2: 미리보기 및 확인 -->
      <div v-if="step === 2" class="import-step">
        <div class="import-summary">
          <div class="summary-card">
            <span class="summary-number">{{ preview.total_rows }}</span>
            <span class="summary-label">전체 행</span>
          </div>
          <div class="summary-card new">
            <span class="summary-number">{{ preview.new_count }}</span>
            <span class="summary-label">신규 등록</span>
          </div>
          <div class="summary-card update">
            <span class="summary-number">{{ preview.update_count }}</span>
            <span class="summary-label">기존 장비</span>
          </div>
          <div class="summary-card error" v-if="preview.error_count > 0">
            <span class="summary-number">{{ preview.error_count }}</span>
            <span class="summary-label">오류</span>
          </div>
        </div>
        
        <!-- 에러 표시 -->
        <div v-if="preview.errors && preview.errors.length > 0" class="import-errors">
          <h4>⚠️ 처리할 수 없는 행</h4>
          <ul>
            <li v-for="(error, idx) in preview.errors" :key="idx">{{ error }}</li>
          </ul>
        </div>
        
        <!-- 미리보기 테이블 -->
        <div class="preview-table-container">
          <h4>미리보기 (처음 10개)</h4>
          <table class="preview-table">
            <thead>
              <tr>
                <th>상태</th>
                <th>자산번호</th>
                <th>구분</th>
                <th>모델명</th>
                <th>사용자</th>
                <th>부서</th>
                <th>보안씰</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in preview.preview" :key="item.row_num">
                <td>
                  <span :class="item.is_new ? 'badge-new' : 'badge-update'">
                    {{ item.is_new ? '신규' : '기존' }}
                  </span>
                </td>
                <td>{{ item.asset_number }}</td>
                <td>{{ item.category }}</td>
                <td>{{ item.model_name }}</td>
                <td>{{ item.user_name || '-' }}</td>
                <td>{{ item.department || '-' }}</td>
                <td>{{ item.seals.join(', ') || '-' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        
        <!-- 옵션 -->
        <div class="import-options">
          <label class="checkbox-label">
            <input type="checkbox" v-model="overwrite" />
            <span>기존 장비 정보 덮어쓰기 (체크하지 않으면 신규만 등록)</span>
          </label>
          <div class="form-group inline">
            <label>작업자명</label>
            <input v-model="changedBy" placeholder="엑셀 임포트" />
          </div>
        </div>
        
        <div class="import-actions">
          <button @click="step = 1" class="btn-secondary">← 이전</button>
          <div>
            <button @click="$emit('close')" class="btn-secondary">취소</button>
            <button @click="executeImport" class="btn-primary" :disabled="loading">
              {{ loading ? '가져오는 중...' : '가져오기 실행' }}
            </button>
          </div>
        </div>
      </div>
      
      <!-- Step 3: 완료 -->
      <div v-if="step === 3" class="import-step">
        <div class="import-complete">
          <div class="complete-icon">✅</div>
          <h3>가져오기 완료!</h3>
          <div class="complete-summary">
            <div class="complete-item">
              <span class="complete-label">장비 등록</span>
              <span class="complete-value">{{ result.equipment_created }}건</span>
            </div>
            <div class="complete-item">
              <span class="complete-label">장비 업데이트</span>
              <span class="complete-value">{{ result.equipment_updated }}건</span>
            </div>
            <div class="complete-item">
              <span class="complete-label">사용자 등록</span>
              <span class="complete-value">{{ result.users_created }}건</span>
            </div>
            <div class="complete-item">
              <span class="complete-label">할당 처리</span>
              <span class="complete-value">{{ result.assignments_created }}건</span>
            </div>
            <div class="complete-item">
              <span class="complete-label">보안씰 등록</span>
              <span class="complete-value">{{ result.seals_created }}건</span>
            </div>
          </div>
          <div v-if="result.errors && result.errors.length > 0" class="complete-errors">
            <h4>⚠️ 일부 오류 발생</h4>
            <ul>
              <li v-for="(error, idx) in result.errors.slice(0, 10)" :key="idx">{{ error }}</li>
            </ul>
          </div>
        </div>
        <div class="import-actions center">
          <button @click="finish" class="btn-primary">확인</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { importApi } from '../../api'

export default {
  name: 'ImportModal',
  emits: ['close', 'imported'],
  data() {
    return {
      step: 1,
      file: null,
      loading: false,
      dragOver: false,
      preview: {
        total_rows: 0,
        valid_rows: 0,
        new_count: 0,
        update_count: 0,
        errors: [],
        error_count: 0,
        preview: []
      },
      result: {
        equipment_created: 0,
        equipment_updated: 0,
        users_created: 0,
        assignments_created: 0,
        seals_created: 0,
        errors: []
      },
      overwrite: false,
      changedBy: ''
    }
  },
  methods: {
    handleFileSelect(event) {
      const selectedFile = event.target.files[0]
      if (selectedFile) {
        this.file = selectedFile
      }
    },
    
    handleFileDrop(event) {
      this.dragOver = false
      const droppedFile = event.dataTransfer.files[0]
      if (droppedFile && (droppedFile.name.endsWith('.xlsx') || droppedFile.name.endsWith('.xls'))) {
        this.file = droppedFile
      } else {
        alert('엑셀 파일(.xlsx, .xls)만 지원합니다.')
      }
    },
    
    clearFile() {
      this.file = null
      if (this.$refs.fileInput) {
        this.$refs.fileInput.value = ''
      }
    },
    
    formatFileSize(bytes) {
      if (bytes < 1024) return bytes + ' B'
      if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
      return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
    },
    
    async downloadTemplate() {
      try {
        const response = await importApi.downloadTemplate()
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', '장비임포트_템플릿.xlsx')
        document.body.appendChild(link)
        link.click()
        link.remove()
      } catch (error) {
        alert('템플릿 다운로드에 실패했습니다.')
      }
    },
    
    async previewImport() {
      if (!this.file) {
        alert('파일을 선택해주세요.')
        return
      }
      
      this.loading = true
      const formData = new FormData()
      formData.append('file', this.file)
      
      try {
        const response = await importApi.previewImport(formData)
        
        if (response.data.success) {
          this.preview = response.data
          this.step = 2
        } else {
          alert('파일 분석 실패: ' + (response.data.error || '알 수 없는 오류'))
        }
      } catch (error) {
        const errorMsg = error.response?.data?.error || error.message
        alert('파일 분석 중 오류: ' + errorMsg)
        
        if (error.response?.data?.found_columns) {
          console.log('발견된 컬럼:', error.response.data.found_columns)
        }
      } finally {
        this.loading = false
      }
    },
    
    async executeImport() {
      this.loading = true
      const formData = new FormData()
      formData.append('file', this.file)
      formData.append('overwrite', this.overwrite)
      formData.append('changed_by', this.changedBy || '엑셀 임포트')
      
      try {
        const response = await importApi.executeImport(formData)
        
        if (response.data.success) {
          this.result = response.data.results
          this.step = 3
        } else {
          alert('가져오기 실패: ' + (response.data.error || '알 수 없는 오류'))
        }
      } catch (error) {
        alert('가져오기 중 오류: ' + (error.response?.data?.error || error.message))
      } finally {
        this.loading = false
      }
    },
    
    finish() {
      this.$emit('imported')
    }
  }
}
</script>