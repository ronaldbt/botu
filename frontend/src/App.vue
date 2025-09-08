<template>
  <div class="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
    <Sidebar v-if="authStore.isAuthenticated" />

    <div :class="authStore.isAuthenticated ? 'md:ml-64 pb-16 md:pb-0' : ''" class="relative z-10">
      <router-view />
    </div>
  </div>
</template>

<script setup>
import Sidebar from './components/Sidebar.vue';
import { useAuthStore } from './stores/authStore';

const authStore = useAuthStore();
</script>
