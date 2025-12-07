import { useEffect } from 'react'

function BackgroundVisual() {
  useEffect(() => {
    const handlePointerMove = (event: PointerEvent) => {
      const xRatio = event.clientX / window.innerWidth || 0.5
      const yRatio = event.clientY / window.innerHeight || 0.5

      document.documentElement.style.setProperty('--pointer-x', xRatio.toString())
      document.documentElement.style.setProperty('--pointer-y', yRatio.toString())
    }

    window.addEventListener('pointermove', handlePointerMove)
    return () => window.removeEventListener('pointermove', handlePointerMove)
  }, [])

  return (
    <div className="background-visual" aria-hidden="true">
      <div className="background-wave" />
      <div className="audio-bars">
        {Array.from({ length: 18 }).map((_, index) => (
          <span key={index} className="audio-bar" />
        ))}
      </div>
    </div>
  )
}

export default BackgroundVisual
