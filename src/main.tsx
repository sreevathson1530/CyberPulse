import '@fontsource-variable/instrument-sans'
import '@fontsource-variable/newsreader'
import '@fontsource-variable/newsreader/wght-italic.css'
import '@fontsource-variable/jetbrains-mono'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
