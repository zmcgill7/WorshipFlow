import React, { useEffect, useMemo, useState } from 'react'

type AnalysisResult = {
  instruments: string[]
}

function App() {
  const [file, setFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [analyzing, setAnalyzing] = useState(false)
  const [result, setResult] = useState<AnalysisResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!file) return
    const url = URL.createObjectURL(file)
    setPreviewUrl(url)
    return () => URL.revokeObjectURL(url)
  }, [file])

  const isVideo = useMemo(() => file?.type?.startsWith('video/'), [file])

  function handleFile(f: File | null) {
    setError(null)
    setResult(null)
    setFile(f)
  }

  function handleInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0] ?? null
    if (!f) return
    if (!/\.(mp3|mp4|wav)$/i.test(f.name)) {
      setError('Please select a .mp3, .mp4, or .wav file')
      return
    }
    handleFile(f)
  }

  function handleDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault()
    const f = e.dataTransfer.files?.[0] ?? null
    if (!f) return
    if (!/\.(mp3|mp4|wav)$/i.test(f.name)) {
      setError('Please drop a .mp3, .mp4, or .wav file')
      return
    }
    handleFile(f)
  }

  async function analyze() {
    if (!file) return
    setAnalyzing(true)
    setError(null)
    setResult(null)
    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch('/api/analyze/', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Failed to analyze file')
      }

      const data = await response.json()

      // Extract instruments from the first result
      if (data.results && data.results.length > 0) {
        const firstResult = data.results[0]
        if (firstResult.error) {
          throw new Error(firstResult.error)
        }
        if (firstResult.predictions) {
          const instruments = firstResult.predictions.map((p: any) => p.instrument)
          setResult({ instruments })
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze file.')
    } finally {
      setAnalyzing(false)
    }
  }

  return (
    <div className="app">
      <header>
        <h1>Worship Flow</h1>
        <p>Upload an .mp3, .mp4, or .wav to preview and simulate instrument detection.</p>
      </header>

      <section>
        <div
          className="dropzone"
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
          aria-label="Drop .mp3, .mp4, or .wav file here"
        >
          <p>Drag & drop a .mp3, .mp4, or .wav here, or select a file</p>
          <input type="file" accept=".mp3,.mp4,.wav,audio/mpeg,video/mp4,audio/wav,audio/x-wav,audio/wave" onChange={handleInputChange} />
        </div>

        {file && (
          <div className="preview">
            <strong>Selected:</strong> {file.name}
            {previewUrl && (
              isVideo ? (
                <video src={previewUrl} controls style={{ width: '100%', maxWidth: 520, marginTop: 12 }} />
              ) : (
                <audio src={previewUrl} controls style={{ width: '100%', marginTop: 12 }} />
              )
            )}
          </div>
        )}

        <div className="actions">
          <button
            className="btn-reactive"
            onMouseMove={(e) => {
              const r = (e.currentTarget as HTMLButtonElement).getBoundingClientRect()
              const x = e.clientX - r.left
              const y = e.clientY - r.top
              e.currentTarget.style.setProperty('--mx', `${x}px`)
              e.currentTarget.style.setProperty('--my', `${y}px`)
            }}
            onClick={analyze}
            disabled={!file || analyzing}
          >
            {analyzing ? 'Analyzing…' : 'Analyze instruments'}
          </button>
        </div>

        {error && <p className="error">{error}</p>}

        {result && (
          <div className="results">
            <h2>Detected instruments</h2>
            <div className="tags">
              {result.instruments.map((inst) => (
                <span key={inst} className="tag">
                  {inst}
                </span>
              ))}
            </div>
            <p className="note"></p>
          </div>
        )}
      </section>
    </div>
  )
}

export default App
