import { useState, useEffect } from 'react'
import { retrieveLaunchParams } from '@tma.js/sdk'
import Home from './pages/Home'
import AnalyzeScreen from './components/AnalyzeScreen'
import GenerateScreen from './components/GenerateScreen'
import ChatScreen from './components/ChatScreen'
import CrushesScreen from './components/CrushesScreen'
import OutfitScreen from './components/OutfitScreen'
import ReferralScreen from './components/ReferralScreen'
import PremiumScreen from './components/PremiumScreen'
import { createUser, getUser } from './api'
import './index.css'

export default function App() {
  const [screen, setScreen] = useState('home')
  const [user, setUser] = useState(null)
  const [lastAnalysis, setLastAnalysis] = useState(null)
  const [prefilledCrush, setPrefilledCrush] = useState(null)
  const [upgradeMessage, setUpgradeMessage] = useState(null)

  useEffect(() => {
    initUser()
  }, [])

  useEffect(() => {
    if (!user) return
    const handleFocus = () => refreshUser()
    window.addEventListener('focus', handleFocus)
    window.Telegram?.WebApp?.onEvent('activated', refreshUser)
    return () => window.removeEventListener('focus', handleFocus)
  }, [user])

  useEffect(() => {
    const handler = (e) => setUpgradeMessage(e.detail)
    window.addEventListener('upgrade-required', handler)
    return () => window.removeEventListener('upgrade-required', handler)
  }, [])

  const initUser = async () => {
    try {
      const tg = window.Telegram?.WebApp
      let telegramId = null
      let username = null

      if (tg && tg.initDataUnsafe?.user) {
        telegramId = String(tg.initDataUnsafe.user.id)
        username = tg.initDataUnsafe.user.username
      } else {
        try {
          const { initData } = retrieveLaunchParams()
          if (initData?.user) {
            telegramId = String(initData.user.id)
            username = initData.user.username
          }
        } catch {}
      }

      if (telegramId) {
        const ref = new URLSearchParams(window.location.search).get('ref')
        const userData = await createUser(telegramId, username, ref)
        setUser(userData)
      } else {
        const userData = await createUser('123456789', 'test_user', null)
        setUser(userData)
      }
    } catch (e) {
      console.error('initUser error:', e)
      try {
        const userData = await createUser('123456789', 'test_user', null)
        setUser(userData)
      } catch (err) {
        console.error('Failed to create user:', err)
      }
    }
  }

  const refreshUser = async () => {
    if (!user) return
    try {
      const data = await getUser(user.telegram_id)
      setUser(data)
    } catch (e) {
      console.error('Failed to refresh user:', e)
    }
  }

  const handleAnalyzeCrush = (crushName) => {
    setPrefilledCrush(crushName)
    setScreen('analyze')
  }

  // Підраховуємо скільки аналізів залишилось
  const getAnalysesLeft = () => {
    if (!user) return 0
    if (user.is_premium) {
      // Love Pro — 50 на місяць, VIP — безліміт
      // Поки що просто показуємо залишок якщо є або ∞
      const used = user.free_analyses_used || 0
      const left = 50 - used
      return left > 0 ? left : '∞'
    }
    const limit = 3 + (user.bonus_analyses || 0)
    const left = limit - (user.free_analyses_used || 0)
    return Math.max(0, left)
  }

  if (!user) {
    return (
      <div className="loading">
        <div className="spinner" />
        <p>Завантаження...</p>
      </div>
    )
  }

  const renderScreen = () => {
    switch (screen) {
      case 'analyze':
        return (
          <AnalyzeScreen
            user={user}
            prefilledCrush={prefilledCrush}
            onBack={() => { setScreen('home'); setPrefilledCrush(null) }}
            onAnalyzed={(result) => {
              setLastAnalysis(result)
              setPrefilledCrush(null)
              refreshUser()
              setScreen('generate')
            }}
          />
        )
      case 'generate':
        return <GenerateScreen user={user} analysis={lastAnalysis} onBack={() => setScreen('analyze')} />
      case 'chat':
        return <ChatScreen user={user} onBack={() => setScreen('home')} />
      case 'crushes':
        return <CrushesScreen user={user} onBack={() => setScreen('home')} onAnalyzeCrush={handleAnalyzeCrush} />
      case 'outfit':
        return <OutfitScreen user={user} onBack={() => setScreen('home')} />
      case 'referral':
        return <ReferralScreen user={user} onBack={() => setScreen('home')} />
      case 'premium':
        return <PremiumScreen user={user} onBack={() => setScreen('home')} />
      default:
        return <Home user={user} onNavigate={setScreen} analysesLeft={getAnalysesLeft()} />
    }
  }

  return (
    <div className="app">
      {renderScreen()}

      {upgradeMessage && (
        <div className="upgrade-overlay" onClick={() => setUpgradeMessage(null)}>
          <div className="upgrade-modal" onClick={e => e.stopPropagation()}>
            <div className="upgrade-icon">💎</div>
            <h3 className="upgrade-title">Потрібен апгрейд</h3>
            <p className="upgrade-text">{upgradeMessage}</p>
            <button className="action-btn" onClick={() => {
              setUpgradeMessage(null)
              setScreen('premium')
            }}>
              Переглянути плани
            </button>
            <button className="upgrade-close" onClick={() => setUpgradeMessage(null)}>
              Закрити
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
