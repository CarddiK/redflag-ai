export default function Home({ user, onNavigate }) {
  const handleCopyReferral = () => {
    navigator.clipboard.writeText(user.referral_link)
  }

  const analysesLeft = user.is_premium
    ? '∞'
    : Math.max(0, 3 + (user.bonus_analyses || 0) - user.free_analyses_used)

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
      </div>

      <div className="stats-bar">
  <div className={`stat-chip ${user.is_premium ? 'premium' : ''}`} onClick={() => onNavigate('premium')}>
    <span className="stat-value">{analysesLeft}</span>
    <span className="stat-label">Аналізів</span>
  </div>
  <div className="stat-chip" onClick={() => onNavigate('referral')}>
    <span className="stat-value">{user.referral_count || 0}</span>
    <span className="stat-label">Рефералів</span>
  </div>
  <div className="stat-chip" onClick={() => onNavigate('premium')}>
    <span className="stat-value">{user.is_premium ? '💎' : '🔓'}</span>
    <span className="stat-label">{user.is_premium ? 'Premium' : 'Апгрейд'}</span>
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
            <span className="card-badge">NEW</span>
            <span className="card-icon">💘</span>
            <div className="card-content">
              <span className="card-title">Краші</span>
              <span className="card-desc">Картотека</span>
            </div>
          </button>

          <button className="menu-card" onClick={() => onNavigate('chat')}>
            <span className="card-icon">💬</span>
            <div className="card-content">
              <span className="card-title">Чат</span>
              <span className="card-desc">Друг / коуч</span>
            </div>
          </button>

          <button className="menu-card" onClick={() => onNavigate('outfit')}>
            <span className="card-icon">👗</span>
            <div className="card-content">
              <span className="card-title">Стиліст</span>
              <span className="card-desc">Оцінка образу</span>
            </div>
          </button>
        </div>
      </div>

      <div className="referral-banner" onClick={() => onNavigate('referral')}>
        <div className="referral-text">
          <strong>👥 Запроси друга — отримай +3 аналізи</strong>
          Натисни щоб скопіювати посилання
        </div>
        <button className="referral-copy">Копіювати</button>
      </div>
    </div>
  )
}