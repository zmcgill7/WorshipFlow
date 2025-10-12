import React, { useEffect, useMemo, useState } from 'react'

const ALL_INSTRUMENTS = ['vocals', 'drums', 'bass', 'piano', 'guitar', 'other'] as const

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
    if (!/\.(mp3|mp4)$/i.test(f.name)) {
      setError('Please select a .mp3 or .mp4 file')
      return
    }
    handleFile(f)
  }

  function handleDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault()
    const f = e.dataTransfer.files?.[0] ?? null
    if (!f) return
    if (!/\.(mp3|mp4)$/i.test(f.name)) {
      setError('Please drop a .mp3 or .mp4 file')
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
      // Simulate backend processing
      await new Promise((r) => setTimeout(r, 1200))
      const instruments = ALL_INSTRUMENTS.filter((_, i) => (file.name.length + i) % 2 === 0)
      if (instruments.length === 0) instruments.push('other')
      setResult({ instruments })
    } catch (err) {
      setError('Failed to analyze file (placeholder).')
    } finally {
      setAnalyzing(false)
    }
  }

  return (
    <div className="app">
      <header>
        <h1>Worship Flow</h1>
        <p>Upload an .mp3 or .mp4 to preview and simulate instrument detection.</p>
      </header>

      <section>
        <div
          className="dropzone"
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
          aria-label="Drop .mp3 or .mp4 file here"
        >
          <p>Drag & drop a .mp3 or .mp4 here, or select a file</p>
          <input type="file" accept=".mp3,.mp4,audio/mpeg,video/mp4" onChange={handleInputChange} />
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
          <button onClick={analyze} disabled={!file || analyzing}>
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
            <p className="note">Backend integration is TODO. This is a placeholder.</p>
          </div>
        )}
      </section>
    </div>
  )
}

export default App
