import { useState, useEffect } from 'react'
import { analyzeScreenshots } from '../api'

export default function AnalyzeScreen({ user, onBack, onAnalyzed, prefilledCrush }) {
  const [files, setFiles] = useState([])
  const [crushName, setCrushName] = useState('')
  const [context, setContext] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (prefilledCrush) setCrushName(prefilledCrush)
  }, [prefilledCrush])

  const handleAnalyze = async () => {
    if (!files.length) return setError('Завантаж хоча б один скріншот')
    if (!crushName.trim()) return setError("Вкажи ім'я краша")

    setLoading(true)
    setError(null)

    try {
      const result = await analyzeScreenshots(user.telegram_id, files, crushName, context)
      onAnalyzed(result)
    } catch (e) {
      if (e.response?.status === 403) {
        setError('Ліміт безкоштовних аналізів вичерпано. Оформи Premium 💎')
      } else {
        setError('Щось пішло не так. Спробуй ще раз.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="screen">
      <div className="screen-header">
        <button className="back-btn" onClick={onBack}>←</button>
        <h2>🔍 Аналіз переписки</h2>
      </div>

      <div className="screen-content">
        <div className="input-group">
          <label>Ім'я краша</label>
          <input
            type="text"
            placeholder="Макс, Даша, Хлопець з універу..."
            value={crushName}
            onChange={e => setCrushName(e.target.value)}
          />
        </div>

        <div className="input-group">
          <label>Скріншоти переписки (до 5 штук)</label>
          <div className="upload-area" onClick={() => document.getElementById('file-input').click()}>
            {files.length ? (
              <div className="files-preview">
                {files.map((f, i) => (
                  <div key={i} className="file-chip">📸 {f.name}</div>
                ))}
                <span className="add-more">+ ще</span>
              </div>
            ) : (
              <>
                <span className="upload-icon">📸</span>
                <span>Натисни щоб завантажити</span>
              </>
            )}
          </div>
          <input
            id="file-input"
            type="file"
            accept="image/*"
            multiple
            style={{ display: 'none' }}
            onChange={e => setFiles(Array.from(e.target.files).slice(0, 5))}
          />
        </div>

        <div className="input-group">
          <label>Контекст (необов'язково)</label>
          <textarea
            placeholder="Знайомі 2 тижні, він написав першим після тижня мовчання..."
            value={context}
            onChange={e => setContext(e.target.value)}
            rows={3}
          />
        </div>

        {error && <div className="error-msg">{error}</div>}

        <button className="action-btn" onClick={handleAnalyze} disabled={loading}>
          {loading ? '⏳ Аналізую...' : '🔍 Проаналізувати'}
        </button>
      </div>
    </div>
  )
}