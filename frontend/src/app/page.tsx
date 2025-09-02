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
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-purple-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Hero Section */}
        <div className="flex flex-col items-center justify-center min-h-screen py-12">
          <div className="text-center max-w-4xl">
            <div className="mb-6 flex items-center justify-center">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-indigo-600 rounded-full"></div>
                <div className="w-8 h-0.5 bg-indigo-300"></div>
                <div className="w-3 h-3 bg-indigo-400 rounded-full"></div>
                <div className="w-8 h-0.5 bg-indigo-300"></div>
                <div className="w-3 h-3 bg-indigo-200 rounded-full"></div>
              </div>
            </div>

            <h1 className="text-4xl font-bold text-gray-900 sm:text-6xl lg:text-7xl">
              AI-Powered Career
              <span className="text-indigo-600 block">Roadmaps</span>
            </h1>

            <p className="mt-6 text-xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
              Get a personalized, step-by-step roadmap tailored to your background, timeline, and career goals.
              Transform your career transition with AI-generated phases, milestones, and actionable insights.
            </p>

            <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                href="/signup"
                className="w-full sm:w-auto rounded-lg bg-indigo-600 px-8 py-4 text-base font-semibold text-white shadow-lg hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 transition-all duration-200"
              >
                Create Your Roadmap
              </Link>
              <Link
                href="/login"
                className="w-full sm:w-auto text-base font-semibold leading-6 text-gray-700 hover:text-indigo-600 px-8 py-4 transition-colors duration-200"
              >
                Sign in <span aria-hidden="true">→</span>
              </Link>
            </div>
          </div>

          {/* Roadmap Generation Process */}
          <div className="mt-20 w-full max-w-6xl">
            <div className="text-center mb-12">
              <h2 className="text-3xl font-bold text-gray-900 mb-4">
                Your Personalized Career Journey
              </h2>
              <p className="text-lg text-gray-600 max-w-2xl mx-auto">
                Our AI analyzes your unique situation to create a customized roadmap that fits your timeline, constraints, and focus areas.
              </p>
            </div>

            {/* Main Roadmap Feature */}
            <div className="bg-white rounded-2xl shadow-xl p-8 mb-12 border border-gray-100">
              <div className="flex flex-col lg:flex-row items-center gap-8">
                <div className="flex-1">
                  <div className="flex items-center mb-4">
                    <div className="w-12 h-12 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl flex items-center justify-center mr-4">
                      <svg className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M9 6.75V15m6-6v8.25m.503 3.498l4.875-2.437c.381-.19.622-.58.622-1.006V4.82c0-.836-.88-1.38-1.628-1.006l-3.869 1.934c-.317.159-.69.159-1.006 0L9.503 3.252a1.125 1.125 0 00-1.006 0L3.622 5.689C3.24 5.88 3 6.27 3 6.695V19.18c0 .836.88 1.38 1.628 1.006l3.869-1.934c.317-.159.69-.159 1.006 0l4.994 2.497c.317.158.69.158 1.006 0z" />
                      </svg>
                    </div>
                    <h3 className="text-2xl font-bold text-gray-900">Smart Roadmap Generation</h3>
                  </div>
                  <p className="text-gray-600 text-lg mb-6 leading-relaxed">
                    Tell us your current role, target position, and preferences. Our AI creates a detailed,
                    phase-by-phase roadmap with specific skills to develop, learning resources, and measurable milestones
                    customized to your unique situation.
                  </p>
                  <div className="space-y-3">
                    <div className="flex items-center text-gray-700">
                      <svg className="h-5 w-5 text-indigo-600 mr-3" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                      Personalized to your background and constraints
                    </div>
                    <div className="flex items-center text-gray-700">
                      <svg className="h-5 w-5 text-indigo-600 mr-3" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                      Flexible timelines that work with your schedule
                    </div>
                    <div className="flex items-center text-gray-700">
                      <svg className="h-5 w-5 text-indigo-600 mr-3" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                      Actionable milestones with specific deliverables
                    </div>
                  </div>
                </div>

                <div className="flex-1 lg:pl-8">
                  <div className="bg-gray-50 rounded-xl p-6 space-y-4">
                    <div className="flex items-center">
                      <div className="w-8 h-8 bg-indigo-600 rounded-full flex items-center justify-center text-white text-sm font-semibold mr-3">1</div>
                      <div>
                        <div className="font-semibold text-gray-900">Foundation Phase</div>
                        <div className="text-sm text-gray-600">Build core skills • 4-6 weeks</div>
                      </div>
                    </div>
                    <div className="ml-5 border-l-2 border-indigo-200 pl-6 pb-2">
                      <div className="text-sm text-gray-600">Learn fundamentals, complete online courses, build first project</div>
                    </div>

                    <div className="flex items-center">
                      <div className="w-8 h-8 bg-indigo-500 rounded-full flex items-center justify-center text-white text-sm font-semibold mr-3">2</div>
                      <div>
                        <div className="font-semibold text-gray-900">Development Phase</div>
                        <div className="text-sm text-gray-600">Advanced skills • 6-8 weeks</div>
                      </div>
                    </div>
                    <div className="ml-5 border-l-2 border-indigo-200 pl-6 pb-2">
                      <div className="text-sm text-gray-600">Specialized training, portfolio projects, networking</div>
                    </div>

                    <div className="flex items-center">
                      <div className="w-8 h-8 bg-indigo-400 rounded-full flex items-center justify-center text-white text-sm font-semibold mr-3">3</div>
                      <div>
                        <div className="font-semibold text-gray-900">Application Phase</div>
                        <div className="text-sm text-gray-600">Job search • 2-4 weeks</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Supporting Features */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100">
                <div className="flex items-center mb-4">
                  <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center mr-3">
                    <svg className="h-5 w-5 text-purple-600" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900">AI Career Mentoring</h3>
                </div>
                <p className="text-gray-600">
                  Get personalized guidance and feedback as you progress through your roadmap.
                  Ask questions, get unstuck, and stay motivated with AI-powered mentoring.
                </p>
              </div>

              <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100">
                <div className="flex items-center mb-4">
                  <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center mr-3">
                    <svg className="h-5 w-5 text-green-600" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0-1.125-.504-1.125-1.125V11.25a9 9 0 00-9-9z" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900">Resume Optimization</h3>
                </div>
                <p className="text-gray-600">
                  Upload your resume for AI analysis that identifies gaps and provides specific
                  recommendations to align with your target role and roadmap goals.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
