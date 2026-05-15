import { useState } from 'react'

const SLIDES = [
  {
    emoji: '🚩',
    title: 'Ласкаво просимо до\nRedFlag AI',
    desc: 'Твій особистий AI-радник у стосунках. Читає між рядків те, що ти боїшся визнати.',
    color: '#FF2D55'
  },
  {
    emoji: '🔍',
    title: 'Аналіз переписки',
    desc: 'Завантаж скріншоти — і дізнайся чи він/вона реально зацікавлені, або просто не хочуть бути грубими.',
    color: '#BF5AF2',
    hint: '5 аналізів безкоштовно щотижня'
  },
  {
    emoji: '🔒',
    title: 'Твої дані в безпеці',
    desc: 'Ми не зберігаємо твої переписки. Скріншоти видаляються одразу після аналізу. Ніхто крім тебе не бачить результати.',
    color: '#00E676'
  }
]

export default function Onboarding({ onDone }) {
  const [current, setCurrent] = useState(0)
  const [animating, setAnimating] = useState(false)

  const slide = SLIDES[current]
  const isLast = current === SLIDES.length - 1

  const next = () => {
    if (animating) return
    if (isLast) {
      onDone()
      return
    }
    setAnimating(true)
    setTimeout(() => {
      setCurrent(c => c + 1)
      setAnimating(false)
    }, 200)
  }

  const skip = () => onDone()

  return (
    <div className="onboarding">
      {!isLast && (
        <button className="onboarding-skip" onClick={skip}>
          Пропустити
        </button>
      )}

      <div className={`onboarding-slide ${animating ? 'fade-out' : 'fade-in'}`}>
        <div className="onboarding-emoji-wrap" style={{ background: `${slide.color}18`, borderColor: `${slide.color}30` }}>
          <span className="onboarding-emoji">{slide.emoji}</span>
          <div className="onboarding-glow" style={{ background: slide.color }} />
        </div>

        <h2 className="onboarding-title" style={{ whiteSpace: 'pre-line' }}>
          {slide.title}
        </h2>

        <p className="onboarding-desc">{slide.desc}</p>

        {slide.hint && (
          <div className="onboarding-hint">
            ✨ {slide.hint}
          </div>
        )}
      </div>

      <div className="onboarding-dots">
        {SLIDES.map((_, i) => (
          <div
            key={i}
            className={`onboarding-dot ${i === current ? 'active' : ''}`}
            style={i === current ? { background: slide.color } : {}}
          />
        ))}
      </div>

      <button
        className="onboarding-btn"
        style={{ background: slide.color, boxShadow: `0 4px 20px ${slide.color}50` }}
        onClick={next}
      >
        {isLast ? 'Почати 🚀' : 'Далі →'}
      </button>
    </div>
  )
}