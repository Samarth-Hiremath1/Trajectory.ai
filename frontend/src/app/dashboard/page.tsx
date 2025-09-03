'use client'

import { useAuth } from '@/lib/auth-context'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { QuickActions } from '@/components/dashboard/QuickActions'

export default function DashboardPage() {
  const { user, profile, loading, profileLoading, signOut } = useAuth()
  const router = useRouter()
  const [userRoadmaps, setUserRoadmaps] = useState<any[]>([])
  const [roadmapsLoading, setRoadmapsLoading] = useState(true)

  // Fetch user roadmaps
  const fetchUserRoadmaps = async () => {
    if (!user?.id) return
    
    setRoadmapsLoading(true)
    try {
      console.log('Fetching roadmaps for user:', user.id)
      const response = await fetch(`/api/roadmap/user/${user.id}`)
      console.log('Roadmaps API response status:', response.status)
      
      if (response.ok) {
        const data = await response.json()
        console.log('Roadmaps API response data:', data)
        
        if (data.success) {
          console.log('Setting user roadmaps:', data.roadmaps || [])
          setUserRoadmaps(data.roadmaps || [])
        } else {
          console.log('API returned success: false')
        }
      } else {
        console.log('API response not ok:', response.statusText)
      }
    } catch (error) {
      console.error('Error fetching user roadmaps:', error)
    } finally {
      setRoadmapsLoading(false)
    }
  }

  useEffect(() => {
    if (user?.id && !loading && !profileLoading) {
      fetchUserRoadmaps()
    }
  }, [user?.id, loading, profileLoading])

  // Listen for roadmap updates (when user returns from roadmap generation)
  useEffect(() => {
    const handleFocus = () => {
      if (user?.id && !loading && !profileLoading) {
        fetchUserRoadmaps()
      }
    }

    const handleRoadmapCreated = () => {
      console.log('Roadmap created event received, refreshing roadmaps...')
      if (user?.id) {
        // Add a small delay to ensure the backend has saved the roadmap
        setTimeout(() => {
          fetchUserRoadmaps()
        }, 1000)
      }
    }

    window.addEventListener('focus', handleFocus)
    window.addEventListener('roadmapCreated', handleRoadmapCreated)
    
    return () => {
      window.removeEventListener('focus', handleFocus)
      window.removeEventListener('roadmapCreated', handleRoadmapCreated)
    }
  }, [user?.id, loading, profileLoading])

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login')
      return
    }
    // If user is authenticated but doesn't have a profile, redirect to onboarding
    // Wait for both auth loading and profile loading to complete
    if (!loading && !profileLoading && user && !profile) {
      router.push('/onboarding')
      return
    }
  }, [user, profile, loading, profileLoading, router])

  if (loading || profileLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">Loading...</div>
      </div>
    )
  }

  if (!user) {
    return null
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center space-x-8">
              <h1 className="text-xl font-semibold text-gray-900">
                Trajectory.AI
              </h1>
              <div className="flex space-x-4">
                <button
                  onClick={() => router.push('/dashboard')}
                  className="bg-indigo-100 text-indigo-700 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Dashboard
                </button>
                <button
                  onClick={() => router.push('/roadmaps')}
                  className="text-gray-500 hover:text-gray-700 px-3 py-2 rounded-md text-sm font-medium relative"
                >
                  Roadmaps
                </button>
                <button
                  onClick={() => router.push('/ai-mentor')}
                  className="text-gray-500 hover:text-gray-700 px-3 py-2 rounded-md text-sm font-medium"
                >
                  AI Mentor
                </button>
                <button
                  onClick={() => router.push('/daily-dashboard')}
                  className="text-gray-500 hover:text-gray-700 px-3 py-2 rounded-md text-sm font-medium"
                >
                  Daily Dashboard
                </button>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-700">
                Welcome, {profile?.name || 'User'}
              </span>
              <button
                onClick={signOut}
                className="bg-indigo-600 hover:bg-indigo-700 text-white px-3 py-2 rounded-md text-sm font-medium"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="mb-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-3xl font-bold text-gray-900 mb-2">
                    Your Career Journey Hub
                  </h2>
                  <p className="text-lg text-gray-600">
                    Create AI-powered roadmaps, track your progress, and accelerate your career transition with personalized guidance.
                  </p>
                </div>
                <button
                  onClick={fetchUserRoadmaps}
                  disabled={roadmapsLoading}
                  className="px-4 py-2 bg-gray-100 hover:bg-gray-200 disabled:bg-gray-50 text-gray-700 rounded-md text-sm font-medium"
                >
                  {roadmapsLoading ? 'Loading...' : 'Refresh'}
                </button>
              </div>
            </div>
            
            {/* Quick Actions */}
            <QuickActions 
              profile={profile} 
              onEditProfile={() => router.push('/profile/edit')}
              onStartOnboarding={() => router.push('/onboarding')}
            />
            
            {/* Main Roadmap Section - Different states based on user roadmaps */}
            <div className="mt-8">
              {roadmapsLoading ? (
                <div className="bg-gray-50 p-8 rounded-xl border border-gray-200">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto mb-4"></div>
                    <p className="text-gray-600">Loading your roadmaps...</p>
                  </div>
                </div>
              ) : userRoadmaps.length === 0 ? (
                // No roadmaps - Show creation CTA
                <div 
                  onClick={() => router.push('/roadmaps')}
                  className="bg-gradient-to-br from-indigo-50 via-indigo-100 to-purple-100 p-8 rounded-xl border-2 border-indigo-200 cursor-pointer hover:shadow-lg transition-all duration-200 hover:border-indigo-300"
                >
                  <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center mb-4">
                        <div className="p-3 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl mr-4">
                          <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 6.75V15m6-6v8.25m.503 3.498l4.875-2.437c.381-.19.622-.58.622-1.006V4.82c0-.836-.88-1.38-1.628-1.006l-3.869 1.934c-.317.159-.69.159-1.006 0L9.503 3.252a1.125 1.125 0 00-1.006 0L3.622 5.689C3.24 5.88 3 6.27 3 6.695V19.18c0 .836.88 1.38 1.628 1.006l3.869-1.934c-.317-.159.69-.159 1.006 0l4.994 2.497c.317.158.69.158 1.006 0z" />
                          </svg>
                        </div>
                        <div>
                          <h3 className="text-2xl font-bold text-gray-900">Create Your AI Roadmap</h3>
                          <p className="text-indigo-700 font-medium">Your personalized path to career success</p>
                        </div>
                      </div>
                      <p className="text-gray-700 text-lg leading-relaxed mb-4">
                        Get a customized, step-by-step roadmap tailored to your background, timeline, and career goals. 
                        Transform your career transition with AI-generated phases, milestones, and actionable insights.
                      </p>
                      <div className="flex flex-wrap gap-3">
                        <div className="flex items-center text-gray-700">
                          <svg className="h-5 w-5 text-indigo-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                          </svg>
                          Personalized to your situation
                        </div>
                        <div className="flex items-center text-gray-700">
                          <svg className="h-5 w-5 text-indigo-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                          </svg>
                          Actionable milestones
                        </div>
                        <div className="flex items-center text-gray-700">
                          <svg className="h-5 w-5 text-indigo-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                          </svg>
                          Flexible timelines
                        </div>
                      </div>
                    </div>
                    <div className="mt-6 lg:mt-0 lg:ml-8">
                      <div className="bg-white/80 backdrop-blur-sm rounded-lg p-4 shadow-sm">
                        <div className="text-center">
                          <div className="text-2xl font-bold text-indigo-600 mb-1">🚀</div>
                          <div className="text-sm font-semibold text-gray-900">Create Your Roadmap</div>
                          <div className="text-xs text-gray-600">Start your journey</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                // Has roadmaps - Show progress dashboard
                <div className="space-y-6">
                  <div className="bg-gradient-to-br from-green-50 via-emerald-50 to-teal-50 p-6 rounded-xl border border-green-200">
                    <div className="flex items-center justify-between mb-4">
                      <div>
                        <h3 className="text-xl font-bold text-gray-900">Your Career Roadmaps</h3>
                        <p className="text-green-700 font-medium">You have {userRoadmaps.length} active roadmap{userRoadmaps.length !== 1 ? 's' : ''}</p>
                      </div>
                      <div className="text-3xl">✅</div>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {userRoadmaps.slice(0, 2).map((roadmap: any, index: number) => (
                        <div key={roadmap.id} className="bg-white/80 backdrop-blur-sm rounded-lg p-4 border border-green-100">
                          <h4 className="font-semibold text-gray-900 mb-1">{roadmap.title}</h4>
                          <p className="text-sm text-gray-600 mb-2">{roadmap.current_role} → {roadmap.target_role}</p>
                          <div className="flex items-center justify-between">
                            <span className="text-xs text-green-600 font-medium">
                              {roadmap.phases?.length || 0} phases
                            </span>
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                router.push('/roadmaps')
                              }}
                              className="text-xs bg-green-100 hover:bg-green-200 text-green-700 px-2 py-1 rounded font-medium"
                            >
                              View
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                    {userRoadmaps.length > 2 && (
                      <div className="mt-4 text-center">
                        <button
                          onClick={() => router.push('/roadmaps')}
                          className="text-sm text-green-700 hover:text-green-800 font-medium"
                        >
                          View all {userRoadmaps.length} roadmaps →
                        </button>
                      </div>
                    )}
                  </div>
                  
                  <div 
                    onClick={() => router.push('/roadmaps')}
                    className="bg-gradient-to-br from-indigo-50 to-purple-50 p-6 rounded-xl border border-indigo-200 cursor-pointer hover:shadow-md transition-all duration-200"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <h4 className="text-lg font-semibold text-gray-900 mb-1">Create Another Roadmap</h4>
                        <p className="text-gray-600">Explore new career paths or refine your current journey</p>
                      </div>
                      <div className="text-2xl">➕</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
            
            {/* Additional Tools */}
            <div className="mt-8">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div 
                  onClick={() => router.push('/ai-mentor')}
                  className="bg-gradient-to-br from-green-50 to-green-100 p-6 rounded-lg border border-green-200 cursor-pointer hover:shadow-md transition-shadow"
                >
                  <div className="flex items-center mb-3">
                    <div className="p-2 bg-green-600 rounded-lg">
                      <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                      </svg>
                    </div>
                    <h3 className="ml-3 text-lg font-semibold text-gray-900">AI Career Mentor</h3>
                  </div>
                  <p className="text-gray-600 text-sm">
                    Get guidance on your roadmap progress, resume feedback, and personalized career advice. 
                    Your AI mentor understands your background and goals.
                  </p>
                </div>

                <div 
                  onClick={() => router.push('/daily-dashboard')}
                  className="bg-gradient-to-br from-purple-50 to-purple-100 p-6 rounded-lg border border-purple-200 cursor-pointer hover:shadow-md transition-shadow"
                >
                  <div className="flex items-center mb-3">
                    <div className="p-2 bg-purple-600 rounded-lg">
                      <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                    </div>
                    <h3 className="ml-3 text-lg font-semibold text-gray-900">Daily Dashboard</h3>
                  </div>
                  <p className="text-gray-600 text-sm">
                    Track your daily progress, manage roadmap tasks, and stay organized with your career development activities.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}