'use client'

import { useAuth } from '@/lib/auth-context'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'
import Link from 'next/link'

export default function Home() {
  const { user, profile, loading, profileLoading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    console.log('🏠 Main page redirect logic:', {
      loading,
      profileLoading,
      user: user ? { id: user.id, email: user.email } : null,
      profile: profile ? 'EXISTS' : 'NULL'
    })
    
    if (!loading && !profileLoading && user) {
      // If user has a profile, go to dashboard
      if (profile) {
        console.log('➡️ Redirecting to dashboard (user has profile)')
        router.push('/dashboard')
      } else {
        // If user doesn't have a profile, go to onboarding
        console.log('➡️ Redirecting to onboarding (user has no profile)')
        router.push('/onboarding')
      }
    }
  }, [user, profile, loading, profileLoading, router])

  if (loading || (user && profileLoading)) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">Loading...</div>
      </div>
    )
  }

  if (user) {
    return null // Will redirect to dashboard or onboarding
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col items-center justify-center min-h-screen py-12">
          <div className="text-center">
            <h1 className="text-4xl font-bold text-gray-900 sm:text-6xl">
              Trajectory.AI
            </h1>
            <p className="mt-6 text-lg text-gray-600 max-w-3xl">
              Your AI-powered career navigation platform. Get personalized feedback, 
              roadmaps, and mentoring to reach your target career goals.
            </p>
            <div className="mt-10 flex items-center justify-center gap-x-6">
              <Link
                href="/signup"
                className="rounded-md bg-indigo-600 px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
              >
                Get started
              </Link>
              <Link
                href="/login"
                className="text-sm font-semibold leading-6 text-gray-900 hover:text-indigo-600"
              >
                Sign in <span aria-hidden="true">→</span>
              </Link>
            </div>
          </div>
          
          <div className="mt-16 grid grid-cols-1 gap-8 sm:grid-cols-3 max-w-4xl">
            <div className="text-center">
              <div className="mx-auto h-12 w-12 bg-indigo-100 rounded-lg flex items-center justify-center">
                <svg className="h-6 w-6 text-indigo-600" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
                </svg>
              </div>
              <h3 className="mt-4 text-lg font-semibold text-gray-900">AI Mentoring</h3>
              <p className="mt-2 text-sm text-gray-600">
                Chat with an AI mentor that understands your background and career goals
              </p>
            </div>
            
            <div className="text-center">
              <div className="mx-auto h-12 w-12 bg-indigo-100 rounded-lg flex items-center justify-center">
                <svg className="h-6 w-6 text-indigo-600" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 6.75V15m6-6v8.25m.503 3.498l4.875-2.437c.381-.19.622-.58.622-1.006V4.82c0-.836-.88-1.38-1.628-1.006l-3.869 1.934c-.317.159-.69.159-1.006 0L9.503 3.252a1.125 1.125 0 00-1.006 0L3.622 5.689C3.24 5.88 3 6.27 3 6.695V19.18c0 .836.88 1.38 1.628 1.006l3.869-1.934c.317-.159.69-.159 1.006 0l4.994 2.497c.317.158.69.158 1.006 0z" />
                </svg>
              </div>
              <h3 className="mt-4 text-lg font-semibold text-gray-900">Career Roadmaps</h3>
              <p className="mt-2 text-sm text-gray-600">
                Get personalized roadmaps for your target roles with skills and timelines
              </p>
            </div>
            
            <div className="text-center">
              <div className="mx-auto h-12 w-12 bg-indigo-100 rounded-lg flex items-center justify-center">
                <svg className="h-6 w-6 text-indigo-600" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0-1.125-.504-1.125-1.125V11.25a9 9 0 00-9-9z" />
                </svg>
              </div>
              <h3 className="mt-4 text-lg font-semibold text-gray-900">Resume Analysis</h3>
              <p className="mt-2 text-sm text-gray-600">
                Upload your resume for AI-powered analysis and personalized recommendations
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
