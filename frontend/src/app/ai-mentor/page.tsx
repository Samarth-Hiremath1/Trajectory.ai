'use client'

import { useAuth } from '@/lib/auth-context'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { ChatInterface } from '@/components/chat/ChatInterface'
import { LoadingSpinner } from '@/components/ui/LoadingSpinner'

export default function AIMentorPage() {
  const { user, profile, loading, profileLoading, signOut } = useAuth()
  const router = useRouter()
  const [isInitializing, setIsInitializing] = useState(true)

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
    
    // Mark as initialized once auth checks are complete
    if (!loading && !profileLoading) {
      setIsInitializing(false)
    }
  }, [user, profile, loading, profileLoading, router])

  if (loading || profileLoading || isInitializing) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <LoadingSpinner size="lg" />
          <p className="mt-4 text-lg text-gray-600">Loading AI Mentor...</p>
        </div>
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
                  className="text-gray-500 hover:text-gray-700 px-3 py-2 rounded-md text-sm font-medium transition-colors"
                >
                  Dashboard
                </button>
                <button
                  onClick={() => router.push('/roadmaps')}
                  className="text-gray-500 hover:text-gray-700 px-3 py-2 rounded-md text-sm font-medium relative transition-colors"
                >
                  Roadmaps
                </button>
                <button
                  onClick={() => router.push('/ai-mentor')}
                  className="bg-indigo-100 text-indigo-700 px-3 py-2 rounded-md text-sm font-medium"
                >
                  AI Mentor
                </button>
                <button
                  onClick={() => router.push('/daily-dashboard')}
                  className="text-gray-500 hover:text-gray-700 px-3 py-2 rounded-md text-sm font-medium transition-colors"
                >
                  Daily Dashboard
                </button>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-700">
                Welcome, {profile?.name || user?.email?.split('@')[0] || 'User'}
              </span>
              <button
                onClick={signOut}
                className="bg-indigo-600 hover:bg-indigo-700 text-white px-3 py-2 rounded-md text-sm font-medium transition-colors"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="bg-white rounded-lg shadow">
            <div className="p-6 border-b border-gray-200">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                AI Career Mentor
              </h2>
              <p className="text-gray-600">
                Get guidance on your roadmap progress, resume feedback, and personalized career advice. 
                Your AI mentor understands your background and goals to provide tailored support.
              </p>
            </div>
            
            {/* Full-height chat interface */}
            <div className="h-[calc(100vh-280px)] min-h-[500px]">
              <ChatInterface className="h-full" />
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}