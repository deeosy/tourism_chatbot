import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
// Import Tailwind CSS (processed by @tailwindcss/vite plugin)
import './index.css'
import App from './App.jsx'

// Mount the React app into the <div id="root"> in index.html
createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
