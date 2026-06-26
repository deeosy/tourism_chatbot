import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// Vite config for the React frontend.
// Plugins:
//   react    – enables JSX transform and React Fast Refresh
//   tailwindcss – processes Tailwind CSS v4 styles (via @import "tailwindcss")
export default defineConfig({
  plugins: [react(), tailwindcss()],
})
