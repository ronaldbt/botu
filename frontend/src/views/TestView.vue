<template>
  <div class="min-h-screen bg-slate-50">
    <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="space-y-8">
        
        <!-- DEBUG: Caja roja de prueba -->
        <div class="bg-red-500 text-white p-4 mb-4">
          DEBUG: Esta es una vista de prueba - debería aparecer siempre
        </div>
        
        <!-- Test Component -->
        <div class="bg-blue-500 text-white p-4 mb-4">
          <h2>Test Component</h2>
          <p>Si ves esto, el template funciona correctamente</p>
        </div>
        
      </div>
    </div>
  </div>
</template>

<script setup>
console.log('[TestView] Vista de prueba montada correctamente')
</script>
