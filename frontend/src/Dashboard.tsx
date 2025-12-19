import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { signOut } from 'firebase/auth'
import { auth } from './firebase'
import App from './App'

function Dashboard() {
  const navigate = useNavigate()
  const [userName, setUserName] = useState<string | null>(null)

  useEffect(() => {
    const unsubscribe = auth.onAuthStateChanged((user) => {
      if (user) {
        setUserName(user.displayName || user.email || null)
      } else {
        setUserName(null)
      }
    })

    return () => unsubscribe()
  }, [])

  const handleLogout = async () => {
    try {
      await signOut(auth)
      navigate('/')
    } catch (err) {
      console.error('Logout error:', err)
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
