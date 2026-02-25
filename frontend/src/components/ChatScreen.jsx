import { useState } from 'react'
import { sendChatMessage } from '../api'

const MODES = [
  { id: 'friend', icon: '👥', label: 'Друг', desc: 'По-людськи, з гумором' },
  { id: 'psychologist', icon: '🧠', label: 'Психолог', desc: 'Розберемось в собі' },
  { id: 'coach', icon: '🎯', label: 'Коуч', desc: 'Чіткий план дій' },
  { id: 'honest', icon: '😤', label: 'Чесний', desc: 'Правда без прикрас' },
]

export default function ChatScreen({ user, onBack }) {
  const [selectedMode, setSelectedMode] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSend = async () => {
    if (!input.trim() || !selectedMode || loading) return
    const newMessages = [...messages, { role: 'user', content: input }]
    setMessages(newMessages)
    setInput('')
    setLoading(true)
    try {
      const result = await sendChatMessage(user.telegram_id, selectedMode, newMessages)
      setMessages([...newMessages, { role: 'assistant', content: result.response }])
    } catch {
      setMessages([...newMessages, { role: 'assistant', content: 'Щось пішло не так 😔' }])
    } finally {
      setLoading(false)
    }
  }

  if (!selectedMode) {
    return (
      <div className="screen">
        <div className="screen-header">
          <button className="back-btn" onClick={onBack}>←</button>
          <h2>💬 Поговорити</h2>
        </div>
        <div className="screen-content">
          <p className="section-subtitle">З ким хочеш поговорити?</p>
          <div className="mode-list">
            {MODES.map(mode => (
              <button key={mode.id} className="mode-list-btn" onClick={() => setSelectedMode(mode.id)}>
                <span className="mode-list-icon">{mode.icon}</span>
                <div>
                  <span className="mode-list-label">{mode.label}</span>
                  <span className="mode-list-desc">{mode.desc}</span>
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>
    )
  }

  const currentMode = MODES.find(m => m.id === selectedMode)

  return (
    <div className="screen chat-screen">
      <div className="screen-header">
        <button className="back-btn" onClick={() => { setSelectedMode(null); setMessages([]) }}>←</button>
        <h2>{currentMode.icon} {currentMode.label}</h2>
      </div>
      <div className="chat-messages">
        {messages.length === 0 && <div className="chat-placeholder">Розкажи що трапилось 👇</div>}
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>{msg.content}</div>
        ))}
        {loading && (
          <div className="message assistant loading-dots">
            <span>.</span><span>.</span><span>.</span>
          </div>
        )}
      </div>
      <div className="chat-input">
        <input
          type="text"
          placeholder="Напиши..."
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleSend()}
        />
        <button className="chat-send-btn" onClick={handleSend} disabled={loading}>→</button>
      </div>
    </div>
  )
}