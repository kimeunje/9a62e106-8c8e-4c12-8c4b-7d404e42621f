<template>
  <div id="app">
    <header class="header">
      <h1>전산장비 관리 시스템</h1>
      <nav>
        <router-link 
          v-for="menu in menus" 
          :key="menu.path"
          :to="menu.path"
          custom
          v-slot="{ isActive, navigate }"
        >
          <button 
            @click="navigate" 
            :class="{ active: isActive || isActiveRoute(menu.path) }"
          >
            {{ menu.label }}
          </button>
        </router-link>
      </nav>
    </header>

    <main class="main-content">
      <router-view v-slot="{ Component }">
        <component :is="Component" @navigate="handleNavigate" />
      </router-view>
    </main>
  </div>
</template>

<script>
export default {
  name: 'App',
  data() {
    return {
      menus: [
        { path: '/', label: '대시보드' },
        { path: '/equipment', label: '장비 관리' },
        { path: '/users', label: '사용자 관리' },
        { path: '/seals', label: '보안씰 관리' },
        { path: '/history', label: '이력 관리' },
        { path: '/floorplan', label: '배치도' }
      ]
    }
  },
  methods: {
    isActiveRoute(path) {
      // /users/:userId 같은 하위 경로도 users 메뉴가 활성화되도록
      if (path === '/') {
        return this.$route.path === '/'
      }
      return this.$route.path.startsWith(path)
    },
    handleNavigate(view, params) {
      // FloorPlan에서 사용자 관리 페이지로 이동 시
      if (view === 'users' && params?.userId) {
        this.$router.push({ name: 'user-detail', params: { userId: params.userId } })
      } else {
        this.$router.push(`/${view === 'dashboard' ? '' : view}`)
      }
    }
  }
}
</script>

<style>
@import './assets/styles.css';
</style>