<template>
  <div class="floor-plan-editor">
    <div class="toolbar">
      <h2>좌석 배치도</h2>
      
      <!-- 검색 영역 -->
      <div class="search-area">
        <input 
          v-model="searchQuery" 
          type="text" 
          placeholder="이름 또는 좌석번호 검색..." 
          @keyup.enter="search"
          @input="onSearchInput"
          class="search-input"
        >
        <button @click="search" class="btn-search">🔍 검색</button>
        <button v-if="searchResults.length > 0" @click="clearSearch" class="btn-clear">✕ 초기화</button>
        <span v-if="searchResults.length > 0" class="search-result-count">
          {{ currentSearchIndex + 1 }} / {{ searchResults.length }}건
          <button @click="prevResult" class="btn-nav" :disabled="searchResults.length <= 1">◀</button>
          <button @click="nextResult" class="btn-nav" :disabled="searchResults.length <= 1">▶</button>
        </span>
      </div>
      
      <div class="toolbar-buttons">
        <button @click="addSeat" class="btn-primary">➕ 좌석 추가</button>
        <button @click="addFacility" class="btn-primary">🏛️ 시설 추가</button>
        <button 
          @click="toggleDeleteMode" 
          :class="['btn-warning', { active: deleteMode }]"
        >
          🗑️ {{ deleteMode ? '삭제 모드 ON' : '삭제 모드' }}
        </button>
        <button @click="saveToServer" class="btn-secondary" :disabled="saving">
          {{ saving ? '저장 중...' : '💾 저장' }}
        </button>
        <button @click="exportData" class="btn-secondary">📥 JSON 내보내기</button>
        <button @click="triggerImport" class="btn-secondary">📂 JSON 불러오기</button>
        <button @click="resetAll" class="btn-danger">🔄 초기화</button>
        <input 
          type="file" 
          ref="fileInput" 
          accept=".json" 
          @change="importData" 
          style="display: none"
        >
      </div>
    </div>

    <div class="status-bar">
      <span v-if="lastSaved" class="save-status">
        ✅ 마지막 저장: {{ lastSaved }}
      </span>
      <span v-if="hasUnsavedChanges" class="unsaved-status">
        ⚠️ 저장되지 않은 변경사항이 있습니다
      </span>
    </div>

    <div class="help-text">
      💡 좌석 클릭: 사용자 정보 | 더블클릭: 수정 | 드래그: 이동 | Ctrl+F: 검색 | Ctrl+S: 저장
    </div>

    <div 
      class="canvas-container" 
      ref="canvas"
      @mouseup="endDrag"
      @mousemove="onDrag"
      @mouseleave="endDrag"
    >
      <div
        v-for="item in items"
        :key="item.id"
        :class="['item', getItemClass(item), { 
          dragging: dragItem?.id === item.id, 
          'delete-mode': deleteMode, 
          'selected': selectedSeat?.id === item.id,
          'search-highlight': isSearchResult(item),
          'search-current': isCurrentSearchResult(item)
        }]"
        :style="getItemStyle(item)"
        @mousedown="(e) => startDrag(e, item)"
        @click="(e) => onItemClick(e, item)"
        @dblclick="editItem(item)"
      >
        <template v-if="item.type === 'seat'">
          <span class="name">{{ item.name || '' }}</span>
          <span class="code">{{ item.code || '' }}</span>
        </template>
        <template v-else>
          <span v-html="formatText(item.name)"></span>
        </template>
        <div 
          class="resize-handle" 
          @mousedown.stop="(e) => startResize(e, item)"
        ></div>
      </div>
    </div>

    <div class="legend">
      <div class="legend-item">
        <div class="legend-color legend-seat"></div>
        <span>좌석</span>
      </div>
      <div class="legend-item">
        <div class="legend-color legend-facility"></div>
        <span>시설</span>
      </div>
      <div class="legend-item">
        <div class="legend-color legend-room"></div>
        <span>회의실/사무실</span>
      </div>
      <div class="legend-item">
        <div class="legend-color legend-equip"></div>
        <span>장비</span>
      </div>
    </div>

    <!-- 좌석 수정 모달 (더블클릭) -->
    <div v-if="showSeatModal" class="modal-overlay" @click.self="closeSeatModal">
      <div class="modal">
        <h3>좌석 정보 수정</h3>
        <div class="form-group">
          <label>좌석 번호</label>
          <input v-model="editingSeat.code" placeholder="예: C-1">
        </div>
        <div class="form-group">
          <label>사용자명</label>
          <input v-model="editingSeat.name" placeholder="이름 입력" @keyup.enter="saveSeat">
        </div>
        <div class="modal-buttons">
          <button @click="closeSeatModal" class="btn-secondary">취소</button>
          <button @click="saveSeat" class="btn-primary">저장</button>
        </div>
      </div>
    </div>

    <!-- 시설 수정 모달 -->
    <div v-if="showFacilityModal" class="modal-overlay" @click.self="closeFacilityModal">
      <div class="modal">
        <h3>시설 정보</h3>
        <div class="form-group">
          <label>시설명</label>
          <input v-model="editingFacility.name" placeholder="예: 회의실" @keyup.enter="saveFacility">
        </div>
        <div class="form-group">
          <label>시설 유형</label>
          <select v-model="editingFacility.facilityType">
            <option value="facility">일반 시설 (회색)</option>
            <option value="facility-room">회의실/사무실 (보라)</option>
            <option value="facility-equip">장비 (노랑)</option>
          </select>
        </div>
        <div class="modal-buttons">
          <button @click="closeFacilityModal" class="btn-secondary">취소</button>
          <button @click="saveFacility" class="btn-primary">저장</button>
        </div>
      </div>
    </div>

    <!-- 사용자 정보 모달 (클릭) -->
    <div v-if="showUserInfoModal" class="modal-overlay" @click.self="closeUserInfoModal">
      <div class="modal modal-large">
        <div class="modal-header">
          <h3>👤 {{ selectedSeat?.name || '사용자 정보' }}</h3>
          <span class="seat-code">{{ selectedSeat?.code }}</span>
        </div>

        <!-- 로딩 상태 -->
        <div v-if="loadingUserInfo" class="loading-state">
          <div class="spinner"></div>
          <p>정보를 불러오는 중...</p>
        </div>

        <!-- 사용자를 찾을 수 없는 경우 -->
        <div v-else-if="!userInfo" class="no-user-state">
          <div class="no-user-icon">❓</div>
          <p>등록된 사용자를 찾을 수 없습니다.</p>
          <p class="hint">이름: <strong>{{ selectedSeat?.name }}</strong></p>
          <button @click="goToUserManagement" class="btn-primary">사용자 관리에서 등록하기</button>
        </div>

        <!-- 사용자 정보 표시 -->
        <div v-else class="user-info-content">
          <!-- 기본 정보 -->
          <div class="info-section">
            <h4>기본 정보</h4>
            <div class="info-grid">
              <div class="info-item">
                <label>이름</label>
                <span>{{ userInfo.name }}</span>
              </div>
              <div class="info-item">
                <label>부서</label>
                <span>{{ userInfo.department }}</span>
              </div>
              <div class="info-item">
                <label>위치</label>
                <span>{{ userInfo.location || '-' }}</span>
              </div>
              <div class="info-item">
                <label>전화번호</label>
                <span>{{ userInfo.phone || '-' }}</span>
              </div>
              <div class="info-item">
                <label>이메일</label>
                <span>{{ userInfo.email || '-' }}</span>
              </div>
            </div>
          </div>

          <!-- 할당된 장비 -->
          <div class="info-section">
            <h4>사용중인 장비 ({{ userAssignments.length }}개)</h4>
            <div v-if="userAssignments.length > 0" class="equipment-list">
              <div v-for="assignment in userAssignments" :key="assignment.id" class="equipment-card">
                <div class="equipment-main">
                  <span class="asset-number">{{ assignment.equipment.asset_number }}</span>
                  <span class="model-name">{{ assignment.equipment.model_name }}</span>
                  <span :class="['category-tag', 'cat-' + assignment.equipment.category]">
                    {{ assignment.equipment.category }}
                  </span>
                </div>
                <div class="equipment-sub">
                  <span>할당일: {{ formatDate(assignment.assignment_date) }}</span>
                  <span v-if="assignment.equipment.network_type" :class="['network-tag', getNetworkClass(assignment.equipment.network_type)]">
                    {{ assignment.equipment.network_type }}
                  </span>
                </div>
              </div>
            </div>
            <div v-else class="no-equipment">
              <p>할당된 장비가 없습니다.</p>
            </div>
          </div>

          <!-- 버튼 -->
          <div class="modal-actions">
            <button @click="goToUserDetail" class="btn-primary">사용자 관리에서 상세보기</button>
            <button @click="closeUserInfoModal" class="btn-secondary">닫기</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000/api'

