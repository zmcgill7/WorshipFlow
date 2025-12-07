import React, { useState } from 'react'
import logo from "./assets/favicon.png";
// --- NEW ICON IMPORTS ---
import { FaGuitar, FaDrum, FaMicrophone, FaKeyboard } from 'react-icons/fa';
import { GiViolin, GiTrumpet, GiGuitarBassHead } from 'react-icons/gi'; 


// --- NEW ICON MAPPING ---
// A dictionary to map instrument strings to their icon components
const instrumentIconMap: { [key: string]: React.ElementType } = {
  'guitar': FaGuitar,
  'bass': GiGuitarBassHead,
  'keyboard': FaKeyboard,
  'drums': FaDrum,
  'strings': GiViolin,
  'brass': GiTrumpet,
  'vocals': FaMicrophone,
};

// --- NEW HELPER FUNCTION ---
// Function to get the correct icon component, defaulting to null if not found
const InstrumentIcon = ({ name }: { name: string }) => {
  const IconComponent = instrumentIconMap[name.toLowerCase()];
  
  if (!IconComponent) {
    return null; // Return nothing if the instrument name isn't mapped
  }

  // Render the component with desired size
  return <IconComponent size={20} style={{ marginRight: '5px' }} />;
};


// --- EXISTING TYPES ---
type FileWithPreview = {
  file: File
  previewUrl: string
  isVideo: boolean
}

type FileAnalysisResult = {
  fileName: string
  instruments: string[]
  error?: string
}
// -----------------------

