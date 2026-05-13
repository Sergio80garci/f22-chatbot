import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Footer from './components/Footer'
import Home from './pages/Home'
import Chat from './pages/Chat'
import Documentos from './pages/Documentos'

// Vite expone import.meta.env.BASE_URL = base de vite.config.js
// React Router lo necesita para que /chat funcione bajo /f22-chatbot/chat.
const BASENAME = import.meta.env.BASE_URL.replace(/\/$/, '') || '/'

export default function App() {
  return (
    <BrowserRouter basename={BASENAME}>
      <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
        <Navbar />
        <div style={{ flex: 1 }}>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/chat" element={<Chat />} />
            <Route path="/documentos" element={<Documentos />} />
          </Routes>
        </div>
        <Footer />
      </div>
    </BrowserRouter>
  )
}
