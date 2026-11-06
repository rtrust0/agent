import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import pinia from './store'
import { vPermission } from './directives/v-permission'
import './assets/main.css'

const app = createApp(App)

app.use(pinia)
app.use(router)
app.directive('permission', vPermission)

app.mount('#app')