export default {
  name: 'FloorPlan',
  data() {
    return {
      items: [],
      itemIdCounter: 1,
      deleteMode: false,
      saving: false,
      lastSaved: null,
      hasUnsavedChanges: false,
      
      // 검색
      searchQuery: '',
      searchResults: [],
      currentSearchIndex: 0,
      
      // 드래그
      dragItem: null,
      dragOffsetX: 0,
      dragOffsetY: 0,
      isDragging: false,
      
      // 리사이즈
      resizeItem: null,
      resizeStartX: 0,
      resizeStartY: 0,
      resizeStartW: 0,
      resizeStartH: 0,
      
      // 좌석 수정 모달
      showSeatModal: false,
      editingSeat: {},
      currentEditId: null,
      
      // 시설 수정 모달
      showFacilityModal: false,
      editingFacility: {},
      
      // 사용자 정보 모달
      showUserInfoModal: false,
      selectedSeat: null,
      userInfo: null,
      userAssignments: [],
      loadingUserInfo: false
    }
  },
  mounted() {
    this.loadFromServer()
    document.addEventListener('keydown', this.handleKeydown)
    window.addEventListener('beforeunload', this.handleBeforeUnload)
  },
  beforeUnmount() {
    document.removeEventListener('keydown', this.handleKeydown)
    window.removeEventListener('beforeunload', this.handleBeforeUnload)
  },
  methods: {
    // ===== 서버 통신 =====
    async loadFromServer() {
      try {
        const response = await axios.get(`${API_BASE}/floorplan`)
        if (response.data && response.data.items) {
          this.items = response.data.items
          this.itemIdCounter = response.data.itemIdCounter || 1
        } else {
          this.createDefaultItems()
        }
        this.hasUnsavedChanges = false
      } catch (error) {
        console.error('배치도 로드 실패:', error)
        this.loadFromStorage()
      }
    },
    
    async saveToServer() {
      this.saving = true
      try {
        await axios.post(`${API_BASE}/floorplan`, {
          items: this.items,
          itemIdCounter: this.itemIdCounter
        })
        this.lastSaved = new Date().toLocaleTimeString('ko-KR')
        this.hasUnsavedChanges = false
        this.saveToStorage()
      } catch (error) {
        console.error('저장 실패:', error)
        alert('서버 저장에 실패했습니다. 로컬에 백업 저장합니다.')
        this.saveToStorage()
      } finally {
        this.saving = false
      }
    },
    
    loadFromStorage() {
      const saved = localStorage.getItem('floorPlanData')
      if (saved) {
        const data = JSON.parse(saved)
        this.items = data.items || []
        this.itemIdCounter = data.itemIdCounter || 1
      } else {
        this.createDefaultItems()
      }
    },
    
    saveToStorage() {
      localStorage.setItem('floorPlanData', JSON.stringify({
        items: this.items,
        itemIdCounter: this.itemIdCounter
      }))
    },
    
    markUnsaved() {
      this.hasUnsavedChanges = true
    },
    
    handleBeforeUnload(e) {
      if (this.hasUnsavedChanges) {
        e.preventDefault()
        e.returnValue = ''
      }
    },
    
    createDefaultItems() {
      const defaultSeats = [
        { code: 'C-1', name: '유성은', x: 540, y: 80 },
        { code: 'C-2', name: '김진솔', x: 620, y: 80 },
        { code: 'C-3', name: '이정선', x: 700, y: 80 },
        { code: 'C-4', name: '정원화', x: 540, y: 140 },
        { code: 'C-5', name: '박수정', x: 620, y: 140 },
        { code: 'C-6', name: '오상은', x: 700, y: 140 },
      ]
      
      defaultSeats.forEach(s => {
        this.items.push({
          id: this.itemIdCounter++,
          type: 'seat',
          code: s.code,
          name: s.name,
          x: s.x,
          y: s.y,
          width: 70,
          height: 50
        })
      })
      
      this.items.push({
        id: this.itemIdCounter++,
        type: 'facility',
        name: '남자화장실',
        facilityType: 'facility',
        x: 20, y: 50, width: 100, height: 80
      })
      
      this.items.push({
        id: this.itemIdCounter++,
        type: 'facility',
        name: '여자화장실',
        facilityType: 'facility',
        x: 20, y: 150, width: 100, height: 80
      })
      
      this.items.push({
        id: this.itemIdCounter++,
        type: 'facility',
        name: '메인 전산실\nC-121',
        facilityType: 'facility-room',
        x: 350, y: 20, width: 150, height: 80
      })
      
      this.markUnsaved()
    },
    
    // ===== 스타일 헬퍼 =====
    getItemClass(item) {
      if (item.type === 'seat') return 'seat'
      return item.facilityType || 'facility'
    },
    
    getItemStyle(item) {
      return {
        left: item.x + 'px',
        top: item.y + 'px',
        width: item.width + 'px',
        height: item.height + 'px'
      }
    },
    
    formatText(text) {
      return (text || '').replace(/\n/g, '<br>')
    },
    
    formatDate(dateStr) {
      if (!dateStr) return '-'
      return dateStr.split('T')[0]
    },
    
    getNetworkClass(networkType) {
      if (!networkType) return ''
      if (networkType.includes('내부') || networkType.includes('업무')) return 'network-internal'
      if (networkType.includes('인터넷') || networkType.includes('외부')) return 'network-external'
      return 'network-default'
    },
    
    // ===== 아이템 클릭 =====
    onItemClick(e, item) {
      // 드래그 중이면 무시
      if (this.isDragging) return
      
      // 삭제 모드면 삭제 처리
      if (this.deleteMode) {
        this.deleteItem(item.id)
        return
      }
      
      // 좌석이면 사용자 정보 모달 표시
      if (item.type === 'seat' && item.name) {
        this.openUserInfoModal(item)
      }
    },
    
    // ===== 사용자 정보 모달 =====
    async openUserInfoModal(seat) {
      this.selectedSeat = seat
      this.showUserInfoModal = true
      this.loadingUserInfo = true
      this.userInfo = null
      this.userAssignments = []
      
      try {
        // 사용자 검색
        const userResponse = await axios.get(`${API_BASE}/users/search`, {
          params: { name: seat.name }
        })
        
        if (userResponse.data && userResponse.data.length > 0) {
          this.userInfo = userResponse.data[0]
          
          // 사용자의 장비 할당 정보 조회
          const assignmentResponse = await axios.get(`${API_BASE}/assignments/user/${this.userInfo.id}`)
          this.userAssignments = assignmentResponse.data.filter(a => a.status === '사용중')
        }
      } catch (error) {
        console.error('사용자 정보 로드 실패:', error)
      } finally {
        this.loadingUserInfo = false
      }
    },
    
    closeUserInfoModal() {
      this.showUserInfoModal = false
      this.selectedSeat = null
      this.userInfo = null
      this.userAssignments = []
    },
    
    goToUserManagement() {
      this.closeUserInfoModal()
      // App.vue의 currentView를 변경하기 위해 이벤트 발생
      this.$emit('navigate', 'users')
    },
    
    goToUserDetail() {
      this.closeUserInfoModal()
      // 사용자 관리 페이지로 이동하면서 선택된 사용자 정보 전달
      this.$emit('navigate', 'users', { userId: this.userInfo?.id })
    },
    
    // ===== 아이템 추가 =====
    addSeat() {
      const newSeat = {
        id: this.itemIdCounter++,
        type: 'seat',
        code: `C-${this.itemIdCounter}`,
        name: '',
        x: 100,
        y: 100,
        width: 70,
        height: 50
      }
      this.items.push(newSeat)
      this.markUnsaved()
      this.editItem(newSeat)
    },
    
    addFacility() {
      const newFacility = {
        id: this.itemIdCounter++,
        type: 'facility',
        name: '새 시설',
        facilityType: 'facility',
        x: 100,
        y: 100,
        width: 100,
        height: 60
      }
      this.items.push(newFacility)
      this.markUnsaved()
      this.editItem(newFacility)
    },
    
    // ===== 아이템 수정 (더블클릭) =====
    editItem(item) {
      if (this.deleteMode) {
        this.deleteItem(item.id)
        return
      }
      
      this.currentEditId = item.id
      
      if (item.type === 'seat') {
        this.editingSeat = { code: item.code, name: item.name }
        this.showSeatModal = true
      } else {
        this.editingFacility = { name: item.name, facilityType: item.facilityType }
        this.showFacilityModal = true
      }
    },
    
    saveSeat() {
      const item = this.items.find(i => i.id === this.currentEditId)
      if (item) {
        item.code = this.editingSeat.code
        item.name = this.editingSeat.name
        this.markUnsaved()
      }
      this.closeSeatModal()
    },
    
    saveFacility() {
      const item = this.items.find(i => i.id === this.currentEditId)
      if (item) {
        item.name = this.editingFacility.name
        item.facilityType = this.editingFacility.facilityType
        this.markUnsaved()
      }
      this.closeFacilityModal()
    },
    
    closeSeatModal() {
      this.showSeatModal = false
      this.editingSeat = {}
      this.currentEditId = null
    },
    
    closeFacilityModal() {
      this.showFacilityModal = false
      this.editingFacility = {}
      this.currentEditId = null
    },
    
    // ===== 삭제 =====
    toggleDeleteMode() {
      this.deleteMode = !this.deleteMode
    },
    
    deleteItem(id) {
      if (confirm('이 항목을 삭제하시겠습니까?')) {
        this.items = this.items.filter(i => i.id !== id)
        this.markUnsaved()
      }
    },
    
    // ===== 드래그 =====
    startDrag(e, item) {
      if (e.target.classList.contains('resize-handle')) return
      
      this.dragItem = item
      this.isDragging = false
      const rect = e.target.closest('.item').getBoundingClientRect()
      this.dragOffsetX = e.clientX - rect.left
      this.dragOffsetY = e.clientY - rect.top
    },
    
    onDrag(e) {
      if (this.dragItem) {
        this.isDragging = true
        const canvas = this.$refs.canvas
        const canvasRect = canvas.getBoundingClientRect()
        
        let newX = e.clientX - canvasRect.left - this.dragOffsetX
        let newY = e.clientY - canvasRect.top - this.dragOffsetY
        
        newX = Math.round(newX / 20) * 20
        newY = Math.round(newY / 20) * 20
        
        newX = Math.max(0, Math.min(newX, canvasRect.width - this.dragItem.width))
        newY = Math.max(0, Math.min(newY, canvasRect.height - this.dragItem.height))
        
        this.dragItem.x = newX
        this.dragItem.y = newY
      }
      
      if (this.resizeItem) {
        let newW = this.resizeStartW + (e.clientX - this.resizeStartX)
        let newH = this.resizeStartH + (e.clientY - this.resizeStartY)
        
        newW = Math.max(50, Math.round(newW / 20) * 20)
        newH = Math.max(30, Math.round(newH / 20) * 20)
        
        this.resizeItem.width = newW
        this.resizeItem.height = newH
      }
    },
    
    endDrag() {
      if (this.dragItem || this.resizeItem) {
        this.markUnsaved()
      }
      
      // 잠시 후 isDragging 리셋 (클릭 이벤트와 구분하기 위해)
      setTimeout(() => {
        this.isDragging = false
      }, 100)
      
      this.dragItem = null
      this.resizeItem = null
    },
    
    // ===== 리사이즈 =====
    startResize(e, item) {
      this.resizeItem = item
      this.resizeStartX = e.clientX
      this.resizeStartY = e.clientY
      this.resizeStartW = item.width
      this.resizeStartH = item.height
    },
    
    // ===== 내보내기/가져오기 =====
    exportData() {
      const dataStr = JSON.stringify({ items: this.items, itemIdCounter: this.itemIdCounter }, null, 2)
      const blob = new Blob([dataStr], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = '배치도_' + new Date().toISOString().slice(0, 10) + '.json'
      a.click()
      URL.revokeObjectURL(url)
    },
    
    triggerImport() {
      this.$refs.fileInput.click()
    },
    
    importData(event) {
      const file = event.target.files[0]
      if (!file) return
      
      const reader = new FileReader()
      reader.onload = (e) => {
        try {
          const data = JSON.parse(e.target.result)
          this.items = data.items || []
          this.itemIdCounter = data.itemIdCounter || 1
          this.markUnsaved()
          alert('배치도를 불러왔습니다. 저장 버튼을 눌러 서버에 저장하세요.')
        } catch (err) {
          alert('파일을 읽을 수 없습니다.')
        }
      }
      reader.readAsText(file)
      event.target.value = ''
    },
    
    resetAll() {
      if (confirm('모든 배치를 초기화하시겠습니까?\n이 작업은 되돌릴 수 없습니다.')) {
        this.items = []
        this.itemIdCounter = 1
        this.createDefaultItems()
      }
    },
    
    // ===== 키보드 =====
    handleKeydown(e) {
      if (e.key === 'Escape') {
        this.closeSeatModal()
        this.closeFacilityModal()
        this.closeUserInfoModal()
        if (this.deleteMode) this.deleteMode = false
      }
      if (e.ctrlKey && e.key === 's') {
        e.preventDefault()
        this.saveToServer()
      }
      // Ctrl+F로 검색창 포커스
      if (e.ctrlKey && e.key === 'f') {
        e.preventDefault()
        document.querySelector('.search-input')?.focus()
      }
    },
    
    // ===== 검색 =====
    search() {
      if (!this.searchQuery.trim()) {
        this.clearSearch()
        return
      }
      
      const query = this.searchQuery.toLowerCase().trim()
      
      this.searchResults = this.items.filter(item => {
        if (item.type === 'seat') {
          return (item.name && item.name.toLowerCase().includes(query)) ||
                 (item.code && item.code.toLowerCase().includes(query))
        }
        return item.name && item.name.toLowerCase().includes(query)
      })
      
      this.currentSearchIndex = 0
      
      if (this.searchResults.length > 0) {
        this.scrollToResult()
      } else {
        alert('검색 결과가 없습니다.')
      }
    },
    
    onSearchInput() {
      // 입력 중에는 실시간 검색하지 않음 (Enter나 버튼 클릭 시에만)
      if (!this.searchQuery.trim()) {
        this.clearSearch()
      }
    },
    
    clearSearch() {
      this.searchQuery = ''
      this.searchResults = []
      this.currentSearchIndex = 0
    },
    
    prevResult() {
      if (this.searchResults.length > 0) {
        this.currentSearchIndex = (this.currentSearchIndex - 1 + this.searchResults.length) % this.searchResults.length
        this.scrollToResult()
      }
    },
    
    nextResult() {
      if (this.searchResults.length > 0) {
        this.currentSearchIndex = (this.currentSearchIndex + 1) % this.searchResults.length
        this.scrollToResult()
      }
    },
    
    scrollToResult() {
      const currentItem = this.searchResults[this.currentSearchIndex]
      if (currentItem && this.$refs.canvas) {
        const canvas = this.$refs.canvas
        // 해당 아이템이 캔버스 중앙에 오도록 스크롤
        const scrollLeft = currentItem.x - (canvas.clientWidth / 2) + (currentItem.width / 2)
        const scrollTop = currentItem.y - (canvas.clientHeight / 2) + (currentItem.height / 2)
        
        canvas.scrollTo({
          left: Math.max(0, scrollLeft),
          top: Math.max(0, scrollTop),
          behavior: 'smooth'
        })
      }
    },
    
    isSearchResult(item) {
      return this.searchResults.some(r => r.id === item.id)
    },
    
    isCurrentSearchResult(item) {
      return this.searchResults.length > 0 && 
             this.searchResults[this.currentSearchIndex]?.id === item.id
    }
  }
}
</script>

<style scoped>
.floor-plan-editor {
  padding: 0;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.toolbar h2 {
  margin: 0;
  color: #2c3e50;
}

/* 검색 영역 */
.search-area {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.search-input {
  padding: 0.5rem 1rem;
  border: 2px solid #ddd;
  border-radius: 20px;
  font-size: 0.9rem;
  width: 200px;
  transition: all 0.2s;
}

.search-input:focus {
  outline: none;
  border-color: #3498db;
  box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.2);
}

.btn-search {
  padding: 0.5rem 1rem;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 20px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s;
}

.btn-search:hover {
  background: #2980b9;
}

.btn-clear {
  padding: 0.5rem 0.75rem;
  background: #e74c3c;
  color: white;
  border: none;
  border-radius: 20px;
  cursor: pointer;
  font-size: 0.85rem;
}

.btn-clear:hover {
  background: #c0392b;
}

.search-result-count {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
  color: #2c3e50;
  background: #ecf0f1;
  padding: 0.4rem 0.75rem;
  border-radius: 20px;
}

.btn-nav {
  padding: 0.25rem 0.5rem;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.8rem;
}

.btn-nav:disabled {
  background: #bdc3c7;
  cursor: not-allowed;
}

.btn-nav:not(:disabled):hover {
  background: #2980b9;
}

.toolbar-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.toolbar-buttons button {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s;
}

.toolbar-buttons button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 3px 10px rgba(0,0,0,0.2);
}

.toolbar-buttons button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary { background: #3498db; color: white; }
.btn-secondary { background: #95a5a6; color: white; }
.btn-warning { background: #f39c12; color: white; }
.btn-warning.active { background: #e74c3c; box-shadow: 0 0 15px rgba(231, 76, 60, 0.5); }
.btn-danger { background: #e74c3c; color: white; }

.status-bar {
  display: flex;
  gap: 1rem;
  margin-bottom: 0.5rem;
  font-size: 0.85rem;
}

.save-status { color: #27ae60; }
.unsaved-status { color: #e67e22; font-weight: 500; }

.help-text {
  text-align: center;
  color: #7f8c8d;
  font-size: 0.85rem;
  margin-bottom: 1rem;
}

.canvas-container {
  background: #f8f9fa;
  border-radius: 12px;
  position: relative;
  width: 100%;
  height: 700px;
  overflow: auto;
  background-image: 
    linear-gradient(rgba(200,200,200,0.3) 1px, transparent 1px),
    linear-gradient(90deg, rgba(200,200,200,0.3) 1px, transparent 1px);
  background-size: 20px 20px;
  border: 1px solid #ddd;
}

.item {
  position: absolute;
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  text-align: center;
  cursor: move;
  user-select: none;
  transition: box-shadow 0.2s;
  overflow: hidden;
  padding: 4px;
  line-height: 1.3;
}

.item:hover {
  box-shadow: 0 5px 20px rgba(0,0,0,0.25);
  z-index: 100;
}

.item.dragging {
  opacity: 0.8;
  z-index: 1000;
  box-shadow: 0 10px 30px rgba(0,0,0,0.3);
}

.item.selected {
  box-shadow: 0 0 0 3px #3498db;
}

.item.search-highlight {
  box-shadow: 0 0 0 3px #f39c12;
  animation: pulse 1s ease-in-out infinite;
}

.item.search-current {
  box-shadow: 0 0 0 4px #e74c3c;
  animation: pulse-strong 0.8s ease-in-out infinite;
  z-index: 150;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.02); }
}

@keyframes pulse-strong {
  0%, 100% { transform: scale(1); box-shadow: 0 0 0 4px #e74c3c; }
  50% { transform: scale(1.05); box-shadow: 0 0 15px 4px rgba(231, 76, 60, 0.6); }
}

.item.delete-mode:hover {
  box-shadow: 0 0 20px rgba(255, 0, 0, 0.6);
  cursor: pointer;
}

.seat {
  background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
  border: 2px solid #1976d2;
  color: #1565c0;
  cursor: pointer;
}

.seat .name { font-weight: 600; font-size: 11px; }
.seat .code { font-size: 9px; opacity: 0.7; }

.facility {
  background: linear-gradient(135deg, #78909c 0%, #546e7a 100%);
  border: 2px solid #37474f;
  color: white;
  font-weight: 500;
}

.facility-room {
  background: linear-gradient(135deg, #ce93d8 0%, #ba68c8 100%);
  border: 2px solid #8e24aa;
  color: #4a148c;
  font-weight: 500;
}

.facility-equip {
  background: linear-gradient(135deg, #fff176 0%, #ffd54f 100%);
  border: 2px solid #f9a825;
  color: #5d4037;
  font-weight: 500;
}

.resize-handle {
  position: absolute;
  width: 12px;
  height: 12px;
  background: #1976d2;
  border-radius: 2px;
  bottom: 2px;
  right: 2px;
  cursor: se-resize;
  opacity: 0;
  transition: opacity 0.2s;
}

.item:hover .resize-handle { opacity: 1; }

.legend {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 1.5rem;
  margin-top: 1rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 8px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
  color: #555;
}

.legend-color {
  width: 24px;
  height: 24px;
  border-radius: 4px;
}

.legend-seat { background: linear-gradient(135deg, #e3f2fd, #bbdefb); border: 2px solid #1976d2; }
.legend-facility { background: linear-gradient(135deg, #78909c, #546e7a); }
.legend-room { background: linear-gradient(135deg, #ce93d8, #ba68c8); }
.legend-equip { background: linear-gradient(135deg, #fff176, #ffd54f); }

/* 모달 공통 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.modal {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  min-width: 320px;
  max-width: 90vw;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 40px rgba(0,0,0,0.3);
}

.modal-large {
  width: 500px;
}

.modal h3 {
  margin: 0 0 1.5rem 0;
  color: #2c3e50;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #eee;
}

.modal-header h3 {
  margin: 0;
}

.seat-code {
  background: #e3f2fd;
  color: #1976d2;
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 600;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  color: #555;
  font-weight: 500;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 1rem;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #3498db;
}

.modal-buttons {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
  margin-top: 1.5rem;
}

.modal-buttons button {
  padding: 0.6rem 1.2rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.95rem;
}

/* 로딩 상태 */
.loading-state {
  text-align: center;
  padding: 2rem;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 사용자 없음 상태 */
.no-user-state {
  text-align: center;
  padding: 2rem;
}

.no-user-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.no-user-state .hint {
  color: #7f8c8d;
  margin: 1rem 0;
}

/* 사용자 정보 */
.user-info-content {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.info-section h4 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
  font-size: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid #3498db;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.info-item label {
  font-size: 0.8rem;
  color: #7f8c8d;
}

.info-item span {
  font-size: 0.95rem;
  color: #2c3e50;
}

/* 장비 목록 */
.equipment-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.equipment-card {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 0.75rem 1rem;
  border-left: 4px solid #3498db;
}

.equipment-main {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}

.asset-number {
  font-family: monospace;
  font-weight: 600;
  color: #3498db;
}

.model-name {
  color: #2c3e50;
}

.category-tag {
  font-size: 0.75rem;
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
  background: #ecf0f1;
  color: #7f8c8d;
}

.equipment-sub {
  display: flex;
  gap: 1rem;
  font-size: 0.8rem;
  color: #7f8c8d;
}

.network-tag {
  padding: 0.1rem 0.4rem;
  border-radius: 3px;
  font-size: 0.75rem;
}

.network-internal { background: #3498db; color: white; }
.network-external { background: #e74c3c; color: white; }
.network-default { background: #9b59b6; color: white; }

.no-equipment {
  text-align: center;
  padding: 1.5rem;
  color: #7f8c8d;
  background: #f8f9fa;
  border-radius: 8px;
}

.modal-actions {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
  padding-top: 1rem;
  border-top: 1px solid #eee;
}

.modal-actions button {
  padding: 0.6rem 1.2rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.95rem;
}
</style>
