import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Home from './pages/Home'
import Chat from './pages/Chat'
import Documentos from './pages/Documentos'
import Todio from './pages/Todio'
import TodioDetalle from './pages/TodioDetalle'

export default function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/documentos" element={<Documentos />} />
        <Route path="/todio" element={<Todio />} />
        <Route path="/todio/:id" element={<TodioDetalle />} />
      </Routes>
    </BrowserRouter>
  )
}
