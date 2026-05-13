import { useState } from 'react'

const REWARDS = [
  {
    at: 2,
    icon: '🎁',
    title: '+10 аналізів',
    desc: 'Безкоштовно',
    color: '#00E676'
  },
  {
    at: 5,
    icon: '💜',
    title: 'Love Pro',
    desc: '1 тиждень безкоштовно',
    color: '#BF5AF2'
  },
  {
    at: 10,
    icon: '👑',
    title: 'VIP',
    desc: '2 тижні безкоштовно',
    color: '#FF9500'
  }
]

export default function ReferralScreen({ user, onBack }) {
  const [copied, setCopied] = useState(false)
  const count = user.referral_count || 0
  const next = user.next_reward

  const handleCopy = () => {
    navigator.clipboard.writeText(user.referral_link)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleShare = () => {
    const text = `Привіт! Я користуюсь RedFlag AI — він аналізує переписки і підказує що думає людина насправді 👀\n\nСпробуй безкоштовно:`
    const shareUrl = `https://t.me/share/url?url=${encodeURIComponent(user.referral_link)}&text=${encodeURIComponent(text)}`
    const tg = window.Telegram?.WebApp
    if (tg) {
      tg.openTelegramLink(shareUrl)
    } else {
      window.open(shareUrl, '_blank')
    }
  }

  const getRewardStatus = (reward) => {
    if (count >= reward.at) return 'done'
    if (next && next.at === reward.at) return 'next'
    return 'locked'
  }

  return (
    <div className="screen">
      <div className="screen-header">
        <button className="back-btn" onClick={onBack}>←</button>
        <h2>👥 Реферальна програма</h2>
      </div>

      <div className="screen-content">

        {/* Лічильник */}
        <div className="referral-counter">
          <div className="referral-counter-inner">
            <span className="referral-big-num">{count}</span>
            <span className="referral-big-label">запрошено друзів</span>
          </div>
          {next && (
            <div className="referral-next">
              <span className="referral-next-text">
                Ще <strong>{next.left}</strong> до: {next.desc}
              </span>
              <div className="referral-progress-bar">
                <div
                  className="referral-progress-fill"
                  style={{
                    width: `${Math.min(100, (count / next.at) * 100)}%`
                  }}
                />
              </div>
            </div>
          )}
          {!next && (
            <div className="referral-maxed">
              🏆 Ти досяг максимального рівня!
            </div>
          )}
        </div>

        {/* Нагороди */}
        <div className="rewards-section">
          <p className="section-label">Нагороди</p>
          <div className="rewards-list">
            {REWARDS.map(reward => {
              const status = getRewardStatus(reward)
              return (
                <div
                  key={reward.at}
                  className={`reward-card ${status}`}
                  style={{ '--reward-color': reward.color }}
                >
                  <div className="reward-left">
                    <div className="reward-icon">{reward.icon}</div>
                    <div className="reward-info">
                      <span className="reward-title">{reward.title}</span>
                      <span className="reward-desc">{reward.desc}</span>
                    </div>
                  </div>
                  <div className="reward-right">
                    {status === 'done' ? (
                      <div className="reward-status done">✓ Отримано</div>
                    ) : status === 'next' ? (
                      <div className="reward-status next">{reward.at} друзів</div>
                    ) : (
                      <div className="reward-status locked">🔒 {reward.at}</div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Посилання */}
        <div className="referral-link-section">
          <p className="section-label">Твоє посилання</p>
          <div className="referral-link-box">
            <span className="referral-link-text">{user.referral_link}</span>
          </div>
          <button className="action-btn" onClick={handleCopy}>
            {copied ? '✅ Скопійовано!' : '📋 Скопіювати посилання'}
          </button>
          <button className="share-btn" onClick={handleShare}>
            ✈️ Запросити друзів
          </button>
        </div>

        {/* Як це працює */}
        <div className="how-it-works">
          <p className="section-label">Як це працює</p>
          <div className="how-steps">
            <div className="how-step">
              <span className="how-num">1</span>
              <span className="how-text">Скопіюй своє посилання і відправ другу</span>
            </div>
            <div className="how-step">
              <span className="how-num">2</span>
              <span className="how-text">Друг запускає бота по твоєму посиланню</span>
            </div>
            <div className="how-step">
              <span className="how-num">3</span>
              <span className="how-text">Ти автоматично отримуєш нагороду</span>
            </div>
          </div>
        </div>

      </div>
    </div>
  )
}
