import { useState, useEffect } from 'react'

export default function Home({ user, onNavigate, analysesLeft }) {
  const [showPrivacy, setShowPrivacy] = useState(false)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    const seen = localStorage.getItem('privacy_seen')
    if (!seen) {
      setShowPrivacy(true)
    }
  }, [])

  const acceptPrivacy = () => {
    localStorage.setItem('privacy_seen', '1')
    setShowPrivacy(false)
  }

  const handleCopyReferral = (e) => {
    e.stopPropagation()
    navigator.clipboard.writeText(user.referral_link)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const leftCount = analysesLeft !== undefined
    ? analysesLeft
    : user.is_premium
      ? '∞'
      : Math.max(0, 5 + (user.bonus_analyses || 0) - user.free_analyses_used)

  const isPremium = user.is_premium
  const outfitLeft = 2 - (user.outfit_analyses_used || 0)
  const streak = user.streak_days || 0
  const achievements = user.achievements || []

  return (
    <div className="home">
      <div className="home-hero">
        <div className="home-logo">
          <div className="logo-icon">🚩</div>
          <span className="logo-text">RedFlag AI</span>
        </div>
        <h1 className="home-greeting">
          Привіт,<br />
          <span>що аналізуємо?</span>
        </h1>
        <p className="home-subtitle">Твій AI-радник у стосунках</p>
        {streak > 1 && (
  <div className="streak-banner" onClick={() => onNavigate('achievements')}>
    <span className="streak-fire">🔥</span>
    <span className="streak-text">
      <strong>{streak} днів поспіль!</strong> Так тримати
    </span>
    <span className="streak-arrow">→</span>
  </div>
)}
      </div>

      <div className="stats-bar">
        <div className={`stat-chip ${isPremium ? 'premium' : ''}`} onClick={() => onNavigate('premium')}>
          <span className="stat-value">{leftCount}</span>
          <span className="stat-label">Аналізів</span>
        </div>
        <div className="stat-chip" onClick={() => onNavigate('referral')}>
          <span className="stat-value">{user.referral_count || 0}</span>
          <span className="stat-label">Рефералів</span>
        </div>
        <div className="stat-chip" onClick={() => onNavigate('achievements')}>
          <span className="stat-value">{streak > 0 ? `${streak}🔥` : `${achievements.length}🏆`}</span>
          <span className="stat-label">{streak > 0 ? 'Streak' : 'Досяг.'}</span>
        </div>
      </div>

      <div className="menu-section">
        <p className="menu-label">Інструменти</p>
        <div className="menu-grid">
          <button className="menu-card primary" onClick={() => onNavigate('analyze')}>
            <span className="card-icon">🔍</span>
            <div className="card-content">
              <span className="card-title">Аналіз переписки</span>
              <span className="card-desc">Рівень інтересу та вайб</span>
            </div>
          </button>

          <button className="menu-card" onClick={() => onNavigate('crushes')}>
            {!isPremium && <span className="card-lock">🔒</span>}
            {isPremium && <span className="card-badge">NEW</span>}
            <span className="card-icon">💘</span>
            <div className="card-content">
              <span className="card-title">Краші</span>
              <span className="card-desc">{isPremium ? 'Картотека' : 'Love Pro+'}</span>
            </div>
          </button>

          <button className="menu-card" onClick={() => onNavigate('chat')}>
            <span className="card-icon">💬</span>
            <div className="card-content">
              <span className="card-title">Чат</span>
              <span className="card-desc">{isPremium ? 'Всі режими' : 'Тільки Друг'}</span>
            </div>
          </button>

          <button className="menu-card" onClick={() => onNavigate('outfit')}>
            {!isPremium && outfitLeft <= 0 && <span className="card-lock">🔒</span>}
            <span className="card-icon">👗</span>
            <div className="card-content">
              <span className="card-title">Стиліст</span>
              <span className="card-desc">
                {isPremium
                  ? 'Оцінка образу'
                  : outfitLeft <= 0
                    ? 'Потрібен VIP 👑'
                    : `${outfitLeft} безкоштовно`
                }
              </span>
            </div>
          </button>
        </div>

        {/* Кнопка досягнень */}
        <button className="achievements-btn" onClick={() => onNavigate('achievements')}>
          <span>🏆 Досягнення</span>
          <span className="achievements-btn-right">
            {achievements.length}/14
            <span className="achievements-btn-arrow">→</span>
          </span>
        </button>
      </div>

      <div className="referral-banner" onClick={() => onNavigate('referral')}>
        <div className="referral-text">
          <strong>👥 Запроси друга — отримай бонуси</strong>
          Натисни щоб дізнатись більше
        </div>
        <button className={`referral-copy ${copied ? 'copied' : ''}`} onClick={handleCopyReferral}>
          {copied ? '✓ Скопійовано' : 'Копіювати'}
        </button>
      </div>

      <div className="privacy-banner" onClick={() => setShowPrivacy(true)}>
        🔒 Ми не зберігаємо твої переписки — дані видаляються одразу після аналізу
      </div>

      {showPrivacy && (
        <div className="upgrade-overlay" onClick={acceptPrivacy}>
          <div className="privacy-modal" onClick={e => e.stopPropagation()}>
            <div className="privacy-modal-icon">🔐</div>
            <h3 className="privacy-modal-title">Твої дані в безпеці</h3>
            <div className="privacy-modal-body">
              <div className="privacy-item">
                <span className="privacy-check">✓</span>
                <span>Ми <strong>не зберігаємо</strong> твої переписки — скріншоти видаляються одразу після аналізу</span>
              </div>
              <div className="privacy-item">
                <span className="privacy-check">✓</span>
                <span>Аналіз виконує AI без участі людей</span>
              </div>
              <div className="privacy-item">
                <span className="privacy-check">✓</span>
                <span>Ми не передаємо дані третім особам</span>
              </div>
              <div className="privacy-item">
                <span className="privacy-check">✓</span>
                <span>Імена та дані крашів видно тільки тобі</span>
              </div>
            </div>
            <button className="action-btn" onClick={acceptPrivacy}>
              Зрозуміло, погнали 🚀
            </button>
          </div>
        </div>
      )}
    </div>
  )
}