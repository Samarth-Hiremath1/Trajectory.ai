'use client'

import { useAuth } from '@/lib/auth-context'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { ChatInterface } from '@/components/chat/ChatInterface'
import { RoadmapInterface } from '@/components/roadmap/RoadmapInterface'
import { DashboardStats } from '@/components/dashboard/DashboardStats'
import { QuickActions } from '@/components/dashboard/QuickActions'

export default function DashboardPage() {
  const { user, profile, loading, profileLoading, signOut } = useAuth()
  const router = useRouter()
  const [activeTab, setActiveTab] = useState<'chat' | 'roadmap'>('chat')

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
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-gray-900">
                Trajectory.AI
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-700">
                Welcome, {user.email}
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
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <DashboardStats user={user} profile={profile} />
            
            <QuickActions 
              profile={profile} 
              onEditProfile={() => router.push('/profile/edit')}
              onStartOnboarding={() => router.push('/onboarding')}
            />
          </div>
          
          {/* Main AI Features */}
          <div className="bg-white rounded-lg shadow">
            {/* Tab Navigation */}
            <div className="border-b border-gray-200">
              <nav className="flex space-x-8 px-6" aria-label="Tabs">
                <button
                  data-tab="chat"
                  onClick={() => setActiveTab('chat')}
                  className={`py-4 px-1 border-b-2 font-medium text-sm ${
                    activeTab === 'chat'
                      ? 'border-indigo-500 text-indigo-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  AI Career Mentor
                </button>
                <button
                  data-tab="roadmap"
                  onClick={() => setActiveTab('roadmap')}
                  className={`py-4 px-1 border-b-2 font-medium text-sm ${
                    activeTab === 'roadmap'
                      ? 'border-indigo-500 text-indigo-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  Career Roadmap
                </button>
              </nav>
            </div>

            {/* Tab Content */}
            <div className="p-6">
              {activeTab === 'chat' ? (
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 mb-2">
                    AI Career Mentor
                  </h2>
                  <p className="text-gray-600 mb-6">
                    Get personalized career advice based on your profile and resume.
                  </p>
                  <div className="h-96">
                    <ChatInterface />
                  </div>
                </div>
              ) : (
                <RoadmapInterface />
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}