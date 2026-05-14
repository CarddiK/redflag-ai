import { useState } from 'react'
import { createInvoice } from '../api'

const PLANS = [
  {
    id: 'light',
    name: 'Light',
    emoji: '✨',
    price_uah: null,
    price_stars: null,
    color: '#636366',
    features: [
      '5 аналізів на тиждень',
      'Режим "Друг"',
      'Базова аналітика',
    ],
    cta: 'Поточний план',
    disabled: true
  },
  {
    id: 'love_pro',
    name: 'Love Pro',
    emoji: '💜',
    price_uah: 199,
    price_uah_offer: 99,
    price_stars: 100,
    color: '#BF5AF2',
    popular: true,
    features: [
      '50 аналізів на місяць',
      'Всі режими відповідей',
      'Картотека крашів',
      'Генератор відповідей',
      'Порівняння крашів',
    ],
    cta: 'Обрати Love Pro'
  },
  {
    id: 'vip',
    name: 'VIP',
    emoji: '👑',
    price_uah: 300,
    price_stars: 250,
    color: '#FF9500',
    features: [
      'Безлімітні аналізи',
      'Всі функції Love Pro',
      'AI-Стиліст',
      'Пріоритетна швидкість',
      'Ранній доступ до нових фіч',
    ],
    cta: 'Стати VIP'
  }
]

