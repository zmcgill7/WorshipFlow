import { useNavigate } from 'react-router-dom'
import App from './App'

function Dashboard() {
  const navigate = useNavigate()

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
        <button onClick={handleLogout} className="btn-logout">
          Sign Out
        </button>
      </div>
      <App />
    </div>
  )
}

export default Dashboard
