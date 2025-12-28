<template>
  <div class="floor-plan-editor">
    <div class="toolbar">
      
      <div class="toolbar-row">
        <h2>좌석 배치도</h2>
        
        <!-- 층 선택 탭 추가 -->
        <div class="floor-tabs">
          <button 
            v-for="floor in floors" 
            :key="floor.id"
            :class="['floor-tab', { active: currentFloor === floor.id }]"
            @click="changeFloor(floor.id)"
          >
            {{ floor.name }}
          </button>
        </div>
      </div>

      <div class="toolbar-row">
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
          <button @click="resetCurrentFloor" class="btn-danger">🔄 현재 층 초기화</button>
          <input 
            type="file" 
            ref="fileInput" 
            accept=".json" 
            @change="importData" 
            style="display: none"
          >
        </div>
      </div>

      <div class="toolbar-row">
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
          <label class="search-all-floors">
            <input type="checkbox" v-model="searchAllFloors">
            전체 층 검색
          </label>
          <button @click="search" class="btn-search">🔍 검색</button>
          <button v-if="searchResults.length > 0" @click="clearSearch" class="btn-clear">✕ 초기화</button>
          <span v-if="searchResults.length > 0" class="search-result-count">
            {{ currentSearchIndex + 1 }} / {{ searchResults.length }}건
            <template v-if="searchAllFloors && searchResults[currentSearchIndex]">
              ({{ getFloorName(searchResults[currentSearchIndex].floor) }})
            </template>
            <button @click="prevResult" class="btn-nav" :disabled="searchResults.length <= 1">◀</button>
            <button @click="nextResult" class="btn-nav" :disabled="searchResults.length <= 1">▶</button>
          </span>
        </div>
      </div>

    </div>

    <div class="status-bar">
      <span class="current-floor-indicator">
        📍 현재: <strong>{{ getFloorName(currentFloor) }}</strong>
        (좌석 {{ currentFloorItems.filter(i => i.type === 'seat').length }}개, 
         시설 {{ currentFloorItems.filter(i => i.type === 'facility').length }}개)
      </span>
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
        v-for="item in currentFloorItems"
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
          <span class="seat-code">{{ selectedSeat?.code }} ({{ getFloorName(selectedSeat?.floor) }})</span>
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
                <span>{{ getFloorName(selectedSeat?.floor) }}</span>
              </div>
            </div>
          </div>

          <!-- 장비 목록 -->
          <div class="info-section">
            <h4>배정 장비</h4>
            <div v-if="userAssignments.length > 0" class="equipment-list">
              <div v-for="eq in userAssignments" :key="eq.id" class="equipment-card">
                <div class="equipment-main">
                  <span class="asset-number">{{ eq.asset_number }}</span>
                  <span class="model-name">{{ eq.model_name }}</span>
                  <span class="category-tag">{{ eq.category }}</span>
                </div>
                <div class="equipment-sub">
                  <span v-if="eq.ip_address">IP: {{ eq.ip_address }}</span>
                  <span v-if="eq.network_type" :class="['network-tag', getNetworkClass(eq.network_type)]">
                    {{ eq.network_type }}
                  </span>
                </div>
              </div>
            </div>
            <div v-else class="no-equipment">
              배정된 장비가 없습니다.
            </div>
          </div>

          <div class="modal-actions">
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
      // 층 정보
      floors: [
        { id: 14, name: '14층' },
        { id: 15, name: '15층' },
        { id: 16, name: '16층' }
      ],
      currentFloor: 15, // 기본 선택 층
      
      // 전체 데이터 (층별로 관리)
      floorData: {
        14: { items: [], itemIdCounter: 1 },
        15: { items: [], itemIdCounter: 1 },
        16: { items: [], itemIdCounter: 1 }
      },
      
      deleteMode: false,
      saving: false,
      lastSaved: null,
      hasUnsavedChanges: false,
      
      // 검색
      searchQuery: '',
      searchResults: [],
      currentSearchIndex: 0,
      searchAllFloors: false,
      
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
  
  computed: {
    // 현재 층의 아이템들
    currentFloorItems() {
      return this.floorData[this.currentFloor]?.items || []
    },
    
    // 현재 층의 itemIdCounter
    currentItemIdCounter: {
      get() {
        return this.floorData[this.currentFloor]?.itemIdCounter || 1
      },
      set(val) {
        if (this.floorData[this.currentFloor]) {
          this.floorData[this.currentFloor].itemIdCounter = val
        }
      }
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
    // ===== 층 관련 =====
    getFloorName(floorId) {
      const floor = this.floors.find(f => f.id === floorId)
      return floor ? floor.name : `${floorId}층`
    },
    
    changeFloor(floorId) {
      if (this.currentFloor === floorId) return
      
      // 저장되지 않은 변경사항 확인
      if (this.hasUnsavedChanges) {
        if (!confirm('저장되지 않은 변경사항이 있습니다. 층을 변경하시겠습니까?')) {
          return
        }
      }
      
      this.currentFloor = floorId
      this.clearSearch()
    },
    
    // ===== 서버 통신 =====
    async loadFromServer() {
      try {
        const response = await axios.get(`${API_BASE}/floorplan/all`)
        if (response.data && response.data.floors) {
          // 층별 데이터 로드
          this.floors.forEach(floor => {
            if (response.data.floors[floor.id]) {
              this.floorData[floor.id] = response.data.floors[floor.id]
            }
          })
        } else {
          // 기존 단일 배치도 데이터 마이그레이션
          await this.migrateOldData()
        }
        this.hasUnsavedChanges = false
      } catch (error) {
        console.error('배치도 로드 실패:', error)
        // 기존 API로 폴백
        await this.loadFromLegacyAPI()
      }
    },
    
    async loadFromLegacyAPI() {
      try {
        const response = await axios.get(`${API_BASE}/floorplan`)
        if (response.data && response.data.items) {
          // 기존 데이터를 15층에 배치 (마이그레이션)
          this.floorData[15] = {
            items: response.data.items.map(item => ({ ...item, floor: 15 })),
            itemIdCounter: response.data.itemIdCounter || 1
          }
        }
        this.hasUnsavedChanges = false
      } catch (error) {
        console.error('기존 API 로드도 실패:', error)
        this.loadFromStorage()
      }
    },
    
    async migrateOldData() {
      try {
        const response = await axios.get(`${API_BASE}/floorplan`)
        if (response.data && response.data.items && response.data.items.length > 0) {
          // 기존 데이터가 있으면 15층으로 마이그레이션
          this.floorData[15] = {
            items: response.data.items.map(item => ({ ...item, floor: 15 })),
            itemIdCounter: response.data.itemIdCounter || 1
          }
        }
      } catch (error) {
        console.log('마이그레이션 대상 데이터 없음')
      }
    },
    
    async saveToServer() {
      this.saving = true
      try {
        // 층별 데이터 저장
        await axios.post(`${API_BASE}/floorplan/all`, {
          floors: this.floorData
        })
        this.lastSaved = new Date().toLocaleTimeString('ko-KR')
        this.hasUnsavedChanges = false
        this.saveToStorage()
      } catch (error) {
        console.error('저장 실패:', error)
        // 기존 API로 폴백 (현재 층만 저장)
        try {
          await axios.post(`${API_BASE}/floorplan`, {
            items: this.currentFloorItems,
            itemIdCounter: this.currentItemIdCounter
          })
          this.lastSaved = new Date().toLocaleTimeString('ko-KR')
          this.hasUnsavedChanges = false
        } catch (fallbackError) {
          alert('서버 저장에 실패했습니다. 로컬에 백업 저장합니다.')
          this.saveToStorage()
        }
      }
      this.saving = false
    },
    
    // 로컬 스토리지 백업
    saveToStorage() {
      try {
        localStorage.setItem('floorplan_data', JSON.stringify(this.floorData))
      } catch (e) {
        console.error('로컬 저장 실패:', e)
      }
    },
    
    loadFromStorage() {
      try {
        const saved = localStorage.getItem('floorplan_data')
        if (saved) {
          this.floorData = JSON.parse(saved)
        }
      } catch (e) {
        console.error('로컬 데이터 로드 실패:', e)
      }
    },
    
    // ===== 아이템 추가 =====
    addSeat() {
      const newSeat = {
        id: this.currentItemIdCounter++,
        type: 'seat',
        code: '',
        name: '',
        floor: this.currentFloor,
        x: 100,
        y: 100,
        width: 70,
        height: 50
      }
      this.floorData[this.currentFloor].items.push(newSeat)
      this.markUnsaved()
    },
    
    addFacility() {
      const newFacility = {
        id: this.currentItemIdCounter++,
        type: 'facility',
        name: '시설',
        facilityType: 'facility',
        floor: this.currentFloor,
        x: 100,
        y: 100,
        width: 100,
        height: 80
      }
      this.floorData[this.currentFloor].items.push(newFacility)
      this.markUnsaved()
    },
    
    // ===== 아이템 수정/삭제 =====
    editItem(item) {
      if (item.type === 'seat') {
        this.editingSeat = { ...item }
        this.currentEditId = item.id
        this.showSeatModal = true
      } else {
        this.editingFacility = { ...item }
        this.currentEditId = item.id
        this.showFacilityModal = true
      }
    },
    
    saveSeat() {
      const idx = this.currentFloorItems.findIndex(i => i.id === this.currentEditId)
      if (idx !== -1) {
        this.floorData[this.currentFloor].items[idx].code = this.editingSeat.code
        this.floorData[this.currentFloor].items[idx].name = this.editingSeat.name
        this.markUnsaved()
      }
      this.closeSeatModal()
    },
    
    closeSeatModal() {
      this.showSeatModal = false
      this.editingSeat = {}
      this.currentEditId = null
    },
    
    saveFacility() {
      const idx = this.currentFloorItems.findIndex(i => i.id === this.currentEditId)
      if (idx !== -1) {
        this.floorData[this.currentFloor].items[idx].name = this.editingFacility.name
        this.floorData[this.currentFloor].items[idx].facilityType = this.editingFacility.facilityType
        this.markUnsaved()
      }
      this.closeFacilityModal()
    },
    
    closeFacilityModal() {
      this.showFacilityModal = false
      this.editingFacility = {}
      this.currentEditId = null
    },
    
    deleteItem(id) {
      if (confirm('이 항목을 삭제하시겠습니까?')) {
        const idx = this.currentFloorItems.findIndex(i => i.id === id)
        if (idx !== -1) {
          this.floorData[this.currentFloor].items.splice(idx, 1)
          this.markUnsaved()
        }
      }
    },
    
    toggleDeleteMode() {
      this.deleteMode = !this.deleteMode
    },
    
    resetCurrentFloor() {
      if (confirm(`${this.getFloorName(this.currentFloor)} 배치도를 초기화하시겠습니까?`)) {
        this.floorData[this.currentFloor] = {
          items: [],
          itemIdCounter: 1
        }
        this.markUnsaved()
      }
    },
    
    markUnsaved() {
      this.hasUnsavedChanges = true
    },
    
    // ===== 드래그 =====
    startDrag(e, item) {
      if (this.deleteMode) return
      
      this.dragItem = item
      this.dragOffsetX = e.clientX - item.x
      this.dragOffsetY = e.clientY - item.y
      this.isDragging = false
    },
    
    onDrag(e) {
      if (!this.dragItem) return
      
      this.isDragging = true
      const idx = this.currentFloorItems.findIndex(i => i.id === this.dragItem.id)
      if (idx !== -1) {
        const canvas = this.$refs.canvas
        const rect = canvas.getBoundingClientRect()
        
        let newX = e.clientX - rect.left - this.dragOffsetX + canvas.scrollLeft
        let newY = e.clientY - rect.top - this.dragOffsetY + canvas.scrollTop
        
        // 경계 체크
        newX = Math.max(0, newX)
        newY = Math.max(0, newY)
        
        this.floorData[this.currentFloor].items[idx].x = newX
        this.floorData[this.currentFloor].items[idx].y = newY
        this.markUnsaved()
      }
    },
    
    endDrag() {
      this.dragItem = null
      setTimeout(() => {
        this.isDragging = false
      }, 100)
    },
    
    // ===== 리사이즈 =====
    startResize(e, item) {
      this.resizeItem = item
      this.resizeStartX = e.clientX
      this.resizeStartY = e.clientY
      this.resizeStartW = item.width
      this.resizeStartH = item.height
      
      document.addEventListener('mousemove', this.onResize)
      document.addEventListener('mouseup', this.endResize)
    },
    
    onResize(e) {
      if (!this.resizeItem) return
      
      const idx = this.currentFloorItems.findIndex(i => i.id === this.resizeItem.id)
      if (idx !== -1) {
        const deltaX = e.clientX - this.resizeStartX
        const deltaY = e.clientY - this.resizeStartY
        
        this.floorData[this.currentFloor].items[idx].width = Math.max(40, this.resizeStartW + deltaX)
        this.floorData[this.currentFloor].items[idx].height = Math.max(30, this.resizeStartH + deltaY)
        this.markUnsaved()
      }
    },
    
    endResize() {
      this.resizeItem = null
      document.removeEventListener('mousemove', this.onResize)
      document.removeEventListener('mouseup', this.endResize)
    },
    
    // ===== 검색 =====
    search() {
      const query = this.searchQuery.trim().toLowerCase()
      if (!query) {
        this.clearSearch()
        return
      }
      
      this.searchResults = []
      
      if (this.searchAllFloors) {
        // 전체 층 검색
        this.floors.forEach(floor => {
          const items = this.floorData[floor.id]?.items || []
          items.forEach(item => {
            if (item.type === 'seat') {
              const nameMatch = (item.name || '').toLowerCase().includes(query)
              const codeMatch = (item.code || '').toLowerCase().includes(query)
              if (nameMatch || codeMatch) {
                this.searchResults.push({ ...item, floor: floor.id })
              }
            }
          })
        })
      } else {
        // 현재 층만 검색
        this.currentFloorItems.forEach(item => {
          if (item.type === 'seat') {
            const nameMatch = (item.name || '').toLowerCase().includes(query)
            const codeMatch = (item.code || '').toLowerCase().includes(query)
            if (nameMatch || codeMatch) {
              this.searchResults.push({ ...item, floor: this.currentFloor })
            }
          }
        })
      }
      
      this.currentSearchIndex = 0
      if (this.searchResults.length > 0) {
        this.scrollToResult()
      } else {
        alert('검색 결과가 없습니다.')
      }
    },
    
    onSearchInput() {
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
      if (!currentItem) return
      
      // 다른 층이면 층 변경
      if (currentItem.floor !== this.currentFloor) {
        this.currentFloor = currentItem.floor
      }
      
      // 스크롤
      this.$nextTick(() => {
        if (this.$refs.canvas) {
          const canvas = this.$refs.canvas
          const scrollLeft = currentItem.x - (canvas.clientWidth / 2) + (currentItem.width / 2)
          const scrollTop = currentItem.y - (canvas.clientHeight / 2) + (currentItem.height / 2)
          
          canvas.scrollTo({
            left: Math.max(0, scrollLeft),
            top: Math.max(0, scrollTop),
            behavior: 'smooth'
          })
        }
      })
    },
    
    isSearchResult(item) {
      return this.searchResults.some(r => r.id === item.id && r.floor === this.currentFloor)
    },
    
    isCurrentSearchResult(item) {
      const current = this.searchResults[this.currentSearchIndex]
      return current && current.id === item.id && current.floor === this.currentFloor
    },
    
    // ===== 아이템 클릭 =====
    onItemClick(e, item) {
      if (this.isDragging) return
      
      if (this.deleteMode) {
        this.deleteItem(item.id)
        return
      }
      
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
        const userRes = await axios.get(`${API_BASE}/users`, {
          params: { search: seat.name }
        })
        
        if (userRes.data && userRes.data.length > 0) {
          const user = userRes.data.find(u => u.name === seat.name) || userRes.data[0]
          this.userInfo = user
          
          // 장비 정보 로드
          const assignRes = await axios.get(`${API_BASE}/users/${user.id}/assignments`)
          this.userAssignments = assignRes.data || []
        }
      } catch (error) {
        console.error('사용자 정보 로드 실패:', error)
      }
      
      this.loadingUserInfo = false
    },
    
    closeUserInfoModal() {
      this.showUserInfoModal = false
      this.selectedSeat = null
      this.userInfo = null
      this.userAssignments = []
    },
    
    goToUserManagement() {
      this.closeUserInfoModal()
      this.$router.push('/users')
    },
    
    // ===== 내보내기/가져오기 =====
    exportData() {
      const dataStr = JSON.stringify(this.floorData, null, 2)
      const blob = new Blob([dataStr], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      
      const a = document.createElement('a')
      a.href = url
      a.download = `floorplan_all_floors_${new Date().toISOString().split('T')[0]}.json`
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
          
          // 새로운 층별 포맷인지 확인
          if (data.floors || (data[14] || data[15] || data[16])) {
            const floors = data.floors || data
            this.floors.forEach(floor => {
              if (floors[floor.id]) {
                this.floorData[floor.id] = floors[floor.id]
              }
            })
          } else if (data.items) {
            // 기존 단일 배치도 포맷
            this.floorData[this.currentFloor] = {
              items: data.items.map(item => ({ ...item, floor: this.currentFloor })),
              itemIdCounter: data.itemIdCounter || 1
            }
          }
          
          this.markUnsaved()
          alert('데이터를 불러왔습니다.')
        } catch (error) {
          alert('파일을 읽는 중 오류가 발생했습니다.')
          console.error(error)
        }
      }
      reader.readAsText(file)
      event.target.value = ''
    },
    
    // ===== 키보드 단축키 =====
    handleKeydown(e) {
      // Ctrl+S: 저장
      if (e.ctrlKey && e.key === 's') {
        e.preventDefault()
        this.saveToServer()
      }
      
      // Ctrl+F: 검색 포커스
      if (e.ctrlKey && e.key === 'f') {
        e.preventDefault()
        document.querySelector('.search-input')?.focus()
      }
      
      // ESC: 모달 닫기
      if (e.key === 'Escape') {
        this.closeSeatModal()
        this.closeFacilityModal()
        this.closeUserInfoModal()
        this.deleteMode = false
      }
    },
    
    handleBeforeUnload(e) {
      if (this.hasUnsavedChanges) {
        e.preventDefault()
        e.returnValue = ''
      }
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
    
    getNetworkClass(networkType) {
      if (!networkType) return ''
      if (networkType.includes('내부') || networkType.includes('업무')) return 'network-internal'
      if (networkType.includes('인터넷') || networkType.includes('외부')) return 'network-external'
      return 'network-default'
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
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}

.toolbar-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.toolbar h2 {
  margin: 0;
  color: #2c3e50;
  white-space: nowrap;
}

/* 층 탭 스타일 */
.floor-tabs {
  display: flex;
  gap: 0.5rem;
  background: #f0f0f0;
  padding: 0.25rem;
  border-radius: 8px;
}

.floor-tab {
  padding: 0.5rem 1.25rem;
  border: none;
  background: transparent;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.95rem;
  font-weight: 500;
  color: #666;
  transition: all 0.2s;
}

.floor-tab:hover {
  background: #e0e0e0;
  color: #333;
}

.floor-tab.active {
  background: #3498db;
  color: white;
  box-shadow: 0 2px 4px rgba(52, 152, 219, 0.3);
}

/* 툴바 버튼 */
.toolbar-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.toolbar-buttons button {
  padding: 0.5rem 0.8rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.2s;
}

.btn-primary {
  background: #3498db;
  color: white;
}

.btn-primary:hover {
  background: #2980b9;
}

.btn-secondary {
  background: #95a5a6;
  color: white;
}

.btn-secondary:hover {
  background: #7f8c8d;
}

.btn-warning {
  background: #f39c12;
  color: white;
}

.btn-warning:hover {
  background: #e67e22;
}

.btn-warning.active {
  background: #e74c3c;
  animation: pulse 1s infinite;
}

.btn-danger {
  background: #e74c3c;
  color: white;
}

.btn-danger:hover {
  background: #c0392b;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
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
}

.search-all-floors {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.85rem;
  color: #666;
  cursor: pointer;
}

.search-all-floors input {
  cursor: pointer;
}

.btn-search {
  padding: 0.5rem 1rem;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 20px;
  cursor: pointer;
}

.btn-search:hover {
  background: #2980b9;
}

.btn-clear {
  padding: 0.35rem 0.7rem;
  background: #e74c3c;
  color: white;
  border: none;
  border-radius: 20px;
  cursor: pointer;
  font-size: 0.8rem;
}

.search-result-count {
  font-size: 0.85rem;
  color: #666;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-nav {
  padding: 0.25rem 0.5rem;
  background: #ecf0f1;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.btn-nav:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 상태 바 */
.status-bar {
  display: flex;
  gap: 1rem;
  padding: 0.5rem 1rem;
  background: #f8f9fa;
  border-radius: 6px;
  font-size: 0.85rem;
  flex-wrap: wrap;
}

.current-floor-indicator {
  color: #2c3e50;
}

.save-status {
  color: #27ae60;
}

.unsaved-status {
  color: #e74c3c;
}

.help-text {
  font-size: 0.8rem;
  color: #7f8c8d;
  margin: 0.5rem 0;
}

/* 캔버스 */
.canvas-container {
  position: relative;
  width: 100%;
  height: 600px;
  background: 
    linear-gradient(#e0e0e0 1px, transparent 1px),
    linear-gradient(90deg, #e0e0e0 1px, transparent 1px);
  background-size: 20px 20px;
  border: 2px solid #bdc3c7;
  border-radius: 8px;
  overflow: auto;
}

/* 아이템 공통 */
.item {
  position: absolute;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  cursor: move;
  user-select: none;
  font-size: 0.75rem;
  text-align: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  transition: box-shadow 0.2s;
}

.item:hover {
  box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}

.item.dragging {
  opacity: 0.8;
  box-shadow: 0 8px 16px rgba(0,0,0,0.3);
  z-index: 1000;
}

.item.delete-mode {
  cursor: pointer;
  animation: shake 0.3s infinite;
}

.item.delete-mode:hover {
  background: #e74c3c !important;
  color: white !important;
}

@keyframes shake {
  0%, 100% { transform: rotate(-1deg); }
  50% { transform: rotate(1deg); }
}

.item.selected {
  outline: 3px solid #3498db;
  outline-offset: 2px;
}

.item.search-highlight {
  outline: 3px solid #f39c12;
  outline-offset: 2px;
}

.item.search-current {
  outline: 4px solid #e74c3c;
  outline-offset: 2px;
  animation: searchPulse 1s infinite;
}

@keyframes searchPulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.02); }
}

/* 좌석 */
.item.seat {
  background: linear-gradient(135deg, #e3f2fd, #bbdefb);
  border: 2px solid #1976d2;
  color: #1565c0;
}

.item.seat .name {
  font-weight: 600;
  font-size: 0.8rem;
}

.item.seat .code {
  font-size: 0.65rem;
  color: #1976d2;
  opacity: 0.8;
}

/* 시설 유형 */
.item.facility {
  background: linear-gradient(135deg, #78909c, #546e7a);
  color: white;
}

.item.facility-room {
  background: linear-gradient(135deg, #ce93d8, #ba68c8);
  color: white;
}

.item.facility-equip {
  background: linear-gradient(135deg, #fff176, #ffd54f);
  color: #5d4037;
}

/* 리사이즈 핸들 */
.resize-handle {
  position: absolute;
  right: 0;
  bottom: 0;
  width: 12px;
  height: 12px;
  background: linear-gradient(135deg, transparent 50%, rgba(0,0,0,0.3) 50%);
  cursor: se-resize;
  border-radius: 0 0 4px 0;
}

/* 범례 */
.legend {
  display: flex;
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
  box-sizing: border-box;
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