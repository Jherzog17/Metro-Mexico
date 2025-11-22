<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const stations = ref([])
const origin = ref('')
const destination = ref('')
const time = ref('')
const routeData = ref(null)
const loading = ref(false)
const error = ref(null)

onMounted(async () => {
  try {
    const response = await axios.get('http://localhost:5000/api/stations')
    stations.value = response.data
    if (stations.value.length > 0) {
      origin.value = stations.value[0]
      destination.value = stations.value[1] || stations.value[0]
    }
    const now = new Date()
    time.value = now.toTimeString().split(' ')[0]
  } catch (e) {
    console.error("Error cargando estaciones:", e)
  }
})

const searchRoute = async () => {
  loading.value = true
  error.value = null
  routeData.value = null
  try {
    const response = await axios.post('http://localhost:5000/api/route', {
      origin: origin.value,
      destination: destination.value,
      time: time.value
    })
    routeData.value = response.data
  } catch (e) {
    error.value = "Error al calcular la ruta. Inténtalo de nuevo."
    console.error(e)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="max-w-4xl mx-auto">
    <h1 class="text-3xl font-bold mb-6 text-center text-indigo-700">Planificador de Rutas</h1>
    
    <div class="bg-white p-6 rounded-lg shadow-md mb-8">
      <form @submit.prevent="searchRoute" class="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Origen</label>
          <select v-model="origin" class="w-full p-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500">
            <option v-for="st in stations" :key="st" :value="st">{{ st }}</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Destino</label>
          <select v-model="destination" class="w-full p-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500">
            <option v-for="st in stations" :key="st" :value="st">{{ st }}</option>
          </select>
        </div>
        <div class="flex gap-2">
            <div class="flex-grow">
                <label class="block text-sm font-medium text-gray-700 mb-1">Hora</label>
                <input type="time" step="1" v-model="time" class="w-full p-2 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500">
            </div>
            <button type="submit" :disabled="loading" class="bg-indigo-600 text-white px-6 py-2 rounded-md hover:bg-indigo-700 transition-colors disabled:opacity-50 h-[42px] self-end">
                {{ loading ? '...' : 'Buscar' }}
            </button>
        </div>
      </form>
    </div>

    <div v-if="error" class="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-6" role="alert">
      <p>{{ error }}</p>
    </div>

    <div v-if="routeData" class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- Ruta -->
      <div class="bg-white p-6 rounded-lg shadow-md">
        <h2 class="text-xl font-semibold mb-4 text-gray-800 border-b pb-2">Itinerario</h2>
        <div class="flex justify-between mb-4 text-sm text-gray-600">
            <span>Distancia: <strong>{{ routeData.distance.toFixed(2) }}</strong></span>
            <span>Estaciones: <strong>{{ routeData.path.length }}</strong></span>
        </div>
        <div class="relative pl-4 border-l-2 border-indigo-200 space-y-4 max-h-[400px] overflow-y-auto pr-2 custom-scrollbar">
          <div v-for="(station, index) in routeData.path" :key="station" class="relative">
            <div class="absolute -left-[21px] bg-white border-2 border-indigo-500 rounded-full w-3 h-3 mt-1.5"></div>
            <p class="text-gray-800 font-medium">{{ station }}</p>
            <p v-if="index < routeData.path.length - 1" class="text-xs text-gray-400 mt-1">↓</p>
          </div>
        </div>
      </div>

      <!-- Próximo Tren -->
      <div class="bg-white p-6 rounded-lg shadow-md h-fit">
        <h2 class="text-xl font-semibold mb-4 text-gray-800 border-b pb-2">Próximo Tren en Origen</h2>
        <div v-if="routeData.next_train.error" class="text-red-500">
            {{ routeData.next_train.error }}
        </div>
        <div v-else class="space-y-3">
            <div class="flex justify-between items-center">
                <span class="text-gray-600">Estación:</span>
                <span class="font-bold text-lg">{{ routeData.next_train.estacion_origen }}</span>
            </div>
            <div class="flex justify-between items-center">
                <span class="text-gray-600">Dirección:</span>
                <span class="bg-indigo-100 text-indigo-800 px-2 py-1 rounded text-sm font-semibold">{{ routeData.next_train.direccion }}</span>
            </div>
            <div class="flex justify-between items-center">
                <span class="text-gray-600">Llegada:</span>
                <span class="text-xl font-mono text-gray-900">{{ routeData.next_train.proxima_llegada }}</span>
            </div>
             <div class="flex justify-between items-center">
                <span class="text-gray-600">Espera:</span>
                <span class="text-green-600 font-bold">{{ routeData.next_train.tiempo_espera }}</span>
            </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: #f1f1f1;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #c7c7c7;
  border-radius: 3px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}
</style>
