import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'

export default function TOTPSetup() {
  const navigate = useNavigate()
  const [qrCode, setQrCode] = useState('')
  const [code, setCode] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const tempToken = localStorage.getItem('temp_token')

  useEffect(() => {
    if (!tempToken) {
      navigate('/login')
      return
    }

    const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://100.30.119.38'

    // Fetch TOTP QR code
    axios.get(`${API_BASE}/api/v1/auth/totp-setup`, {
      headers: { Authorization: `Bearer ${tempToken}` }
    })
      .then(res => setQrCode(res.data.qr_code))
      .catch(err => setError(err.response?.data?.detail || 'Failed to load TOTP setup'))
  }, [tempToken, navigate])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://100.30.119.38'

      const response = await axios.post(
        `${API_BASE}/api/v1/auth/totp`,
        { code },
        { headers: { Authorization: `Bearer ${tempToken}` } }
      )

      localStorage.removeItem('temp_token')
      localStorage.setItem('access_token', response.data.access_token)
      localStorage.setItem('refresh_token', response.data.refresh_token)
      navigate('/')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid code')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-8 shadow-xl">
          <h2 className="text-2xl font-bold text-slate-100 mb-6">Two-Factor Authentication</h2>

          {qrCode && (
            <div className="mb-6">
              <p className="text-slate-300 text-sm mb-4">
                Scan this QR code with Google Authenticator or Authy:
              </p>
              <div className="bg-white p-4 rounded-lg">
                <img src={qrCode} alt="TOTP QR Code" className="w-full" />
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="code" className="block text-sm font-medium text-slate-300 mb-1">
                Enter 6-digit code
              </label>
              <input
                id="code"
                type="text"
                value={code}
                onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                className="w-full px-4 py-2 bg-slate-900 border border-slate-600 rounded-md text-slate-100 text-center text-2xl tracking-widest placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="000000"
                required
                maxLength={6}
                pattern="\d{6}"
              />
            </div>

            {error && (
              <div className="bg-red-500/10 border border-red-500/50 rounded-md p-3">
                <p className="text-red-400 text-sm">{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={loading || code.length !== 6}
              className="w-full bg-blue-500 hover:bg-blue-600 disabled:bg-slate-600 disabled:cursor-not-allowed text-white font-medium py-2 px-4 rounded-md transition-colors"
            >
              {loading ? 'Verifying...' : 'Verify & Login'}
            </button>
          </form>

          <button
            onClick={() => navigate('/login')}
            className="w-full mt-4 text-slate-400 hover:text-slate-300 text-sm"
          >
            ← Back to login
          </button>
        </div>
      </div>
    </div>
  )
}
