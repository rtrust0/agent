import { createPinia } from 'pinia'

const pinia = createPinia()

export default pinia

export { useAuthStore } from './auth'
export { usePermissionStore } from './permission'
export type { LoginCredentials } from './auth'
