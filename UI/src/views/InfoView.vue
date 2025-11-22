<template>
  <div class="max-w-4xl mx-auto text-center py-12">
    <div class="bg-white p-8 rounded-lg shadow-md">
      <div class="text-6xl mb-4">ℹ️</div>
      <h1 class="text-3xl font-bold text-gray-800 mb-4">Información del Metro</h1>
      <p class="text-gray-600 text-lg mb-8">
        Aquí encontrarás noticias, mapas estáticos, tarifas y reglamentos del Sistema de Transporte Colectivo Metro.
      </p>
      
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6 text-left">
        <div class="border p-4 rounded hover:shadow-lg transition cursor-pointer">
            <h3 class="font-bold text-indigo-600 mb-2">Tarifas</h3>
            <p class="text-sm text-gray-500">Consulta el costo del boleto y tarjetas recargables.</p>
        </div>
        <div class="border p-4 rounded hover:shadow-lg transition cursor-pointer">
            <h3 class="font-bold text-indigo-600 mb-2">Horarios</h3>
            <p class="text-sm text-gray-500">Lunes a Viernes: 5:00 - 00:00<br>Sábados: 6:00 - 00:00<br>Domingos: 7:00 - 00:00</p>
        </div>
        <div class="border p-4 rounded hover:shadow-lg transition cursor-pointer">
            <h3 class="font-bold text-indigo-600 mb-2">Contacto</h3>
            <p class="text-sm text-gray-500">Atención al usuario y objetos perdidos.</p>
        </div>
      </div>
    </div>
  </div>
</template>
