# Worship Flow — Frontend

This is the frontend for uploading a song (.mp3 or .mp4) and viewing placeholder instrument detection results. The actual backend/ML separation will be integrated later.

## Stack
- Vite
- React + TypeScript

## Getting started

1. Install dependencies (already done):
   - npm install

2. Run the dev server:
   - npm run dev

   Then open http://localhost:5173

3. Build for production:
   - npm run build

4. Preview the build locally:
   - npm run preview

## Notes
- The Analyze button currently simulates results client-side as a placeholder.
- Accepted formats: .mp3 and .mp4.
- Backend integration will replace the placeholder with a real API call (e.g. multipart upload to /api/analyze).
