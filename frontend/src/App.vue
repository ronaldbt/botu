<template>
  <div class="flex min-h-screen">
    <Sidebar v-if="authStore.isAuthenticated" />

    <div class="flex-1 ml-64 relative z-10">
      <router-view />
    </div>
  </div>
</template>

<script setup>
import Sidebar from './components/Sidebar.vue';
import { useAuthStore } from './stores/authStore';

const authStore = useAuthStore();
</script>
