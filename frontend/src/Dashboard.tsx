import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import App from './App'

function Dashboard() {
  const navigate = useNavigate()
  const [userName, setUserName] = useState<string | null>(null)

  useEffect(() => {
    try {
      const stored = localStorage.getItem('worshipUser')
      if (stored) {
        const parsed = JSON.parse(stored)
        const nameFromStorage = parsed.name || parsed.email || null
        setUserName(nameFromStorage)
      }
    } catch {
      setUserName(null)
    }
  }, [])

  const handleLogout = async () => {
    try {
      await fetch('/api/logout/', {
        method: 'POST',
        credentials: 'include',
      })
    } catch (err) {
      // Ignore network errors on logout; still clear local state
    } finally {
      localStorage.removeItem('isAuthenticated')
      localStorage.removeItem('worshipUser')
      navigate('/')
    }
  }

  return (
    <div>
      <div className="logout-bar">
        <button onClick={() => navigate('/history')} className="btn-history">
          History
        </button>
        <div className="logout-bar-right">
          {userName && <span className="welcome-text">Welcome {userName}</span>}
          <button onClick={handleLogout} className="btn-logout">
            Sign Out
          </button>
        </div>
      </div>
      <App />
    </div>
  )
}

export default Dashboard
