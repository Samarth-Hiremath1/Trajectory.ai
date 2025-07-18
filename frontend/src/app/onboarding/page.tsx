'use client'

import { useAuth } from '@/lib/auth-context'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'
import OnboardingWizard from '@/components/onboarding/OnboardingWizard'

export default function OnboardingPage() {
  const { user, profile, loading, profileLoading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login')
      return
    }
    // If user already has a profile, redirect to dashboard
    if (!loading && !profileLoading && user && profile) {
      router.push('/dashboard')
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

  // If user already has a profile, don't show onboarding
  if (profile) {
    return null
  }

  return <OnboardingWizard />
}