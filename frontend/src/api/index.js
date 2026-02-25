import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

export const createUser = async (telegram_id, username, referral_code = null) => {
  const payload = { 
    telegram_id: String(telegram_id), 
    username: username || null
  }
  if (referral_code) payload.referral_code = referral_code
  
  const { data } = await api.post('/users/', payload)
  return data
}

export const analyzeScreenshots = async (telegram_id, files, crush_name = null, context = null) => {
  const formData = new FormData()
  formData.append('telegram_id', telegram_id)
  if (crush_name) formData.append('crush_name', crush_name)
  if (context) formData.append('context', context)
  files.forEach(file => formData.append('files', file))

  const { data } = await axios.post(`${API_URL}/analyze/`, formData)
  return data
}

export const getCrushes = async (telegram_id) => {
  const { data } = await api.get(`/analyze/crushes/${telegram_id}`)
  return data
}

export const compareCrushes = async (telegram_id, crush1_id, crush2_id) => {
  const formData = new FormData()
  formData.append('telegram_id', telegram_id)
  formData.append('crush1_id', crush1_id)
  formData.append('crush2_id', crush2_id)

  const { data } = await axios.post(`${API_URL}/analyze/compare`, formData)
  return data
}

export const generateResponse = async (telegram_id, analysis_id, mode) => {
  const { data } = await api.post('/generate/response', { 
    telegram_id, 
    analysis_id, 
    mode 
  })
  return data
}

export const sendChatMessage = async (telegram_id, mode, messages) => {
  const { data } = await api.post('/generate/chat', { 
    telegram_id, 
    mode, 
    messages 
  })
  return data
}

export const getUser = async (telegram_id) => {
  const { data } = await api.get(`/users/${telegram_id}`)
  return data
}

export const analyzeOutfit = async (telegram_id, file, destination) => {
  const formData = new FormData()
  formData.append('telegram_id', telegram_id)
  formData.append('destination', destination)
  formData.append('file', file)

  const { data } = await axios.post(`${API_URL}/analyze/outfit`, formData)
  return data
}
