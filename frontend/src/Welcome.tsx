import { useNavigate } from 'react-router-dom'
import logo from "./assets/favicon.png";
import { FaGuitar } from 'react-icons/fa';

function Welcome() {
  const navigate = useNavigate()

  return (
    <div className="welcome-container">
      <div className="welcome-card">
        <div className="welcome-header">
          <div className="logo-wrapper">             
            <img src={logo} alt="Logo" width={115} height={115} />
            <div className="logo-square"></div>
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
            Login
            <span className="welcome-sub">If you already have an account</span>
          </button>
        </div>

        <p className="welcome-note"></p>
      </div>
    </div>
  )
}

export default Welcome
