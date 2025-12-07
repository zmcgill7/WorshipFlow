import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import logo from "./assets/favicon.png";


const STORAGE_KEY = 'worshipUser'

function Signup() {
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (!name.trim() || !email.trim() || !password.trim()) {
      setError('Please fill in all fields.')
      return
    }

    setIsLoading(true)

    try {
      const response = await fetch('/api/signup/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          name: name.trim(),
          email: email.trim(),
          password,
        }),
      })

      const data = await response.json().catch(() => ({}))

      if (!response.ok) {
        setError(data.error || 'Unable to sign up. Please try again.')
        return
      }

      // Persist authenticated user information locally (without password)
      localStorage.setItem('isAuthenticated', 'true')
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({ id: data.id, name: data.name, email: data.email }),
      )

      navigate('/dashboard')
    } catch (err) {
      setError('Unable to sign up. Please try again later.')
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
          <h1>Create your account</h1>
          <p>Sign up to start using Worship Flow</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label htmlFor="name">Name</label>
            <input
              type="text"
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter your name"
              required
              autoComplete="name"
            />
          </div>

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
              placeholder="Create a password"
              required
              autoComplete="new-password"
            />
          </div>

          {error && <p className="error">{error}</p>}

          <button
            type="submit"
            className="btn-login"
            disabled={isLoading}
          >
            {isLoading ? 'Creating account...' : 'Sign Up'}
          </button>
        </form>

        <div className="auth-switch">
          <span>Already a user?</span>
          <button
            type="button"
            className="link-button"
            onClick={() => navigate('/login')}
          >
            Sign in
          </button>
        </div>
      </div>
    </div>
  )
}

export default Signup
