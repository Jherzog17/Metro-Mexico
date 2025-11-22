<script setup>
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <div class="min-h-screen flex flex-col font-sans text-gray-800">
    <header class="bg-white shadow-md">
      <nav class="container mx-auto px-4 py-4 flex justify-between items-center">
        <div class="text-xl font-bold text-indigo-600 flex items-center gap-2">
          <span>🚇</span> Metro CDMX
        </div>
        <div class="flex gap-6">
          <RouterLink to="/" class="nav-link" active-class="active">Rutas</RouterLink>
          <RouterLink to="/map" class="nav-link" active-class="active">Mapa</RouterLink>
          <RouterLink to="/info" class="nav-link" active-class="active">Información</RouterLink>
        </div>
      </nav>
    </header>

    <main class="flex-grow container mx-auto px-4 py-6">
      <RouterView />
    </main>

    <footer class="bg-gray-800 text-white py-4 text-center text-sm">
      <p>&copy; 2025 Metro CDMX Planner</p>
    </footer>
  </div>
</template>

<style scoped>
.nav-link {
  @apply text-gray-600 hover:text-indigo-600 font-medium transition-colors duration-200;
}
.nav-link.active {
  @apply text-indigo-600 border-b-2 border-indigo-600;
}
</style>
