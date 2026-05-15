const ALL_ACHIEVEMENTS = [
  {
    key: 'first_analysis',
    title: 'Перший аналіз 🔍',
    desc: 'Зроби перший аналіз переписки',
    bonus: '+1 аналіз',
    category: 'Аналізи'
  },
  {
    key: 'analyses_5',
    title: '5 аналізів 📊',
    desc: 'Зроби 5 аналізів переписки',
    bonus: '+2 аналізи',
    category: 'Аналізи'
  },
  {
    key: 'analyses_10',
    title: 'Детектив 🕵️',
    desc: 'Зроби 10 аналізів переписки',
    bonus: '+3 аналізи',
    category: 'Аналізи'
  },
  {
    key: 'analyses_25',
    title: 'Профі 💼',
    desc: 'Зроби 25 аналізів переписки',
    bonus: '+5 аналізів',
    category: 'Аналізи'
  },
  {
    key: 'analyses_50',
    title: 'Легенда 👑',
    desc: 'Зроби 50 аналізів переписки',
    bonus: 'Love Pro на 3 дні',
    category: 'Аналізи'
  },
  {
    key: 'streak_3',
    title: '3 дні поспіль 🔥',
    desc: 'Заходь 3 дні поспіль',
    bonus: '+2 аналізи',
    category: 'Streak'
  },
  {
    key: 'streak_7',
    title: 'Тижневий стрік 🔥🔥',
    desc: 'Заходь 7 днів поспіль',
    bonus: '+5 аналізів',
    category: 'Streak'
  },
  {
    key: 'streak_14',
    title: '2 тижні поспіль 💪',
    desc: 'Заходь 14 днів поспіль',
    bonus: 'Love Pro на тиждень',
    category: 'Streak'
  },
  {
    key: 'streak_30',
    title: 'Місяць поспіль 🏆',
    desc: 'Заходь 30 днів поспіль',
    bonus: 'VIP на тиждень',
    category: 'Streak'
  },
  {
    key: 'first_redflag',
    title: 'Перший редфлаг 🚩',
    desc: 'Знайди перший редфлаг',
    bonus: '+1 аналіз',
    category: 'Редфлаги'
  },
  {
    key: 'redflags_10',
    title: 'Детектор брехні 🎯',
    desc: 'Знайди 10 редфлагів',
    bonus: '+2 спроби стиліста',
    category: 'Редфлаги'
  },
  {
    key: 'redflags_25',
    title: 'Психолог 🧠',
    desc: 'Знайди 25 редфлагів',
    bonus: '+5 аналізів',
    category: 'Редфлаги'
  },
  {
    key: 'first_message',
    title: 'Перша розмова 💬',
    desc: 'Відправ перше повідомлення в чаті',
    bonus: '+1 аналіз',
    category: 'Чат'
  },
  {
    key: 'messages_10',
    title: 'Балакун 🗣️',
    desc: 'Відправ 10 повідомлень в чаті',
    bonus: '+2 спроби стиліста',
    category: 'Чат'
  },
]

const CATEGORIES = ['Аналізи', 'Streak', 'Редфлаги', 'Чат']

export default function AchievementsScreen({ user, onBack }) {
  const earned = user.achievements || []
  const streak = user.streak_days || 0
  const total = user.total_analyses || 0
  const earnedCount = earned.length
  const totalCount = ALL_ACHIEVEMENTS.length

  return (
    <div className="screen">
      <div className="screen-header">
        <button className="back-btn" onClick={onBack}>←</button>
        <h2>🏆 Досягнення</h2>
      </div>

      <div className="screen-content">

        {/* Статистика */}
        <div className="achieve-stats">
          <div className="achieve-stat">
            <span className="achieve-stat-val">{earnedCount}/{totalCount}</span>
            <span className="achieve-stat-label">Отримано</span>
          </div>
          <div className="achieve-stat">
            <span className="achieve-stat-val">{streak}🔥</span>
            <span className="achieve-stat-label">Streak</span>
          </div>
          <div className="achieve-stat">
            <span className="achieve-stat-val">{total}</span>
            <span className="achieve-stat-label">Аналізів</span>
          </div>
        </div>

        {/* Прогрес бар */}
        <div className="achieve-progress-wrap">
          <div className="achieve-progress-bar">
            <div
              className="achieve-progress-fill"
              style={{ width: `${Math.round(earnedCount / totalCount * 100)}%` }}
            />
          </div>
          <span className="achieve-progress-text">
            {Math.round(earnedCount / totalCount * 100)}% завершено
          </span>
        </div>

        {/* Список по категоріях */}
        {CATEGORIES.map(category => {
          const items = ALL_ACHIEVEMENTS.filter(a => a.category === category)
          return (
            <div key={category} className="achieve-category">
              <p className="section-label">{category}</p>
              <div className="achieve-list">
                {items.map(achievement => {
                  const isDone = earned.includes(achievement.key)
                  return (
                    <div
                      key={achievement.key}
                      className={`achieve-card ${isDone ? 'done' : 'locked'}`}
                    >
                      <div className="achieve-card-left">
                        <div className={`achieve-icon-wrap ${isDone ? 'done' : ''}`}>
                          <span className="achieve-icon">
                            {isDone ? '✓' : '🔒'}
                          </span>
                        </div>
                        <div className="achieve-info">
                          <span className="achieve-title">{achievement.title}</span>
                          <span className="achieve-desc">{achievement.desc}</span>
                        </div>
                      </div>
                      <div className={`achieve-bonus ${isDone ? 'done' : ''}`}>
                        {achievement.bonus}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )
        })}

      </div>
    </div>
  )
}