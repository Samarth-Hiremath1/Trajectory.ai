import { supabase, Profile } from './supabase'

export interface ProfileData {
  name?: string
  education: Record<string, unknown>
  career_background: string
  current_role: string
  target_roles: string[]
  additional_details: string
}

export async function getProfile(userId: string): Promise<Profile | null> {
  console.log('Fetching profile for user ID:', userId)
  
  const { data, error } = await supabase
    .from('profiles')
    .select('*')
    .eq('user_id', userId)
    .single()

  if (error) {
    // If the error is "not found", that's expected for new users
    if (error.code === 'PGRST116') {
      console.log('No profile found for user - this is normal for new users')
      return null
    }
    console.error('Error fetching profile:', error)
    return null
  }

  console.log('Profile found:', data)
  return data
}

export async function createProfile(userId: string, profileData: ProfileData): Promise<Profile | null> {
  console.log('Creating profile for user ID:', userId)
  console.log('Profile data:', profileData)
  
  try {
    // Use backend API instead of direct Supabase calls
    const apiUrl = `/api/profile/${userId}`
    console.log('Making request to:', apiUrl)
    console.log('Request body:', JSON.stringify(profileData, null, 2))
    
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-User-Id': userId,
      },
      body: JSON.stringify(profileData),
    })

    console.log('Response status:', response.status)
    console.log('Response headers:', Object.fromEntries(response.headers.entries()))

    if (!response.ok) {
      const responseText = await response.text()
      console.error('Raw response text:', responseText)
      
      let errorData
      try {
        errorData = JSON.parse(responseText)
      } catch {
        errorData = { detail: `HTTP ${response.status}: ${responseText || 'Profile creation failed'}` }
      }
      
      console.error('Profile creation failed:', errorData)
      console.error('Response status:', response.status)
      
      // If profile already exists, try updating instead
      if (response.status === 400 && errorData.detail?.includes('already exist')) {
        console.log('Profile already exists, updating instead...')
        return await updateProfile(userId, profileData)
      }
      
      throw new Error(errorData.detail || `Failed to create profile (HTTP ${response.status})`)
    }

    const result = await response.json()
    console.log('Profile created successfully:', result)
    
    return result
  } catch (error) {
    console.error('Error in createProfile:', error)
    throw error
  }
}

export async function updateProfile(userId: string, profileData: Partial<ProfileData>): Promise<Profile | null> {
  try {
    const response = await fetch(`/api/profile/${userId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(profileData),
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: 'Update failed' }))
      throw new Error(errorData.error || 'Failed to update profile')
    }

    const result = await response.json()
    return result

  } catch (error) {
    console.error('Error updating profile:', error)
    throw error
  }
}