export default function PremiumScreen({ user, onBack }) {
  const [paymentMethod, setPaymentMethod] = useState('stars')
  const [selectedPlan, setSelectedPlan] = useState('love_pro')
  const [loading, setLoading] = useState(false)
  const [showCardModal, setShowCardModal] = useState(false)

  // Чи є оффер першого місяця
  const hasOffer = !user.is_premium &&
    (user.free_analyses_used || 0) >= 3 &&
    !localStorage.getItem(`offer_used_${user.telegram_id}`)

  const handlePay = async (plan) => {
    if (plan.disabled) return

    if (paymentMethod === 'stars') {
      try {
        setLoading(true)
        await createInvoice(user.telegram_id, plan.id)
        if (plan.id === 'love_pro' && hasOffer) {
          localStorage.setItem(`offer_used_${user.telegram_id}`, '1')
        }
        window.Telegram?.WebApp?.close()
      } catch (e) {
        alert('Помилка при створенні інвойсу. Спробуй ще раз.')
      } finally {
        setLoading(false)
      }
    } else {
      setShowCardModal(true)
    }
  }

  const handleOpenManager = () => {
    const url = 'https://t.me/shrekpaupau'
    const tg = window.Telegram?.WebApp
    if (tg) {
      tg.openTelegramLink(url)
    } else {
      window.open(url, '_blank')
    }
    setShowCardModal(false)
  }

  const getCardPrice = (plan) => {
    if (plan.id === 'love_pro' && hasOffer) {
      return plan.price_uah_offer
    }
    return Math.round(plan.price_uah * 0.9)
  }

  return (
    <div className="screen">
      <div className="screen-header">
        <button className="back-btn" onClick={onBack}>←</button>
        <h2>💎 Premium</h2>
      </div>

      <div className="screen-content">

        <div className="premium-hero">
          <h2 className="premium-title">
            Стань тією,<br />
            <span>чиї повідомлення<br />чекають з трепетом</span>
          </h2>
          <p className="premium-subtitle">
            Розблокуй всі можливості AI-радника
          </p>
        </div>

        {hasOffer && (
          <div className="offer-banner">
            🔥 Спецпропозиція: перший місяць Love Pro за <strong>99 грн</strong>
          </div>
        )}

        <div className="payment-toggle">
          <button
            className={`payment-tab ${paymentMethod === 'stars' ? 'active' : ''}`}
            onClick={() => setPaymentMethod('stars')}
          >
            ⭐️ Telegram Stars
          </button>
          <button
            className={`payment-tab ${paymentMethod === 'card' ? 'active' : ''}`}
            onClick={() => setPaymentMethod('card')}
          >
            💳 Карткою
          </button>
        </div>

        {paymentMethod === 'card' && (
          <div className="card-discount-banner">
            🎉 {hasOffer ? 'Перший місяць за 99 грн!' : 'Знижка 10% при оплаті карткою!'}
          </div>
        )}

        <div className="plans-list">
          {PLANS.map(plan => (
            <div
              key={plan.id}
              className={`plan-card ${selectedPlan === plan.id ? 'selected' : ''} ${plan.popular ? 'popular' : ''} ${plan.disabled ? 'disabled' : ''}`}
              style={{ '--plan-color': plan.color }}
              onClick={() => !plan.disabled && setSelectedPlan(plan.id)}
            >
              {plan.popular && (
                <div className="plan-badge">🔥 Популярний</div>
              )}

              <div className="plan-header">
                <div className="plan-name-row">
                  <span className="plan-emoji">{plan.emoji}</span>
                  <span className="plan-name">{plan.name}</span>
                </div>
                <div className="plan-price">
                  {plan.disabled ? (
                    <span className="plan-free">Безкоштовно</span>
                  ) : paymentMethod === 'stars' ? (
                    <span className="plan-amount">
                      {plan.price_stars} <span className="plan-currency">⭐️</span>
                    </span>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
                      {plan.id === 'love_pro' && hasOffer && (
                        <span style={{ fontSize: 11, color: 'var(--text-muted)', textDecoration: 'line-through' }}>
                          {plan.price_uah} грн
                        </span>
                      )}
                      <span className="plan-amount">
                        {getCardPrice(plan)} <span className="plan-currency">грн</span>
                      </span>
                    </div>
                  )}
                  {!plan.disabled && <span className="plan-period">/міс</span>}
                </div>
              </div>

              <div className="plan-features">
                {plan.features.map((feature, i) => (
                  <div key={i} className="plan-feature">
                    <span className="feature-check" style={{ color: plan.color }}>✓</span>
                    <span>{feature}</span>
                  </div>
                ))}
              </div>

              {!plan.disabled && (
                <button
                  className={`plan-btn ${selectedPlan === plan.id ? 'active' : ''}`}
                  style={selectedPlan === plan.id ? { background: plan.color } : {}}
                  onClick={(e) => { e.stopPropagation(); handlePay(plan) }}
                  disabled={loading}
                >
                  {loading && selectedPlan === plan.id ? '⏳ Завантаження...' : plan.cta}
                </button>
              )}

              {plan.disabled && (
                <div className="plan-current">Твій поточний план</div>
              )}
            </div>
          ))}
        </div>

        <div className="fomo-banner">
          <span className="fomo-dot" />
          <span>⚡️ Акційна ціна діє обмежений час</span>
        </div>

        <div className="social-proof">
          <p className="social-quote">
            "Бот помітив що він пише мені тільки коли йому нудно. Я змінила тактику і тепер він сам кличе на побачення щотижня!"
          </p>
          <p className="social-author">— Катя, 22 роки</p>
        </div>

        <div className="tech-note">
          Використовуємо <strong>GPT-4o</strong> для максимально точного аналізу контексту та емоцій
        </div>

      </div>

      {showCardModal && (
        <div className="upgrade-overlay" onClick={() => setShowCardModal(false)}>
          <div className="upgrade-modal" onClick={e => e.stopPropagation()}>
            <div className="upgrade-icon">💳</div>
            <h3 className="upgrade-title">Оплата карткою</h3>
            <p className="upgrade-text">
              Для оплати карткою напишіть нашому менеджеру
            </p>
            <button className="action-btn" onClick={handleOpenManager}>
              Написати @shrekpaupau
            </button>
            <button className="upgrade-close" onClick={() => setShowCardModal(false)}>
              Закрити
            </button>
          </div>
        </div>
      )}
    </div>
  )
}