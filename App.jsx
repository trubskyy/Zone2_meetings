import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Progress } from '@/components/ui/progress.jsx'
import { 
  Heart, 
  Users, 
  Calendar, 
  Activity, 
  Mic, 
  Play, 
  Pause,
  BarChart3,
  User,
  Home,
  Video,
  Settings,
  RefreshCw
} from 'lucide-react'
import './App.css'

const API_BASE_URL = 'http://localhost:5000/api'

function App() {
  const [currentView, setCurrentView] = useState('dashboard')
  const [isInMeeting, setIsInMeeting] = useState(false)
  const [currentMeeting, setCurrentMeeting] = useState(null)
  const [meetings, setMeetings] = useState([])
  const [participants, setParticipants] = useState([])
  const [biometrics, setBiometrics] = useState({ heart_rate: 142, zone: 'Zone 2' })
  const [isRecording, setIsRecording] = useState(false)
  const [isPodcastPlaying, setIsPodcastPlaying] = useState(false)
  const [loading, setLoading] = useState(false)

  // Fetch meetings from backend
  const fetchMeetings = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${API_BASE_URL}/meetings`)
      const data = await response.json()
      if (data.success) {
        setMeetings(data.meetings)
      }
    } catch (error) {
      console.error('Error fetching meetings:', error)
    } finally {
      setLoading(false)
    }
  }

  // Fetch current biometrics
  const fetchBiometrics = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/biometrics/current`)
      const data = await response.json()
      if (data.success) {
        setBiometrics(data.data)
      }
    } catch (error) {
      console.error('Error fetching biometrics:', error)
    }
  }

  // Join meeting
  const joinMeeting = async (meetingId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/meetings/${meetingId}/join`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      })
      const data = await response.json()
      if (data.success) {
        setCurrentMeeting(data.meeting)
        setParticipants(data.participants)
        setIsInMeeting(true)
        setCurrentView('meeting')
      }
    } catch (error) {
      console.error('Error joining meeting:', error)
    }
  }

  // Leave meeting
  const leaveMeeting = async () => {
    if (!currentMeeting) return
    
    try {
      await fetch(`${API_BASE_URL}/meetings/${currentMeeting.id}/leave`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      })
      setIsInMeeting(false)
      setCurrentMeeting(null)
      setParticipants([])
      setCurrentView('dashboard')
    } catch (error) {
      console.error('Error leaving meeting:', error)
    }
  }

  // Save voice note
  const saveVoiceNote = async (transcript) => {
    if (!currentMeeting) return
    
    try {
      await fetch(`${API_BASE_URL}/meetings/${currentMeeting.id}/voice-note`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ transcript, duration: 30 })
      })
    } catch (error) {
      console.error('Error saving voice note:', error)
    }
  }

  // Load initial data
  useEffect(() => {
    fetchMeetings()
    fetchBiometrics()
    
    // Set up biometrics polling when in meeting
    let interval
    if (isInMeeting) {
      interval = setInterval(fetchBiometrics, 5000) // Update every 5 seconds
    }
    
    return () => {
      if (interval) clearInterval(interval)
    }
  }, [isInMeeting])

  const getZoneColor = (zone) => {
    switch(zone) {
      case "Zone 1": return "bg-blue-500"
      case "Zone 2": return "bg-green-500"
      case "Zone 3": return "bg-yellow-500"
      case "Zone 4": return "bg-orange-500"
      case "Zone 5": return "bg-red-500"
      default: return "bg-gray-500"
    }
  }

  const getHeartRateZone = (hr) => {
    if (hr < 120) return "Zone 1"
    if (hr < 150) return "Zone 2"
    if (hr < 170) return "Zone 3"
    if (hr < 185) return "Zone 4"
    return "Zone 5"
  }

  const currentZone = biometrics.zone || getHeartRateZone(biometrics.heart_rate)
  const zoneProgress = ((biometrics.heart_rate - 120) / (150 - 120)) * 100

  const Dashboard = () => (
    <div className="p-6 max-w-md mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Activity className="h-8 w-8 text-green-600" />
          <h1 className="text-2xl font-bold">Zone 2 Meeting</h1>
        </div>
        <div className="flex gap-2">
          <Button 
            variant="outline" 
            size="icon"
            onClick={fetchMeetings}
            disabled={loading}
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </Button>
          <Button variant="outline" size="icon">
            <Settings className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            Upcoming Meetings
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {loading ? (
            <div className="text-center text-muted-foreground">Loading meetings...</div>
          ) : meetings.length === 0 ? (
            <div className="text-center text-muted-foreground">No meetings found</div>
          ) : (
            meetings.map((meeting) => (
              <div key={meeting.id} className="flex items-center justify-between p-3 border rounded-lg">
                <div>
                  <h3 className="font-medium">{meeting.title}</h3>
                  <div className="flex items-center gap-1 text-sm text-muted-foreground">
                    <Users className="h-3 w-3" />
                    {meeting.participants} participants
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-medium">{meeting.time}</div>
                  <Button 
                    size="sm" 
                    onClick={() => joinMeeting(meeting.id)}
                    className="mt-1"
                  >
                    Join
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    className="mt-1 ml-2"
                    onClick={() => {
                      navigator.clipboard.writeText(`/join ${meeting.id}`)
                      alert('Copied Telegram join command to clipboard — open your bot chat and paste it.')
                    }}
                  >
                    Join via Telegram
                  </Button>
                </div>
              </div>
            ))
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Heart className="h-5 w-5" />
            Current Zone
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center">
            <div className="relative w-32 h-32 mx-auto mb-4">
              <div className="absolute inset-0 rounded-full border-8 border-gray-200"></div>
              <div 
                className={`absolute inset-0 rounded-full border-8 border-t-green-500 border-r-green-500 ${zoneProgress > 50 ? 'border-b-green-500' : ''} ${zoneProgress > 75 ? 'border-l-green-500' : ''}`}
                style={{ transform: `rotate(${(Math.max(0, Math.min(100, zoneProgress)) / 100) * 360}deg)` }}
              ></div>
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                  <div className="text-2xl font-bold">{biometrics.heart_rate}</div>
                  <div className="text-sm text-muted-foreground">BPM</div>
                </div>
              </div>
            </div>
            <Badge className={`${getZoneColor(currentZone)} text-white`}>
              {currentZone}
            </Badge>
            {biometrics.speed && (
              <div className="mt-2 text-sm text-muted-foreground">
                Speed: {biometrics.speed} km/h
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const MeetingInterface = () => (
    <div className="p-6 max-w-md mx-auto">
      <div className="flex items-center justify-between mb-6">
        <Button 
          variant="outline" 
          onClick={() => {
            setCurrentView('dashboard')
            setIsInMeeting(false)
          }}
        >
          ← Back
        </Button>
        <div className="text-center">
          <h2 className="font-bold">{currentMeeting?.title || 'Meeting'}</h2>
          <div className="text-sm text-muted-foreground">
            15:32 • {participants.length}/{(currentMeeting?.participants || 0) + 1} joined
          </div>
        </div>
        <Button variant="destructive" size="sm" onClick={leaveMeeting}>
          Leave
        </Button>
      </div>

      <div className="grid grid-cols-2 gap-3 mb-6">
        {participants.map((participant, index) => (
          <Card key={index} className="p-3">
            <div className="text-center">
              <div className="w-12 h-12 bg-gray-200 rounded-full mx-auto mb-2 flex items-center justify-center">
                <User className="h-6 w-6 text-gray-500" />
              </div>
              <h3 className="font-medium text-sm">{participant.name}</h3>
              <div className="text-xs text-muted-foreground mb-1">{participant.heartRate} BPM</div>
              <Badge 
                size="sm" 
                className={`${getZoneColor(participant.zone)} text-white text-xs`}
              >
                {participant.zone}
              </Badge>
            </div>
          </Card>
        ))}
      </div>

      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-medium">Podcast: The Tim Ferriss Show</h3>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsPodcastPlaying(!isPodcastPlaying)}
            >
              {isPodcastPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
            </Button>
          </div>
          <Progress value={35} className="mb-2" />
          <div className="text-xs text-muted-foreground">12:45 / 36:20</div>
        </CardContent>
      </Card>

      <div className="flex items-center justify-center gap-4">
        <Button
          size="lg"
          variant={isRecording ? "destructive" : "default"}
          className="rounded-full w-16 h-16"
          onClick={() => {
            setIsRecording(!isRecording)
            if (!isRecording) {
              // Simulate voice note recording
              setTimeout(() => {
                setIsRecording(false)
                saveVoiceNote("This is a sample voice note from the meeting.")
              }, 3000)
            }
          }}
        >
          <Mic className="h-6 w-6" />
        </Button>
        <div className="text-center">
          <div className="text-2xl font-bold">{biometrics.heart_rate}</div>
          <div className="text-sm text-muted-foreground">BPM</div>
          <Badge className={`${getZoneColor(currentZone)} text-white mt-1`}>
            {currentZone}
          </Badge>
          {biometrics.speed && (
            <div className="text-xs text-muted-foreground mt-1">
              {biometrics.speed} km/h
            </div>
          )}
        </div>
      </div>

      {isRecording && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center gap-2 text-red-700">
            <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
            Recording voice note...
          </div>
        </div>
      )}
    </div>
  )

  const BottomNavigation = () => (
    <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 px-6 py-3">
      <div className="flex justify-around max-w-md mx-auto">
        <Button
          variant={currentView === 'dashboard' ? 'default' : 'ghost'}
          size="sm"
          onClick={() => setCurrentView('dashboard')}
          className="flex flex-col items-center gap-1"
        >
          <Home className="h-4 w-4" />
          <span className="text-xs">Dashboard</span>
        </Button>
        <Button
          variant={currentView === 'meeting' ? 'default' : 'ghost'}
          size="sm"
          onClick={() => setCurrentView('meeting')}
          className="flex flex-col items-center gap-1"
        >
          <Video className="h-4 w-4" />
          <span className="text-xs">Meetings</span>
        </Button>
        <Button
          variant={currentView === 'analytics' ? 'default' : 'ghost'}
          size="sm"
          onClick={() => setCurrentView('analytics')}
          className="flex flex-col items-center gap-1"
        >
          <BarChart3 className="h-4 w-4" />
          <span className="text-xs">Analytics</span>
        </Button>
        <Button
          variant={currentView === 'profile' ? 'default' : 'ghost'}
          size="sm"
          onClick={() => setCurrentView('profile')}
          className="flex flex-col items-center gap-1"
        >
          <User className="h-4 w-4" />
          <span className="text-xs">Profile</span>
        </Button>
      </div>
    </div>
  )

  return (
    <div className="min-h-screen bg-gray-50 pb-20">
      {currentView === 'dashboard' && <Dashboard />}
      {currentView === 'meeting' && <MeetingInterface />}
      {currentView === 'analytics' && (
        <div className="p-6 max-w-md mx-auto">
          <h1 className="text-2xl font-bold mb-6">Analytics</h1>
          <Card>
            <CardContent className="p-6">
              <div className="text-center text-muted-foreground">
                Analytics dashboard coming soon...
                <br />
                <small className="text-xs">Will show Zone 2 time, calories burned, meeting productivity metrics</small>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
      {currentView === 'profile' && (
        <div className="p-6 max-w-md mx-auto">
          <h1 className="text-2xl font-bold mb-6">Profile</h1>
          <Card>
            <CardContent className="p-6">
              <div className="text-center text-muted-foreground">
                Profile settings coming soon...
                <br />
                <small className="text-xs">Will include wearable device connections, Zone 2 targets, preferences</small>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
      <BottomNavigation />
    </div>
  )
}

export default App

