import { createRouter, createWebHistory } from 'vue-router'
import RoutesView from '../views/RoutesView.vue'
import MapView from '../views/MapView.vue'
import InfoView from '../views/InfoView.vue'

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/',
            name: 'routes',
            component: RoutesView
        },
        {
            path: '/map',
            name: 'map',
            component: MapView
        },
        {
            path: '/info',
            name: 'info',
            component: InfoView
        }
    ]
})

export default router
