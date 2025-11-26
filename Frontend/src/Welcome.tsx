import React from 'react'
import { useNavigate } from 'react-router-dom'

function Welcome() {
  const navigate = useNavigate()

  return (
    <div className="welcome-container">
      <div className="welcome-card">
        <div className="welcome-header">
          <div className="logo-circle large">
            <svg width="56" height="56" viewBox="0 0 40 40" fill="none">
              <path
                d="M20 5L25 15H35L27 22L30 32L20 26L10 32L13 22L5 15H15L20 5Z"
                fill="url(#gradient)"
                stroke="currentColor"
                strokeWidth="1.5"
              />
              <defs>
                <linearGradient id="gradient" x1="5" y1="5" x2="35" y2="35">
                  <stop offset="0%" stopColor="#60a5fa" />
                  <stop offset="100%" stopColor="#a5b4fc" />
                </linearGradient>
              </defs>
            </svg>
          </div>
          <h1>Welcome to Worship Flow</h1>
          <p>Plan, organize, and flow through your worship sets with ease.</p>
        </div>

        <div className="welcome-options">
          <button
            className="welcome-button primary"
            onClick={() => navigate('/signup')}
          >
            I am new here
            <span className="welcome-sub">Create a new Worship Flow account</span>
          </button>

          <button
            className="welcome-button secondary"
            onClick={() => navigate('/login')}
          >
            I already have an account
            <span className="welcome-sub">Sign in </span>
          </button>
        </div>

        <p className="welcome-note"></p>
      </div>
    </div>
  )
}

export default Welcome
