import { Routes, Route } from 'react-router-dom'

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Routes>
        <Route path="/" element={<div className="p-8"><h1 className="text-2xl font-bold">AI Voice Agent</h1><p className="text-gray-600 mt-2">Dashboard coming soon...</p></div>} />
      </Routes>
    </div>
  )
}

export default App

