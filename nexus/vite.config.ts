import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  define: {
    __GOOGLE_CLIENT_ID__: JSON.stringify(
      process.env.VITE_GOOGLE_CLIENT_ID
    ),
  },
});