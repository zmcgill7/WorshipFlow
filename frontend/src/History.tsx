import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

type HistoryItem = {
  id: number
  filename: string
  predictions: Array<{
    instrument: string
    confidence: number
  }>
}

function History() {
  const navigate = useNavigate()
  const [history, setHistory] = useState<HistoryItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [allInstruments, setAllInstruments] = useState<string[]>([])
  const [selectedInstruments, setSelectedInstruments] = useState<string[]>([])
  const [filterMode, setFilterMode] = useState<'require' | 'exclude'>('require')
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

  useEffect(() => {
    fetchHistory()
  }, [selectedInstruments, filterMode])

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

      const response = await fetch(`/api/history/?${params.toString()}`, {
        method: 'GET',
        credentials: 'include',
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
      await fetch('/api/logout/', {
        method: 'POST',
        credentials: 'include',
      })
    } catch (err) {
      // Ignore network errors on logout
    } finally {
      localStorage.removeItem('isAuthenticated')
      localStorage.removeItem('worshipUser')
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
                          <span key={i} className="tag">
                            {pred.instrument}
                            <span className="tag-confidence">
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
