'use client'

import { createContext, useContext, useEffect, useState, useCallback, useMemo } from 'react'
import { useSession, signOut as nextAuthSignOut } from 'next-auth/react'
import { Profile } from './supabase'
import { getProfile } from './profile'

interface AuthUser {
  id: string
  email: string
  name?: string | null
  image?: string | null
}

interface ExtendedUser {
  id: string
  name?: string | null
  email?: string | null
  image?: string | null
}

interface AuthContextType {
  user: AuthUser | null
  profile: Profile | null
  loading: boolean
  profileLoading: boolean
  signOut: () => Promise<void>
  refreshProfile: () => Promise<void>
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  profile: null,
  loading: true,
  profileLoading: false,
  signOut: async () => {},
  refreshProfile: async () => {},
})

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const { data: session, status } = useSession()
  const [profile, setProfile] = useState<Profile | null>(null)
  const [profileLoading, setProfileLoading] = useState(false)

  const user: AuthUser | null = useMemo(() => {
    return session?.user ? {
      id: (session.user as ExtendedUser).id,
      email: session.user.email!,
      name: session.user.name,
      image: session.user.image,
    } : null
  }, [session?.user])

  const loading = status === 'loading'

  const refreshProfile = useCallback(async () => {
    if (user) {
      console.log('🔍 Refreshing profile for user:', user.id)
      setProfileLoading(true)
      try {
        const userProfile = await getProfile(user.id)
        console.log('📋 Profile found:', userProfile ? 'YES' : 'NO', userProfile)
        setProfile(userProfile)
      } catch (error) {
        console.error('Error in refreshProfile:', error)
        // Ensure we don't throw the error up to the error boundary
        setProfile(null)
      } finally {
        setProfileLoading(false)
      }
    }
  }, [user])

  useEffect(() => {
    // Load profile when user changes
    if (user) {
      refreshProfile()
    } else {
      setProfile(null)
    }
  }, [user?.id]) // Only depend on user ID to avoid infinite loops

  const signOut = async () => {
    await nextAuthSignOut({ callbackUrl: '/' })
    setProfile(null)
  }

  const value = {
    user,
    profile,
    loading,
    profileLoading,
    signOut,
    refreshProfile,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}