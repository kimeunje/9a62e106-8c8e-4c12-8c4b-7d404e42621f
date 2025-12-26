<template>
  <div class="pagination">
    <button @click="$emit('page-change', 1)" :disabled="currentPage === 1" class="page-btn">«</button>
    <button @click="$emit('page-change', currentPage - 1)" :disabled="currentPage === 1" class="page-btn">‹</button>
    
    <template v-for="p in visiblePages" :key="p">
      <span v-if="p === '...'" class="page-ellipsis">...</span>
      <button 
        v-else 
        @click="$emit('page-change', p)" 
        :class="['page-btn', { active: p === currentPage }]"
      >
        {{ p }}
      </button>
    </template>
    
    <button @click="$emit('page-change', currentPage + 1)" :disabled="currentPage === totalPages" class="page-btn">›</button>
    <button @click="$emit('page-change', totalPages)" :disabled="currentPage === totalPages" class="page-btn">»</button>
    
    <span class="page-info">{{ currentPage }} / {{ totalPages }} 페이지</span>
  </div>
</template>

<script>
export default {
  name: 'Pagination',
  props: {
    currentPage: {
      type: Number,
      required: true
    },
    totalPages: {
      type: Number,
      required: true
    }
  },
  emits: ['page-change'],
  computed: {
    visiblePages() {
      const current = this.currentPage
      const total = this.totalPages
      const pages = []
      
      if (total <= 7) {
        for (let i = 1; i <= total; i++) pages.push(i)
      } else {
        pages.push(1)
        if (current > 3) pages.push('...')
        
        let start = Math.max(2, current - 1)
        let end = Math.min(total - 1, current + 1)
        
        if (current <= 3) end = 4
        if (current >= total - 2) start = total - 3
        
        for (let i = start; i <= end; i++) pages.push(i)
        
        if (current < total - 2) pages.push('...')
        pages.push(total)
      }
      return pages
    }
  }
}
</script>