function App() {
  const [files, setFiles] = useState<FileWithPreview[]>([])
  const [analyzing, setAnalyzing] = useState(false)
  const [results, setResults] = useState<FileAnalysisResult[]>([])
  const [error, setError] = useState<string | null>(null)

  function addFiles(newFiles: FileList | File[]) {
    setError(null)
    setResults([])

    const fileArray = Array.from(newFiles)
    const validFiles: FileWithPreview[] = []
    const invalidFiles: string[] = []

    fileArray.forEach((file) => {
      if (/\.(mp3|mp4|wav)$/i.test(file.name)) {
        const previewUrl = URL.createObjectURL(file)
        const isVideo = file.type.startsWith('video/')
        validFiles.push({ file, previewUrl, isVideo })
      } else {
        invalidFiles.push(file.name)
      }
    })

    if (invalidFiles.length > 0) {
      setError(`Invalid file(s): ${invalidFiles.join(', ')}. Only .mp3, .mp4, or .wav files are allowed.`)
    }

    if (validFiles.length > 0) {
      setFiles((prev) => {
        // Clean up old preview URLs
        prev.forEach((f) => URL.revokeObjectURL(f.previewUrl))
        return validFiles
      })
    }
  }

  function handleInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    const fileList = e.target.files
    if (!fileList || fileList.length === 0) return
    addFiles(fileList)
  }

  function handleDrop(e: React.DragEvent<HTMLDivElement>) {
    e.preventDefault()
    const fileList = e.dataTransfer.files
    if (!fileList || fileList.length === 0) return
    addFiles(fileList)
  }

  function removeFile(index: number) {
    setFiles((prev) => {
      const newFiles = [...prev]
      URL.revokeObjectURL(newFiles[index].previewUrl)
      newFiles.splice(index, 1)
      return newFiles
    })
  }

  async function analyzeFiles() {
    if (files.length === 0) return
    setAnalyzing(true)
    setError(null)
    setResults([])

    const analysisResults: FileAnalysisResult[] = []

    try {
      // Analyze each file individually
      for (const { file } of files) {
        try {
          const formData = new FormData()
          formData.append('file', file)

          const response = await fetch('/api/analyze/', {
            method: 'POST',
            body: formData,
          })

          if (!response.ok) {
            const errorData = await response.json()
            analysisResults.push({
              fileName: file.name,
              instruments: [],
              error: errorData.error || 'Failed to analyze file',
            })
            continue
          }

          const data = await response.json()

          // Extract instruments from the first result
          if (data.results && data.results.length > 0) {
            const firstResult = data.results[0]
            if (firstResult.error) {
              analysisResults.push({
                fileName: file.name,
                instruments: [],
                error: firstResult.error,
              })
            } else if (firstResult.predictions) {
              const instruments = firstResult.predictions.map((p: any) => p.instrument)
              analysisResults.push({
                fileName: file.name,
                instruments,
              })
            }
          } else {
            analysisResults.push({
              fileName: file.name,
              instruments: [],
              error: 'No analysis results returned',
            })
          }
        } catch (err) {
          analysisResults.push({
            fileName: file.name,
            instruments: [],
            error: err instanceof Error ? err.message : 'Failed to analyze file',
          })
        }
      }

      setResults(analysisResults)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to analyze files.')
    } finally {
      setAnalyzing(false)
    }
  }

  return (
    <div className="app">
      <header>
         <div className="logo-wrapper">             
            <img src={logo} alt="Logo" width={115} height={115} />
            <div className="logo-square"></div>
          </div>        
        <h1>Worship Flow</h1>
        <p>Upload multiple .mp3, .mp4, or .wav files to analyze instruments simultaneously.</p>
      </header>

      <section className="layout">
        <div className="analysis-column">
          <div
            className="dropzone"
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            aria-label="Drop .mp3, .mp4, or .wav files here"
          >
            <p>Drag & drop multiple .mp3, .mp4, or .wav files here, or select files</p>
            <input
              type="file"
              accept=".mp3,.mp4,.wav,audio/mpeg,video/mp4,audio/wav,audio/x-wav,audio/wave"
              onChange={handleInputChange}
              multiple
            />
          </div>

          {files.length > 0 && (
            <div className="file-list">
              <h3>Selected Files ({files.length})</h3>
              <div className="files-grid">
                {files.map((fileWithPreview, index) => (
                  <div key={index} className="file-item">
                    <div className="file-header">
                      <span className="file-name">{fileWithPreview.file.name}</span>
                      <button
                        className="btn-remove"
                        onClick={() => removeFile(index)}
                        aria-label="Remove file"
                      >
                        ✕
                      </button>
                    </div>
                    {fileWithPreview.isVideo ? (
                      <video
                        src={fileWithPreview.previewUrl}
                        controls
                        className="file-preview"
                      />
                    ) : (
                      <audio
                        src={fileWithPreview.previewUrl}
                        controls
                        className="file-preview"
                      />
                    )}
                  </div>
                ))}
              </div>
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
              onClick={analyzeFiles}
              disabled={files.length === 0 || analyzing}
            >
              {analyzing ? `Analyzing ${files.length} file(s)…` : `Analyze ${files.length} file(s)`}
            </button>
          </div>

          {error && <p className="error">{error}</p>}

          {results.length > 0 && (
            <div className="results-container">
              <h2>Analysis Results</h2>
              {results.map((result, index) => (
                <div key={index} className="results">
                  <div className="result-header">
                    <h3>{result.fileName}</h3>
                    {result.error && <span className="result-error">❌ {result.error}</span>}
                  </div>
                  {!result.error && result.instruments.length > 0 && (
                    <div className="tags">
                      {result.instruments.map((inst, i) => (
                        <span 
                          key={i} 
                          className="tag"
                          // ADDED STYLING to align the icon and text
                          style={{ 
                            display: 'flex', 
                            alignItems: 'center', 
                            fontSize: '16px'
                          }}
                        >
                          {/* --- DYNAMIC ICON COMPONENT --- */}
                          <InstrumentIcon name={inst} />
                          {inst}
                        </span>
                      ))}
                    </div>
                  )}
                  {!result.error && result.instruments.length === 0 && (
                    <p className="no-instruments">No instruments detected</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </section>
    </div>
  )
}

export default App