import { useState } from 'react'
import { generateResponse } from '../api'
import ResultCard from './ResultCard'

const MODES = [
  { id: 'flirt', label: '😏 Флірт' },
  { id: 'put_in_place', label: '😤 Поставити на місце' },
  { id: 'joke', label: '😂 Пожартувати' },
  { id: 'soft_reject', label: '🙏 М\'яко відшити' },
  { id: 'support', label: '🤗 Підтримати' },
]

export default function GenerateScreen({ user, analysis, onBack }) {
  const [selectedMode, setSelectedMode] = useState(null)
  const [variants, setVariants] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [copied, setCopied] = useState(null)

  const handleGenerate = async (mode) => {
    setSelectedMode(mode)
    setLoading(true)
    setError(null)
    setVariants([])

    try {
      const result = await generateResponse(user.telegram_id, analysis.analysis_id, mode)
      setVariants(result.variants)
    } catch (e) {
      if (e.response?.status === 403) {
        setError('Генератор відповідей доступний тільки в Premium 💎')
      } else {
        setError('Щось пішло не так. Спробуй ще раз.')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleCopy = (text, index) => {
    navigator.clipboard.writeText(text)
    setCopied(index)
    setTimeout(() => setCopied(null), 2000)
  }

  return (
    <div className="screen">
      <div className="screen-header">
        <button className="back-btn" onClick={onBack}>←</button>
        <h2>✍️ Відповідь</h2>
      </div>

      <div className="screen-content">
        <ResultCard analysis={analysis} />

        <h3 className="section-title">Що робимо?</h3>

        <div className="modes-grid">
          {MODES.map(mode => (
            <button
              key={mode.id}
              className={`mode-btn ${selectedMode === mode.id ? 'active' : ''}`}
              onClick={() => handleGenerate(mode.id)}
            >
              {mode.label}
            </button>
          ))}
        </div>

        {loading && <div className="loading-text">⏳ Генерую варіанти...</div>}

        {error && <div className="error-msg">{error}</div>}

        {variants.length > 0 && (
          <div className="variants">
            <h3 className="section-title">Варіанти відповіді</h3>
            {variants.map((variant, i) => (
              <div key={i} className="variant-card">
                <div className="variant-label">{variant.label}</div>
                <div className="variant-text">{variant.text}</div>
                <button
                  className="copy-btn"
                  onClick={() => handleCopy(variant.text, i)}
                >
                  {copied === i ? '✅ Скопійовано' : '📋 Копіювати'}
                </button>
              </div>
            ))}

            <button
              className="regenerate-btn"
              onClick={() => handleGenerate(selectedMode)}
            >
              🔄 Перегенерувати
            </button>
          </div>
        )}
      </div>
    </div>
  )
}