'use client'

import { useState, useEffect, useCallback } from 'react'
import { TrophyIcon, ChartBarIcon } from '@heroicons/react/24/outline'
import { Roadmap } from '@/types/roadmap'

interface ProgressData {
  totalMilestones: number
  completedMilestones: number
  totalPhases: number
  completedPhases: number
  overallProgress: number
  currentStreak: number
  longestStreak: number
  weeklyProgress: number[]
  recentAchievements: Achievement[]
}

interface Achievement {
  id: string
  title: string
  description: string
  type: 'milestone' | 'phase' | 'streak' | 'skill'
  date: Date
  roadmapTitle?: string
  icon: string
}

interface ProgressTrackerProps {
  roadmaps: Roadmap[]
  userId: string
}

export function ProgressTracker({ roadmaps, userId }: ProgressTrackerProps) {
  const [progressData, setProgressData] = useState<ProgressData>({
    totalMilestones: 0,
    completedMilestones: 0,
    totalPhases: 0,
    completedPhases: 0,
    overallProgress: 0,
    currentStreak: 0,
    longestStreak: 0,
    weeklyProgress: [0, 0, 0, 0, 0, 0, 0],
    recentAchievements: []
  })
  
  const [selectedTimeframe, setSelectedTimeframe] = useState<'week' | 'month' | 'quarter'>('week')
  const [showAchievements, setShowAchievements] = useState(false)

  const calculateProgress = useCallback(() => {
    let totalMilestones = 0
    let completedMilestones = 0
    let totalPhases = 0
    let completedPhases = 0
    const achievements: Achievement[] = []

    roadmaps.forEach(roadmap => {
      if (roadmap.status === 'active' || roadmap.status === 'completed') {
        roadmap.phases.forEach(phase => {
          totalPhases++
          if (phase.is_completed) {
            completedPhases++
            achievements.push({
              id: `phase-${roadmap.id}-${phase.phase_number}`,
              title: `Completed ${phase.title}`,
              description: `Finished phase ${phase.phase_number} of ${roadmap.title}`,
              type: 'phase',
              date: phase.completed_date || new Date(),
              roadmapTitle: roadmap.title,
              icon: '🎯'
            })
          }

          phase.milestones.forEach(milestone => {
            totalMilestones++
            if (milestone.is_completed) {
              completedMilestones++
              achievements.push({
                id: `milestone-${roadmap.id}-${phase.phase_number}-${milestone.title}`,
                title: milestone.title,
                description: `Milestone completed in ${phase.title}`,
                type: 'milestone',
                date: milestone.completed_date || new Date(),
                roadmapTitle: roadmap.title,
                icon: '✅'
              })
            }
          })
        })
      }
    })

    // Calculate overall progress
    const overallProgress = totalMilestones > 0 ? (completedMilestones / totalMilestones) * 100 : 0

    // Calculate streaks (simplified - in real app would use actual completion dates)
    const currentStreak = calculateCurrentStreak(achievements)
    const longestStreak = calculateLongestStreak(achievements)

    // Generate weekly progress (mock data - in real app would use actual data)
    const weeklyProgress = generateWeeklyProgress(achievements)

    // Sort achievements by date (most recent first) and take top 10
    const recentAchievements = achievements
      .sort((a, b) => b.date.getTime() - a.date.getTime())
      .slice(0, 10)

    setProgressData({
      totalMilestones,
      completedMilestones,
      totalPhases,
      completedPhases,
      overallProgress,
      currentStreak,
      longestStreak,
      weeklyProgress,
      recentAchievements
    })
  }, [roadmaps])

  useEffect(() => {
    calculateProgress()
  }, [calculateProgress])

  const calculateCurrentStreak = (achievements: Achievement[]): number => {
    // Simplified streak calculation
    const today = new Date()
    let streak = 0
    let currentDate = new Date(today)

    for (let i = 0; i < 30; i++) {
      const hasAchievement = achievements.some(achievement => 
        achievement.date.toDateString() === currentDate.toDateString()
      )
      
      if (hasAchievement) {
        streak++
      } else if (streak > 0) {
        break
      }
      
      currentDate.setDate(currentDate.getDate() - 1)
    }

    return streak
  }

  const calculateLongestStreak = (achievements: Achievement[]): number => {
    // Simplified longest streak calculation
    return Math.max(progressData.currentStreak, 5) // Mock data
  }

  const generateWeeklyProgress = (achievements: Achievement[]): number[] => {
    const weekProgress = [0, 0, 0, 0, 0, 0, 0]
    const today = new Date()
    
    for (let i = 0; i < 7; i++) {
      const date = new Date(today)
      date.setDate(today.getDate() - i)
      
      const dayAchievements = achievements.filter(achievement =>
        achievement.date.toDateString() === date.toDateString()
      ).length
      
      weekProgress[6 - i] = dayAchievements
    }
    
    return weekProgress
  }

  const getProgressColor = (percentage: number) => {
    if (percentage >= 80) return 'text-green-600 bg-green-100'
    if (percentage >= 60) return 'text-blue-600 bg-blue-100'
    if (percentage >= 40) return 'text-yellow-600 bg-yellow-100'
    return 'text-red-600 bg-red-100'
  }

  const getStreakMessage = (streak: number) => {
    if (streak === 0) return "Start your streak today!"
    if (streak === 1) return "Great start! Keep it going!"
    if (streak < 7) return `${streak} days strong! 💪`
    if (streak < 30) return `Amazing ${streak}-day streak! 🔥`
    return `Incredible ${streak}-day streak! You're unstoppable! 🚀`
  }

  const formatDate = (date: Date) => {
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

    if (diffDays === 0) return 'Today'
    if (diffDays === 1) return 'Yesterday'
    if (diffDays < 7) return `${diffDays} days ago`
    return date.toLocaleDateString()
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Progress Tracking</h3>
        <div className="flex items-center space-x-2">
          <select
            value={selectedTimeframe}
            onChange={(e) => setSelectedTimeframe(e.target.value as any)}
            className="text-sm border border-gray-300 rounded px-2 py-1"
          >
            <option value="week">This Week</option>
            <option value="month">This Month</option>
            <option value="quarter">This Quarter</option>
          </select>
          <button
            onClick={() => setShowAchievements(!showAchievements)}
            className="text-sm bg-indigo-100 hover:bg-indigo-200 text-indigo-700 px-3 py-1 rounded"
          >
            {showAchievements ? 'Hide' : 'Show'} Achievements
          </button>
        </div>
      </div>

      {/* Progress Overview */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="text-center p-4 bg-gray-50 rounded-lg">
          <div className="text-2xl font-bold text-gray-900">{progressData.completedMilestones}</div>
          <div className="text-sm text-gray-600">Milestones</div>
          <div className="text-xs text-gray-500">of {progressData.totalMilestones}</div>
        </div>
        
        <div className="text-center p-4 bg-gray-50 rounded-lg">
          <div className="text-2xl font-bold text-blue-600">{progressData.completedPhases}</div>
          <div className="text-sm text-gray-600">Phases</div>
          <div className="text-xs text-gray-500">of {progressData.totalPhases}</div>
        </div>
        
        <div className="text-center p-4 bg-gray-50 rounded-lg">
          <div className="text-2xl font-bold text-green-600">{Math.round(progressData.overallProgress)}%</div>
          <div className="text-sm text-gray-600">Complete</div>
          <div className="text-xs text-gray-500">Overall</div>
        </div>
        
        <div className="text-center p-4 bg-gray-50 rounded-lg">
          <div className="text-2xl font-bold text-orange-600">{progressData.currentStreak}</div>
          <div className="text-sm text-gray-600">Day Streak</div>
          <div className="text-xs text-gray-500">Current</div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">Overall Progress</span>
          <span className="text-sm text-gray-600">{Math.round(progressData.overallProgress)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div
            className="bg-gradient-to-r from-blue-500 to-green-500 h-3 rounded-full transition-all duration-500"
            style={{ width: `${progressData.overallProgress}%` }}
          ></div>
        </div>
      </div>

      {/* Streak Information */}
      <div className="bg-gradient-to-r from-orange-50 to-red-50 rounded-lg p-4 mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h4 className="font-medium text-gray-900 mb-1">Daily Streak</h4>
            <p className="text-sm text-gray-600">{getStreakMessage(progressData.currentStreak)}</p>
            <p className="text-xs text-gray-500 mt-1">
              Longest streak: {progressData.longestStreak} days
            </p>
          </div>
          <div className="text-4xl">
            {progressData.currentStreak > 0 ? '🔥' : '💤'}
          </div>
        </div>
      </div>

      {/* Weekly Activity Chart */}
      <div className="mb-6">
        <h4 className="font-medium text-gray-900 mb-3">Weekly Activity</h4>
        <div className="flex items-end justify-between space-x-1 h-20">
          {progressData.weeklyProgress.map((count, index) => {
            const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
            const maxCount = Math.max(...progressData.weeklyProgress, 1)
            const height = (count / maxCount) * 100
            
            return (
              <div key={index} className="flex-1 flex flex-col items-center">
                <div
                  className="w-full bg-indigo-500 rounded-t transition-all duration-300"
                  style={{ height: `${height}%`, minHeight: count > 0 ? '8px' : '2px' }}
                  title={`${count} achievements on ${days[index]}`}
                ></div>
                <div className="text-xs text-gray-500 mt-1">{days[index]}</div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Recent Achievements */}
      {showAchievements && (
        <div>
          <h4 className="font-medium text-gray-900 mb-3 flex items-center">
            <TrophyIcon className="w-5 h-5 mr-2 text-yellow-500" />
            Recent Achievements
          </h4>
          <div className="space-y-3 max-h-64 overflow-y-auto">
            {progressData.recentAchievements.map(achievement => (
              <div
                key={achievement.id}
                className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg"
              >
                <div className="text-2xl">{achievement.icon}</div>
                <div className="flex-1">
                  <h5 className="font-medium text-gray-900">{achievement.title}</h5>
                  <p className="text-sm text-gray-600">{achievement.description}</p>
                  <div className="flex items-center space-x-2 mt-1">
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      achievement.type === 'milestone' ? 'bg-green-100 text-green-800' :
                      achievement.type === 'phase' ? 'bg-blue-100 text-blue-800' :
                      'bg-purple-100 text-purple-800'
                    }`}>
                      {achievement.type}
                    </span>
                    <span className="text-xs text-gray-500">{formatDate(achievement.date)}</span>
                  </div>
                </div>
              </div>
            ))}
            
            {progressData.recentAchievements.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                <TrophyIcon className="w-12 h-12 mx-auto mb-2 text-gray-300" />
                <p>No achievements yet. Complete your first milestone to get started!</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Motivational Message */}
      {progressData.overallProgress > 0 && (
        <div className="mt-6 p-4 bg-gradient-to-r from-green-50 to-blue-50 rounded-lg">
          <div className="flex items-center space-x-2">
            <ChartBarIcon className="w-5 h-5 text-green-600" />
            <p className="text-sm text-gray-700">
              {progressData.overallProgress < 25 ? "Great start! Every expert was once a beginner. Keep pushing forward! 🌱" :
               progressData.overallProgress < 50 ? "You're making solid progress! Stay consistent and you'll reach your goals! 📈" :
               progressData.overallProgress < 75 ? "Excellent work! You're more than halfway there. The finish line is in sight! 🎯" :
               progressData.overallProgress < 100 ? "Outstanding progress! You're so close to achieving your goals! 🚀" :
               "Congratulations! You've completed your career roadmap. Time to set new goals! 🎉"}
            </p>
          </div>
        </div>
      )}
    </div>
  )
}