import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
    plugins: [react()],
    server: {
        port: 5173,
        host: true,
    },
    // When serving the built frontend from the API under /dashboard, set base accordingly
    base: '/dashboard/',
})
