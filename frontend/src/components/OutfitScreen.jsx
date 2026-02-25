import { useState } from 'react'
import { analyzeOutfit } from '../api'

export default function OutfitScreen({ user, onBack }) {
  const [file, setFile] = useState(null)
  const [destination, setDestination] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleAnalyze = async () => {
    if (!file) return setError('Завантаж фото образу')
    if (!destination.trim()) return setError('Вкажи куди збираєшся')

    setLoading(true)
    setError(null)

    try {
      const data = await analyzeOutfit(user.telegram_id, file, destination)
      setResult(data)
    } catch (e) {
      setError('Щось пішло не так. Спробуй ще раз.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="screen">
      <div className="screen-header">
        <button className="back-btn" onClick={onBack}>←</button>
        <h2>👗 Стиліст</h2>
      </div>

      <div className="screen-content">
        {!result ? (
          <>
            <div className="input-group">
              <label>Куди збираєшся?</label>
              <input
                type="text"
                placeholder="Побачення, вечірка, навчання, робота..."
                value={destination}
                onChange={e => setDestination(e.target.value)}
              />
            </div>

            <div className="input-group">
              <label>Фото образу</label>
              <div className="upload-area" onClick={() => document.getElementById('outfit-input').click()}>
                {file ? (
                  <div>
                    <img src={URL.createObjectURL(file)} alt="outfit" className="outfit-preview" />
                    <p>{file.name}</p>
                  </div>
                ) : (
                  <>
                    <span className="upload-icon">👗</span>
                    <span>Натисни щоб завантажити фото</span>
                  </>
                )}
              </div>
              <input
                id="outfit-input"
                type="file"
                accept="image/*"
                style={{ display: 'none' }}
                onChange={e => setFile(e.target.files[0])}
              />
            </div>

            {error && <div className="error-msg">{error}</div>}

            <button className="action-btn" onClick={handleAnalyze} disabled={loading}>
              {loading ? '⏳ Аналізую образ...' : '👗 Оцінити образ'}
            </button>
          </>
        ) : (
          <div className="outfit-result">
            <div className="outfit-vibe">"{result.vibe}"</div>

            <div className="outfit-score">
              <span className="score-number">{result.score}</span>
              <span className="score-label">/100</span>
            </div>

            <div className="outfit-section">
              <h4>✅ Що зайшло</h4>
              {result.what_works?.map((item, i) => (
                <div key={i} className="outfit-item good">👍 {item}</div>
              ))}
            </div>

            <div className="outfit-section">
              <h4>⚠️ Що змінити</h4>
              {result.fix_this?.map((item, i) => (
                <div key={i} className="outfit-item bad">✏️ {item}</div>
              ))}
            </div>

            <div className="outfit-verdict">
              <p>{result.final_verdict}</p>
            </div>

            <button className="action-btn" onClick={() => { setResult(null); setFile(null); setDestination('') }}>
              🔄 Оцінити інший образ
            </button>
          </div>
        )}
      </div>
    </div>
  )
}