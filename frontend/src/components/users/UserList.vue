<template>
  <div class="user-management">
    <div class="user-layout">
      <!-- 좌측: 사용자 목록 -->
      <div class="user-list-panel">
        <div class="panel-header">
          <h2>사용자 목록</h2>
          <button @click="openAddModal" class="btn-primary btn-sm">+ 등록</button>
        </div>

        <div class="search-box compact">
          <input v-model="search.name" placeholder="이름" @keyup.enter="searchUsers" />
          <input v-model="search.department" placeholder="부서" @keyup.enter="searchUsers" />
          <button @click="searchUsers" class="btn-search">검색</button>
        </div>

        <div class="user-list">
          <div 
            v-for="user in userList" 
            :key="user.id" 
            :class="['user-card', { selected: selectedUser?.id === user.id }]"
            @click="selectUser(user)"
          >
            <div class="user-info">
              <div class="user-name">{{ user.name }}</div>
              <div class="user-detail">{{ user.department }} · {{ user.location }}</div>
            </div>
            <div class="user-equipment-count">
              <span class="badge">{{ getUserEquipmentCount(user.id) }}</span>
            </div>
          </div>
          <div v-if="userList.length === 0" class="empty-list">
            등록된 사용자가 없습니다.
          </div>
        </div>
      </div>

      <!-- 우측: 선택된 사용자 상세 -->
      <div class="user-detail-panel">
        <div v-if="selectedUser" class="user-detail-content">
          <!-- 사용자 정보 카드 -->
          <div class="info-card">
            <div class="info-card-header">
              <h3>{{ selectedUser.name }}</h3>
              <div class="info-card-actions">
                <button @click="openEditModal(selectedUser)" class="btn-small">수정</button>
                <button @click="deleteUser(selectedUser.id)" class="btn-small btn-danger">삭제</button>
              </div>
            </div>
            <div class="info-card-body">
              <div class="info-row">
                <span class="info-label">부서</span>
                <span class="info-value">{{ selectedUser.department }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">위치</span>
                <span class="info-value">{{ selectedUser.location }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">전화번호</span>
                <span class="info-value">{{ selectedUser.phone || '-' }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">이메일</span>
                <span class="info-value">{{ selectedUser.email || '-' }}</span>
              </div>
            </div>
          </div>

          <!-- 사용중인 장비 섹션 -->
          <div class="equipment-section">
            <div class="section-header">
              <h4>사용중인 장비 ({{ userAssignments.length }}개)</h4>
              <button @click="openAssignModal" class="btn-primary btn-sm">+ 장비 할당</button>
            </div>

            <div v-if="userAssignments.length > 0" class="assigned-equipment-list">
              <div v-for="assignment in userAssignments" :key="assignment.id" class="equipment-card">
                <div class="equipment-card-main clickable" @click="openEquipmentDetail(assignment.equipment)">
                  <div class="equipment-icon">
                    <span v-if="assignment.equipment.category === '데스크탑'">🖥️</span>
                    <span v-else-if="assignment.equipment.category === '노트북'">💻</span>
                    <span v-else-if="assignment.equipment.category === '모니터'">🖥️</span>
                    <span v-else-if="assignment.equipment.category === '미니PC'">📲</span>
                    <span v-else>📦</span>
                  </div>
                  <div class="equipment-details">
                    <div class="equipment-name">
                      {{ assignment.equipment.model_name }}
                      <span class="click-hint">클릭하여 상세보기</span>
                    </div>
                    <div class="equipment-meta">
                      <span class="asset-number">{{ assignment.equipment.asset_number }}</span>
                      <span class="category-tag">{{ assignment.equipment.category }}</span>
                      <!-- 데스크탑/미니PC인 경우 망분리 정보 표시 -->
                      <span 
                        v-if="showNetworkType(assignment.equipment)" 
                        :class="['network-tag', 'network-' + getNetworkClass(assignment.equipment.network_type)]"
                      >
                        {{ assignment.equipment.network_type }}
                      </span>
                    </div>
                    <div class="assignment-date">할당일: {{ formatDate(assignment.assignment_date) }}</div>
                  </div>
                </div>
                <div class="equipment-card-actions">
                  <button @click.stop="openReplaceModal(assignment)" class="btn-small btn-replace">교체</button>
                  <button @click.stop="openReturnModal(assignment)" class="btn-small btn-danger">반납</button>
                </div>
              </div>
            </div>
            
            <div v-else class="empty-equipment">
              <div class="empty-icon">🔭</div>
              <p>사용중인 장비가 없습니다.</p>
              <button @click="openAssignModal" class="btn-primary">장비 할당하기</button>
            </div>
          </div>

          <!-- 할당 이력 섹션 -->
          <div class="history-section">
            <h4>할당 이력</h4>
            <div v-if="userAllAssignments.length > 0" class="history-list">
              <div v-for="assignment in userAllAssignments" :key="assignment.id" class="history-item">
                <div class="history-info">
                  <span class="history-equipment">{{ assignment.equipment.asset_number }}</span>
                  <span class="history-model">{{ assignment.equipment.model_name }}</span>
                </div>
                <div class="history-dates">
                  <span>{{ formatDate(assignment.assignment_date) }}</span>
                  <span v-if="assignment.return_date"> ~ {{ formatDate(assignment.return_date) }}</span>
                </div>
                <span :class="'status-badge status-' + assignment.status">{{ assignment.status }}</span>
              </div>
            </div>
            <div v-else class="empty-history">할당 이력이 없습니다.</div>
          </div>
        </div>

        <!-- 사용자 미선택 상태 -->
        <div v-else class="no-selection">
          <div class="no-selection-icon">👈</div>
          <p>좌측 목록에서 사용자를 선택하세요</p>
          <p class="hint">사용자를 선택하면 상세 정보와 장비 할당 현황을 확인할 수 있습니다.</p>
        </div>
      </div>
    </div>

    <!-- 사용자 등록/수정 모달 -->
    <UserForm
      v-if="showUserModal"
      :user="editingUser"
      :is-edit="isEdit"
      @close="closeUserModal"
      @saved="onUserSaved"
    />

    <!-- 장비 할당 모달 -->
    <AssignmentModal
      v-if="showAssignModal"
      :user="selectedUser"
      @close="showAssignModal = false"
      @assigned="onAssigned"
    />

    <!-- 반납 모달 -->
    <ReturnModal
      v-if="showReturnModal"
      :assignment="returningAssignment"
      @close="showReturnModal = false"
      @returned="onReturned"
    />

    <!-- 교체 모달 -->
    <ReplaceModal
      v-if="showReplaceModal"
      :user="selectedUser"
      :current-assignment="replacingAssignment"
      @close="showReplaceModal = false"
      @replaced="onReplaced"
    />

    <!-- 장비 상세/수정 모달 -->
    <EquipmentDetailModal
      v-if="showEquipmentDetailModal"
      :equipment="selectedEquipment"
      @close="showEquipmentDetailModal = false"
      @updated="onEquipmentUpdated"
    />
  </div>
</template>

<script>
import { userApi, assignmentApi } from '../../api'
import UserForm from './UserForm.vue'
import AssignmentModal from './AssignmentModal.vue'
import ReturnModal from './ReturnModal.vue'
import ReplaceModal from './ReplaceModal.vue'
import EquipmentDetailModal from './EquipmentDetailModal.vue'

export default {
  name: 'UserList',
  components: {
    UserForm,
    AssignmentModal,
    ReturnModal,
    ReplaceModal,
    EquipmentDetailModal
  },
  props: {
    // Vue Router에서 전달받는 userId (route params)
    userId: {
      type: [String, Number],
      default: null
    }
  },
  data() {
    return {
      userList: [],
      activeAssignments: [],
      selectedUser: null,
      userAssignments: [],
      userAllAssignments: [],
      search: {
        name: '',
        department: ''
      },
      showUserModal: false,
      showAssignModal: false,
      showReturnModal: false,
      showReplaceModal: false,
      showEquipmentDetailModal: false,
      isEdit: false,
      editingUser: null,
      returningAssignment: null,
      replacingAssignment: null,
      selectedEquipment: null
    }
  },
  watch: {
    // route params 변경 감지
    '$route.params.userId': {
      immediate: true,
      handler(newUserId) {
        if (newUserId) {
          this.selectUserById(newUserId)
        }
      }
    }
  },
  async mounted() {
    await this.loadUsers()
    await this.loadActiveAssignments()
    
    // 초기 userId가 있으면 해당 사용자 선택
    const routeUserId = this.$route?.params?.userId || this.userId
    if (routeUserId) {
      this.selectUserById(routeUserId)
    }
  },
  methods: {
    async loadUsers() {
      try {
        const response = await userApi.getAll()
        this.userList = response.data
      } catch (error) {
        console.error('사용자 목록 로드 실패:', error)
      }
    },
    
    async searchUsers() {
      try {
        const response = await userApi.search(this.search)
        this.userList = response.data
      } catch (error) {
        alert('검색에 실패했습니다.')
      }
    },
    
    async loadActiveAssignments() {
      try {
        const response = await assignmentApi.getActive()
        this.activeAssignments = response.data
      } catch (error) {
        console.error('할당 목록 로드 실패:', error)
      }
    },
    
    async selectUser(user) {
      this.selectedUser = user
      await this.loadUserAssignments(user.id)
      
      // URL 업데이트 (히스토리에 추가하지 않고 replace)
      if (this.$router && this.$route.params.userId !== String(user.id)) {
        this.$router.replace({ name: 'user-detail', params: { userId: user.id } })
      }
    },
    
    // ID로 사용자 선택 (외부에서 호출 가능)
    async selectUserById(userId) {
      // 사용자 목록이 로드될 때까지 대기
      if (this.userList.length === 0) {
        await this.loadUsers()
      }
      
      const user = this.userList.find(u => u.id === Number(userId))
      if (user) {
        this.selectedUser = user
        await this.loadUserAssignments(user.id)
      }
    },
    
    async loadUserAssignments(userId) {
      try {
        const response = await assignmentApi.getByUser(userId)
        this.userAllAssignments = response.data
        this.userAssignments = response.data.filter(a => a.status === '사용중')
      } catch (error) {
        console.error('사용자 할당 정보 로드 실패:', error)
      }
    },
    
    getUserEquipmentCount(userId) {
      return this.activeAssignments.filter(a => a.user_id === userId).length
    },
    
    // 데스크탑/미니PC인 경우 망분리 정보 표시 여부
    showNetworkType(equipment) {
      return (equipment.category === '데스크탑' || equipment.category === '미니PC') && equipment.network_type
    },
    
    // 망분리 타입에 따른 CSS 클래스
    getNetworkClass(networkType) {
      if (!networkType) return ''
      if (networkType.includes('내부') || networkType.includes('업무')) return 'internal'
      if (networkType.includes('인터넷') || networkType.includes('외부')) return 'external'
      return 'default'
    },
    
    openAddModal() {
      this.editingUser = null
      this.isEdit = false
      this.showUserModal = true
    },
    
    openEditModal(user) {
      this.editingUser = { ...user }
      this.isEdit = true
      this.showUserModal = true
    },
    
    closeUserModal() {
      this.showUserModal = false
      this.editingUser = null
    },
    
    async onUserSaved(user) {
      this.closeUserModal()
      await this.loadUsers()
      
      if (user && !this.isEdit) {
        this.selectedUser = user
        this.userAssignments = []
        this.userAllAssignments = []
      } else if (this.selectedUser?.id === user?.id) {
        this.selectedUser = { ...this.selectedUser, ...user }
      }
    },
    
    async deleteUser(id) {
      if (!confirm('이 사용자를 삭제하시겠습니까?')) return
      
      try {
        await userApi.delete(id)
        alert('삭제되었습니다.')
        
        if (this.selectedUser?.id === id) {
          this.selectedUser = null
          this.userAssignments = []
          this.userAllAssignments = []
          
          // URL도 초기화
          if (this.$router) {
            this.$router.replace({ name: 'users' })
          }
        }
        
        await this.loadUsers()
      } catch (error) {
        alert('삭제에 실패했습니다: ' + (error.response?.data?.error || error.message))
      }
    },
    
    openAssignModal() {
      if (!this.selectedUser) {
        alert('사용자를 먼저 선택해주세요.')
        return
      }
      this.showAssignModal = true
    },
    
    async onAssigned() {
      this.showAssignModal = false
      await this.loadUserAssignments(this.selectedUser.id)
      await this.loadActiveAssignments()
    },
    
    openReturnModal(assignment) {
      this.returningAssignment = assignment
      this.showReturnModal = true
    },
    
    async onReturned() {
      this.showReturnModal = false
      this.returningAssignment = null
      await this.loadUserAssignments(this.selectedUser.id)
      await this.loadActiveAssignments()
    },
    
    // 교체 모달 열기
    openReplaceModal(assignment) {
      this.replacingAssignment = assignment
      this.showReplaceModal = true
    },
    
    // 교체 완료 후 처리
    async onReplaced() {
      this.showReplaceModal = false
      this.replacingAssignment = null
      await this.loadUserAssignments(this.selectedUser.id)
      await this.loadActiveAssignments()
    },
    
    // 장비 상세 모달 열기
    openEquipmentDetail(equipment) {
      this.selectedEquipment = equipment
      this.showEquipmentDetailModal = true
    },
    
    // 장비 수정 완료 후 처리
    async onEquipmentUpdated() {
      this.showEquipmentDetailModal = false
      this.selectedEquipment = null
      // 장비 정보가 변경되었으므로 할당 목록 새로고침
      await this.loadUserAssignments(this.selectedUser.id)
      await this.loadActiveAssignments()
    },
    
    formatDate(dateString) {
      if (!dateString) return '-'
      return dateString.split('T')[0]
    }
  }
}
</script>

<style scoped>
/* 교체 버튼 스타일 */
.btn-replace {
  background: #f39c12 !important;
  color: white !important;
}

.btn-replace:hover {
  background: #e67e22 !important;
}

/* 망분리 태그 스타일 */
.network-tag {
  font-size: 0.7rem;
  padding: 0.15rem 0.4rem;
  border-radius: 3px;
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

/* 장비 카드 액션 버튼 간격 */
.equipment-card-actions {
  display: flex;
  gap: 0.5rem;
}

/* 클릭 가능한 장비 카드 영역 */
.equipment-card-main.clickable {
  cursor: pointer;
  transition: background 0.2s;
  border-radius: 6px;
  padding: 0.5rem;
  margin: -0.5rem;
  margin-right: 0;
}

.equipment-card-main.clickable:hover {
  background: rgba(52, 152, 219, 0.1);
}

/* 클릭 힌트 */
.click-hint {
  font-size: 0.7rem;
  color: #95a5a6;
  margin-left: 0.5rem;
  opacity: 0;
  transition: opacity 0.2s;
}

.equipment-card-main.clickable:hover .click-hint {
  opacity: 1;
}
</style>