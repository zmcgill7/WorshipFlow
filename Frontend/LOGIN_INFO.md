# Login Information

## Demo Credentials

Use these credentials to access the Worship Flow dashboard:

- **Username:** `worshipadmin`
- **Email:** `admin@worshipflow.com`
- **Password:** `worship123`

## How to Use

1. Start the development server:
   ```bash
   npm run dev
   ```

2. Open your browser to `http://localhost:5173`

3. You'll see the login page first

4. Enter the demo credentials above

5. Click "Sign In" to access the Worship Flow dashboard

6. Use the "Sign Out" button in the top-right corner to return to the login page

## Features

- **Dark theme** login page matching the application's visual style
- **Form validation** for required fields
- **Protected routes** - dashboard requires authentication
- **Session persistence** - uses localStorage to maintain login state
- **Responsive design** - works on all screen sizes
- **Smooth animations** - fade-in effects and interactive hover states

## Technical Details

- Built with React, TypeScript, and React Router
- Authentication state stored in localStorage
- Protected route component prevents unauthorized access
- Automatic redirect to login if not authenticated
