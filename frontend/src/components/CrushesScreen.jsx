import { useState, useEffect } from 'react'
import { getCrushes, compareCrushes } from '../api'

export default function CrushesScreen({ user, onBack, onAnalyzeCrush }) {
  const [crushes, setCrushes] = useState([])
  const [loading, setLoading] = useState(true)
  const [compareMode, setCompareMode] = useState(false)
  const [selected, setSelected] = useState([])
  const [comparison, setComparison] = useState(null)
  const [comparing, setComparing] = useState(false)
  const [expanded, setExpanded] = useState(null)

  useEffect(() => {
    loadCrushes()
  }, [])

  const loadCrushes = async () => {
    try {
      const data = await getCrushes(user.telegram_id)
      setCrushes(data)
    } finally {
      setLoading(false)
    }
  }

  const handleSelect = (crush) => {
    if (!compareMode) return
    if (selected.find(s => s.contact_id === crush.contact_id)) {
      setSelected(selected.filter(s => s.contact_id !== crush.contact_id))
    } else if (selected.length < 2) {
      setSelected([...selected, crush])
    }
  }

  const handleCompare = async () => {
    if (selected.length !== 2) return
    setComparing(true)
    try {
      const result = await compareCrushes(user.telegram_id, selected[0].contact_id, selected[1].contact_id)
      setComparison(result)
    } catch (e) {
      alert('Порівняння доступне тільки в Premium 💎')
    } finally {
      setComparing(false)
    }
  }

  const getInterestColor = (level) => {
    if (level >= 70) return '#4CAF50'
    if (level >= 40) return '#FF9800'
    return '#F44336'
  }

  const renderMiniChart = (history) => {
    if (!history || history.length < 2) return null

    const width = 200
    const height = 50
    const max = 100
    const points = history.map((h, i) => {
      const x = (i / (history.length - 1)) * width
      const y = height - (h.interest_level / max) * height
      return `${x},${y}`
    }).join(' ')

    const lastLevel = history[history.length - 1].interest_level
    const color = getInterestColor(lastLevel)

    return (
      <svg width={width} height={height} className="mini-chart">
        <polyline
          points={points}
          fill="none"
          stroke={color}
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        {history.map((h, i) => {
          const x = (i / (history.length - 1)) * width
          const y = height - (h.interest_level / max) * height
          return (
            <circle
              key={i}
              cx={x}
              cy={y}
              r="3"
              fill={color}
            />
          )
        })}
      </svg>
    )
  }

  if (loading) return <div className="loading"><div className="spinner" /></div>

  return (
    <div className="screen">
      <div className="screen-header">
        <button className="back-btn" onClick={onBack}>←</button>
        <h2>💘 Картотека крашів</h2>
        {crushes.length >= 2 && (
          <button
            className="compare-toggle"
            onClick={() => { setCompareMode(!compareMode); setSelected([]); setComparison(null) }}
          >
            {compareMode ? 'Скасувати' : '⚖️ Порівняти'}
          </button>
        )}
      </div>

      <div className="screen-content">
        {crushes.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">💘</div>
            <p>Тут будуть твої краші</p>
            <small>Зроби перший аналіз переписки щоб додати краша</small>
            <button className="action-btn" onClick={onBack} style={{marginTop: 16}}>
              🔍 Зробити аналіз
            </button>
          </div>
        ) : (
          <>
            {compareMode && (
              <div className="compare-hint">
                <span>Вибери 2 краші ({selected.length}/2)</span>
                {selected.length === 2 && (
                  <button className="action-btn small" onClick={handleCompare} disabled={comparing}>
                    {comparing ? '⏳' : '⚖️ Порівняти'}
                  </button>
                )}
              </div>
            )}

            {comparison && (
              <div className="comparison-result">
                <h3>🏆 {comparison.winner} перемагає!</h3>
                <p>{comparison.verdict}</p>
                <p className="final-advice">{comparison.final_advice}</p>
                <button className="action-btn small" onClick={() => setComparison(null)}>Закрити</button>
              </div>
            )}

            <div className="crushes-list">
              {crushes.map(crush => (
                <div
                  key={crush.contact_id}
                  className={`crush-card ${selected.find(s => s.contact_id === crush.contact_id) ? 'selected' : ''}`}
                  onClick={() => compareMode ? handleSelect(crush) : setExpanded(expanded === crush.contact_id ? null : crush.contact_id)}
                >
                  <div className="crush-header">
                    <div className="crush-name-row">
                      <strong>{crush.name}</strong>
                      <span className="crush-count">{crush.analyses_count} аналізів</span>
                    </div>
                    <span className="crush-interest" style={{ color: getInterestColor(crush.avg_interest) }}>
                      {crush.avg_interest}%
                    </span>
                  </div>

                  {crush.history.length >= 2 && (
                    <div className="crush-chart">
                      {renderMiniChart(crush.history)}
                      <div className="chart-labels">
                        <span style={{color: getInterestColor(crush.history[0].interest_level)}}>
                          {crush.history[0].interest_level}%
                        </span>
                        <span className="chart-arrow">→</span>
                        <span style={{color: getInterestColor(crush.history[crush.history.length-1].interest_level)}}>
                          {crush.history[crush.history.length-1].interest_level}%
                        </span>
                      </div>
                    </div>
                  )}

                  {expanded === crush.contact_id && (
                    <div className="crush-expanded">
                      <p className="crush-summary">{crush.last_analysis.summary}</p>
                      <button
                        className="analyze-crush-btn"
                        onClick={(e) => {
                          e.stopPropagation()
                          onAnalyzeCrush(crush.name)
                        }}
                      >
                        🔍 Проаналізувати ще раз
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  )
}