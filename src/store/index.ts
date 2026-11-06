import { createPinia } from 'pinia'

const pinia = createPinia()

export default pinia

export { useAuthStore } from './auth'
export { usePermissionStore } from './permission'
export { useUserStore } from './user'
export { useRoleStore } from './role'
export type { LoginCredentials } from './auth'
