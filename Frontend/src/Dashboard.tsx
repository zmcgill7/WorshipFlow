import React from 'react'
import { useNavigate } from 'react-router-dom'
import App from './App'

function Dashboard() {
  const navigate = useNavigate()

  const handleLogout = () => {
    localStorage.removeItem('isAuthenticated')
    navigate('/')
  }

  return (
    <div>
      <div className="logout-bar">
        <button onClick={handleLogout} className="btn-logout">
          Sign Out
        </button>
      </div>
      <App />
    </div>
  )
}

export default Dashboard
