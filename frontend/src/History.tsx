import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { signOut } from 'firebase/auth'
import { auth } from './firebase'
// --- NEW ICON IMPORTS ---
import { FaGuitar, FaDrum, FaMicrophone, FaKeyboard } from 'react-icons/fa';
import { GiViolin, GiTrumpet, GiGuitarBassHead } from 'react-icons/gi'; 


// --- NEW ICON MAPPING ---
// A dictionary to map instrument strings to their icon components
const instrumentIconMap: { [key: string]: React.ElementType } = {
  'guitar': FaGuitar,
  'bass': GiGuitarBassHead,
  'keyboard': FaKeyboard,
  'drums': FaDrum,
  'strings': GiViolin,
  'brass': GiTrumpet,
  'vocals': FaMicrophone,
};

// --- NEW HELPER COMPONENT ---
// Component to render the correct icon based on the instrument name
const InstrumentIcon = ({ name }: { name: string }) => {
  const IconComponent = instrumentIconMap[name.toLowerCase()];
  
  if (!IconComponent) {
    return null; // Return nothing if the instrument name isn't mapped
  }

  // Render the component with desired size and spacing
  return <IconComponent size={16} style={{ marginRight: '5px' }} />;
};


// --- EXISTING TYPES ---
type HistoryItem = {
  id: number
  filename: string
  predictions: Array<{
    instrument: string
    confidence: number
  }>
}
// -----------------------

function History() {
  const navigate = useNavigate()
  const [history, setHistory] = useState<HistoryItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [allInstruments, setAllInstruments] = useState<string[]>([])
  const [selectedInstruments, setSelectedInstruments] = useState<string[]>([])
  const [filterMode, setFilterMode] = useState<'require' | 'exclude'>('require')
  const [userName, setUserName] = useState<string | null>(null)
  const [authReady, setAuthReady] = useState(false)

  useEffect(() => {
    const unsubscribe = auth.onAuthStateChanged((user) => {
      if (user) {
        setUserName(user.displayName || user.email || null)
      } else {
        setUserName(null)
      }
      setAuthReady(true)
    })

    return () => unsubscribe()
  }, [])

  useEffect(() => {
    if (!authReady) return
    fetchHistory()
  }, [authReady, selectedInstruments, filterMode])

  async function fetchHistory() {
    setLoading(true)
    setError(null)

    try {
      const params = new URLSearchParams()
      if (selectedInstruments.length > 0) {
        params.append('instruments', selectedInstruments.join(','))
        params.append('filterMode', filterMode)
      } else {
        params.append('filterMode', 'none')
      }

      // Get Firebase auth token
      const headers: HeadersInit = {}
      const user = auth.currentUser
      if (!user) {
        setError('Please sign in to view history')
        return
      }
      const token = await user.getIdToken()
      headers['Authorization'] = `Bearer ${token}`

      const response = await fetch(`/api/history/?${params.toString()}`, {
        method: 'GET',
        headers,
      })

      if (!response.ok) {
        throw new Error('Failed to fetch history')
      }

      const data = await response.json()
      setHistory(data.results || [])

      const instruments = new Set<string>()
      data.results.forEach((item: HistoryItem) => {
        item.predictions.forEach((pred) => {
          instruments.add(pred.instrument)
        })
      })
      setAllInstruments(Array.from(instruments).sort())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load history')
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = async () => {
    try {
      await signOut(auth)
      navigate('/')
    } catch (err) {
      console.error('Logout error:', err)
      navigate('/')
    }
  }

  function toggleInstrument(instrument: string) {
    setSelectedInstruments((prev) =>
      prev.includes(instrument)
        ? prev.filter((i) => i !== instrument)
        : [...prev, instrument]
    )
  }

  return (
    <div>
      <div className="logout-bar">
        <button onClick={() => navigate('/dashboard')} className="btn-history">
          Dashboard
        </button>
        <div className="logout-bar-right">
          {userName && <span className="welcome-text">Welcome {userName}</span>}
          <button onClick={handleLogout} className="btn-logout">
            Sign Out
          </button>
        </div>
      </div>

      <div className="app">
        <header>
          <h1>Analysis History</h1>
          <p>View and filter your previously analyzed songs</p>
        </header>

        {loading && (
          <div className="history-loading">
            <p>Loading your history...</p>
          </div>
        )}

        {error && (
          <div className="error">
            {error}
          </div>
        )}

        {!loading && !error && (
          <>
            <div className="filter-section">
              <div className="filter-header">
                <h2>Filter by Instruments</h2>
                <div className="filter-mode-toggle">
                  <button
                    className={`filter-mode-btn ${filterMode === 'require' ? 'active' : ''}`}
                    onClick={() => setFilterMode('require')}
                  >
                    Require
                  </button>
                  <button
                    className={`filter-mode-btn ${filterMode === 'exclude' ? 'active' : ''}`}
                    onClick={() => setFilterMode('exclude')}
                  >
                    Exclude
                  </button>
                </div>
              </div>

              {allInstruments.length > 0 ? (
                <div className="instrument-filters">
                  {allInstruments.map((instrument) => (
                    <button
                      key={instrument}
                      className={`instrument-filter-btn ${
                        selectedInstruments.includes(instrument) ? 'selected' : ''
                      }`}
                      onClick={() => toggleInstrument(instrument)}
                    >
                      {/* Using the icon component in the filter button for visual consistency */}
                      <InstrumentIcon name={instrument} />
                      {instrument}
                    </button>
                  ))}
                </div>
              ) : (
                <p className="no-instruments-available">No instruments found in your history</p>
              )}
            </div>

            <div className="history-results">
              <h2>
                {history.length} Song{history.length !== 1 ? 's' : ''}
                {selectedInstruments.length > 0 && (
                  <span className="filter-indicator">
                    ({filterMode === 'require' ? 'with' : 'without'}{' '}
                    {selectedInstruments.join(', ')})
                  </span>
                )}
              </h2>

              {history.length === 0 ? (
                <div className="no-history">
                  <p>No songs match your filters</p>
                </div>
              ) : (
                <div className="history-grid">
                  {history.map((item) => (
                    <div key={item.id} className="history-item">
                      <div className="history-item-header">
                        <h3>{item.filename}</h3>
                      </div>
                      <div className="tags">
                        {item.predictions.map((pred, i) => (
                          <span 
                            key={i} 
                            className="tag"
                            // ADDED STYLING to align the icon and text
                            style={{ 
                              display: 'flex', 
                              alignItems: 'center', 
                              fontSize: '14px' // Slightly smaller size for history view
                            }}
                          >
                            {/* --- DYNAMIC ICON INTEGRATION --- */}
                            <InstrumentIcon name={pred.instrument} />
                            {pred.instrument}
                            <span className="tag-confidence">
                              {/* Confidence percentage is calculated and rounded here */}
                              {Math.round(pred.confidence * 100)}%
                            </span>
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default History
