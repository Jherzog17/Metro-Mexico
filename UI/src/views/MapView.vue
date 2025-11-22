<script setup>
import { ref, onMounted, computed } from 'vue'
import { LMap, LTileLayer, LMarker, LPopup, LPolyline } from '@vue-leaflet/vue-leaflet'
import L from 'leaflet'
import axios from 'axios'

// Fix iconos Leaflet
import iconUrl from 'leaflet/dist/images/marker-icon.png'
import shadowUrl from 'leaflet/dist/images/marker-shadow.png'

const zoom = ref(12)
const center = ref([19.4326, -99.1332])
const locations = ref({})
const selectedStation = ref(null)
const stationInfo = ref(null)
const loadingInfo = ref(false)

// Icono personalizado "bonito"
const customIcon = L.icon({
  iconUrl: 'https://cdn-icons-png.flaticon.com/512/684/684908.png', // Icono de ubicación más estético
  iconSize: [32, 32],
  iconAnchor: [16, 32],
  popupAnchor: [0, -32],
  shadowUrl: null
})

onMounted(async () => {
  try {
    const response = await axios.get('http://localhost:5000/api/locations')
    locations.value = response.data
  } catch (e) {
    console.error("Error cargando ubicaciones:", e)
  }
})

const handleMarkerClick = async (name) => {
  selectedStation.value = name
  stationInfo.value = null
  loadingInfo.value = true
  
  try {
    const response = await axios.get(`http://localhost:5000/api/station/${name}`)
    stationInfo.value = response.data
  } catch (e) {
    console.error("Error cargando info estación:", e)
  } finally {
    loadingInfo.value = false
  }
}

const closeMenu = () => {
  selectedStation.value = null
  stationInfo.value = null
}
</script>

<template>
  <div class="relative h-[calc(100vh-100px)] rounded-lg overflow-hidden shadow-lg border border-gray-200">
    <l-map ref="map" v-model:zoom="zoom" v-model:center="center" :use-global-leaflet="false">
      <l-tile-layer
        url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
        layer-type="base"
        name="CartoDB Voyager"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
      ></l-tile-layer>

      <l-marker 
        v-for="(loc, name) in locations" 
        :key="name" 
        :lat-lng="[loc.lat, loc.lon]"
        :icon="customIcon"
        @click="handleMarkerClick(name)"
      >
      </l-marker>
    </l-map>

    <!-- Menú Lateral de Estación -->
    <div v-if="selectedStation" class="absolute top-0 right-0 h-full w-80 bg-white shadow-2xl z-[1000] transform transition-transform duration-300 overflow-y-auto">
      <div class="p-4 bg-indigo-600 text-white flex justify-between items-center sticky top-0">
        <h2 class="font-bold text-lg truncate pr-2">{{ selectedStation }}</h2>
        <button @click="closeMenu" class="text-white hover:bg-indigo-700 rounded-full p-1">✕</button>
      </div>
      
      <div class="p-4">
        <div v-if="loadingInfo" class="flex justify-center py-8">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
        </div>
        
        <div v-else-if="stationInfo">
            <div class="mb-6">
                <span class="text-xs font-bold text-gray-500 uppercase tracking-wider">Línea</span>
                <div class="mt-1 inline-block px-3 py-1 rounded-full bg-orange-100 text-orange-800 font-bold border border-orange-200">
                    Línea {{ stationInfo.line }}
                </div>
            </div>

            <div class="mb-6">
                <h3 class="font-bold text-gray-800 mb-3 flex items-center gap-2">
                    <span>🕒</span> Próximos Trenes
                </h3>
                <div v-if="stationInfo.next_trains.length === 0" class="text-gray-500 text-sm italic">
                    No hay trenes programados pronto.
                </div>
                <div v-else class="space-y-3">
                    <div v-for="(train, idx) in stationInfo.next_trains" :key="idx" class="bg-gray-50 p-3 rounded border border-gray-100 hover:border-indigo-200 transition">
                        <div class="flex justify-between text-sm mb-1">
                            <span class="font-medium text-gray-700">Destino: {{ train.direccion }}</span>
                        </div>
                        <div class="flex justify-between items-end">
                            <span class="text-xs text-gray-500">Llegada: {{ train.proxima_llegada }}</span>
                            <span class="text-green-600 font-bold text-sm">{{ train.tiempo_espera }}</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="mt-8 pt-4 border-t text-center">
                <button class="text-indigo-600 text-sm font-medium hover:underline">Ver detalles de la línea →</button>
            </div>
        </div>
      </div>
    </div>
  </div>
</template>
