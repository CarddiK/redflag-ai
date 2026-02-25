export default function ResultCard({ analysis }) {
  const getColor = (level) => {
    if (level >= 70) return '#00E676'
    if (level >= 40) return '#FF9500'
    return '#FF2D55'
  }

  const getEmoji = (level) => {
    if (level >= 70) return '🔥'
    if (level >= 40) return '🤔'
    return '💀'
  }

  const color = getColor(analysis.interest_level)
  const circumference = 2 * Math.PI * 30
  const progress = (analysis.interest_level / 100) * circumference

  const renderRedFlags = () => {
    if (!analysis.red_flags?.length) return null
    const isNewFormat = typeof analysis.red_flags[0] === 'object'

    return (
      <div className="red-flags">
        <p className="red-flags-title">🚩 Червоні прапорці</p>
        {analysis.red_flags.map((flag, i) => (
          isNewFormat ? (
            <div key={i} className="flag-item-detailed">
              <div className="flag-title">⚠️ {flag.flag}</div>
              <div className="flag-psychotype">{flag.psychotype}</div>
              <div className="flag-advice">{flag.advice}</div>
            </div>
          ) : (
            <div key={i} className="flag-item">⚠️ {flag}</div>
          )
        ))}
      </div>
    )
  }

  return (
    <div className="result-card">
      <div className="result-hero" style={{ '--accent': color }}>
        <div className="interest-ring">
          <svg width="80" height="80" viewBox="0 0 80 80">
            <circle cx="40" cy="40" r="30" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="6" />
            <circle
              cx="40" cy="40" r="30"
              fill="none"
              stroke={color}
              strokeWidth="6"
              strokeDasharray={`${progress} ${circumference}`}
              strokeLinecap="round"
              style={{ filter: `drop-shadow(0 0 6px ${color})` }}
            />
          </svg>
          <div className="interest-ring-text">
            <span className="interest-number" style={{ color }}>{analysis.interest_level}%</span>
            <span className="interest-emoji">{getEmoji(analysis.interest_level)}</span>
          </div>
        </div>

        <div className="result-hero-info">
          {analysis.vibe_check && (
            <div className="vibe-check">"{analysis.vibe_check}"</div>
          )}
          <div className="result-badges">
            {analysis.tone && <span className="badge">{analysis.tone}</span>}
            {analysis.response_pattern && <span className="badge">{analysis.response_pattern}</span>}
          </div>
        </div>
      </div>

      <div className="result-divider" />
      <p className="result-summary">{analysis.summary}</p>

      {renderRedFlags()}

      {analysis.free_analyses_left !== null && analysis.free_analyses_left !== undefined && (
        <div className="analyses-left">
          Залишилось аналізів: <strong>{analysis.free_analyses_left}</strong>
        </div>
      )}
    </div>
  )
}