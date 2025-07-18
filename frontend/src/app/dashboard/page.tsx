'use client'

import { useAuth } from '@/lib/auth-context'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'

export default function DashboardPage() {
  const { user, profile, loading, profileLoading, signOut } = useAuth()
  const router = useRouter()

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
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">User Information</h3>
              <div className="space-y-2">
                <p><span className="font-medium">Email:</span> {user.email}</p>
                <p><span className="font-medium">User ID:</span> {user.id}</p>
                <p><span className="font-medium">Profile Status:</span> {profile ? 'Profile Created' : 'No Profile Yet'}</p>
                {profile && (
                  <>
                    <p><span className="font-medium">Current Role:</span> {profile.current_role || 'Not specified'}</p>
                    <p><span className="font-medium">Target Roles:</span> {profile.target_roles.length > 0 ? profile.target_roles.join(', ') : 'Not specified'}</p>
                  </>
                )}
              </div>
              {profile && (
                <div className="mt-4">
                  <button
                    onClick={() => router.push('/profile/edit')}
                    className="text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1 rounded"
                  >
                    Edit Profile
                  </button>
                </div>
              )}
            </div>
            
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Next Steps</h3>
              <div className="space-y-3">
                {!profile ? (
                  <div className="bg-yellow-50 border border-yellow-200 rounded p-3">
                    <p className="text-yellow-800">Complete your profile setup to get started!</p>
                    <button
                      onClick={() => router.push('/onboarding')}
                      className="mt-2 bg-yellow-600 hover:bg-yellow-700 text-white px-3 py-1 rounded text-sm"
                    >
                      Start Onboarding
                    </button>
                  </div>
                ) : (
                  <div className="bg-green-50 border border-green-200 rounded p-3">
                    <p className="text-green-800">Profile complete! Ready for AI features.</p>
                  </div>
                )}
              </div>
            </div>
          </div>
          
          <div className="border-4 border-dashed border-gray-200 rounded-lg h-64 flex items-center justify-center">
            <div className="text-center">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">
                Welcome to your Career Dashboard
              </h2>
              <p className="text-gray-600 mb-4">
                This is where your AI chat and roadmap features will be implemented.
              </p>
              <p className="text-sm text-gray-500">
                Authentication is working! ✅ Database connection established! ✅
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}