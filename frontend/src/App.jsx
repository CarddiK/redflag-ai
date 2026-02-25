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
import { createUser } from './api'
import './index.css'

export default function App() {
  const [screen, setScreen] = useState('home')
  const [user, setUser] = useState(null)
  const [lastAnalysis, setLastAnalysis] = useState(null)
  const [prefilledCrush, setPrefilledCrush] = useState(null)

  useEffect(() => {
    initUser()
  }, [])

  const initUser = async () => {
    try {
      const { initData } = retrieveLaunchParams()
      const tgUser = initData?.user
      if (tgUser) {
        const ref = new URLSearchParams(window.location.search).get('ref')
        const userData = await createUser(String(tgUser.id), tgUser.username, ref)
        setUser(userData)
      } else {
        throw new Error('No tg user')
      }
    } catch (e) {
      try {
        const userData = await createUser('123456789', 'test_user', null)
        setUser(userData)
      } catch (err) {
        console.error('Failed to create user:', err)
      }
    }
  }

  const handleAnalyzeCrush = (crushName) => {
    setPrefilledCrush(crushName)
    setScreen('analyze')
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
      return <Home user={user} onNavigate={setScreen} />
  }
}


  return (
    <div className="app">
      {renderScreen()}
    </div>
  )
}

const refreshUser = async () => {
  try {
    const { data } = await axios.get(`${import.meta.env.VITE_API_URL}/users/${user.telegram_id}`)
    setUser(data)
  } catch (e) {
    console.error('Failed to refresh user:', e)
  }
}

useEffect(() => {
  if (!user) return
  
  // Оновлюємо дані коли вікно стає активним
  const handleFocus = () => refreshUser()
  window.addEventListener('focus', handleFocus)
  
  // Оновлюємо через Telegram WebApp події
  window.Telegram?.WebApp?.onEvent('activated', refreshUser)
  
  return () => {
    window.removeEventListener('focus', handleFocus)
  }
}, [user])
