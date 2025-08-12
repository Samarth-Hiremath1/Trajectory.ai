'use client'

import { useEffect, useState } from 'react'

interface DashboardStatsProps {
  user: any
  profile: any
}

interface UserStats {
  totalRoadmaps: number
  activeRoadmaps: number
  completedPhases: number
  totalChatSessions: number
  lastActivity: string | null
}

export function DashboardStats({ user, profile }: DashboardStatsProps) {
  const [stats, setStats] = useState<UserStats>({
    totalRoadmaps: 0,
    activeRoadmaps: 0,
    completedPhases: 0,
    totalChatSessions: 0,
    lastActivity: null
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadUserStats()
  }, [user])

  const loadUserStats = async () => {
    if (!user) return

    try {
      setLoading(true)
      const userId = 'temp_user_123' // TODO: Get from auth context

      // Load roadmap stats
      const roadmapResponse = await fetch(`/api/roadmap/user/${userId}`)
      let roadmapStats = { totalRoadmaps: 0, activeRoadmaps: 0, completedPhases: 0 }
      
      if (roadmapResponse.ok) {
        const roadmapData = await roadmapResponse.json()
        if (roadmapData.success) {
          roadmapStats.totalRoadmaps = roadmapData.roadmaps.length
          roadmapStats.activeRoadmaps = roadmapData.roadmaps.filter((r: any) => r.status === 'active').length
          roadmapStats.completedPhases = roadmapData.roadmaps.reduce((sum: number, r: any) => {
            return sum + Math.floor((r.overall_progress_percentage / 100) * r.phase_count)
          }, 0)
        }
      }

      // Load chat session stats
      const chatResponse = await fetch(`/api/chat/users/${userId}/sessions`)
      let chatStats = { totalChatSessions: 0, lastActivity: null }
      
      if (chatResponse.ok) {
        const chatData = await chatResponse.json()
        chatStats.totalChatSessions = chatData.length
        if (chatData.length > 0) {
          // Find most recent activity
          const mostRecent = chatData.reduce((latest: any, session: any) => {
            return new Date(session.updated_at) > new Date(latest.updated_at) ? session : latest
          })
          chatStats.lastActivity = mostRecent.updated_at
        }
      }

      setStats({
        ...roadmapStats,
        ...chatStats
      })
    } catch (error) {
      console.error('Error loading user stats:', error)
    } finally {
      setLoading(false)
    }
  }

  const formatLastActivity = (dateString: string | null) => {
    if (!dateString) return 'Never'
    
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
    const diffDays = Math.floor(diffHours / 24)

    if (diffHours < 1) return 'Just now'
    if (diffHours < 24) return `${diffHours} hours ago`
    if (diffDays < 7) return `${diffDays} days ago`
    return date.toLocaleDateString()
  }

  if (loading) {
    return (
      <div className="bg-white p-6 rounded-lg shadow">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Dashboard Overview</h3>
        <div className="animate-pulse space-y-3">
          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          <div className="h-4 bg-gray-200 rounded w-2/3"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Dashboard Overview</h3>
      <div className="space-y-4">
        {/* User Info */}
        <div className="space-y-2">
          <p><span className="font-medium">Email:</span> {user.email}</p>
          <p><span className="font-medium">Profile Status:</span> {profile ? 'Complete' : 'Incomplete'}</p>
          {profile && (
            <>
              <p><span className="font-medium">Current Role:</span> {profile.current_role || 'Not specified'}</p>
              <p><span className="font-medium">Target Roles:</span> {profile.target_roles?.length > 0 ? profile.target_roles.join(', ') : 'Not specified'}</p>
            </>
          )}
        </div>



        {/* Progress Indicator */}
        {stats.totalRoadmaps > 0 && (
          <div className="border-t pt-4">
            <h4 className="font-medium text-gray-900 mb-2">Progress</h4>
            <div className="flex items-center space-x-2">
              <div className="flex-1 bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
                  style={{ 
                    width: `${stats.totalRoadmaps > 0 ? (stats.completedPhases / (stats.totalRoadmaps * 4)) * 100 : 0}%` 
                  }}
                ></div>
              </div>
              <span className="text-sm text-gray-600">{stats.completedPhases} phases completed</span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}