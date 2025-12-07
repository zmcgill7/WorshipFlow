import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import logo from "./assets/favicon.png";

const STORAGE_KEY = 'worshipUser'

function Login() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    try {
      const response = await fetch('/api/login/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          // "username" is no longer used for auth; we authenticate via email + password
          email: email.trim(),
          password,
        }),
      })

      const data = await response.json().catch(() => ({}))

      if (!response.ok) {
        setError(data.error || 'Invalid email or password. Please try again.')
        return
      }

      localStorage.setItem('isAuthenticated', 'true')
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({ id: data.id, name: data.name, email: data.email }),
      )

      navigate('/dashboard')
    } catch (err) {
      setError('Unable to sign in. Please try again later.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
         <div className="logo-wrapper">             
            <img src={logo} alt="Logo" width={115} height={115} />
            <div className="logo-square"></div>
          </div>
          <h1>Welcome back</h1>
          <p>Login to continue to your Worship Flow dashboard</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email"
              required
              autoComplete="email"
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              required
              autoComplete="current-password"
            />
          </div>

          {error && <p className="error">{error}</p>}

          <button
            type="submit"
            className="btn-login"
            disabled={isLoading}
          >
            {isLoading ? 'Logging in...' : 'Login'}
          </button>
        </form>

        <div className="auth-switch">
          <span>New to Worship Flow?</span>
          <button
            type="button"
            className="link-button"
            onClick={() => navigate('/signup')}
          >
            Create an account
          </button>
        </div>
      </div>
    </div>
  )
}

export default Login
