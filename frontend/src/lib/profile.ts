import { supabase, Profile } from './supabase'

export interface ProfileData {
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
  
  const insertData = {
    user_id: userId,
    ...profileData,
  }
  
  console.log('Insert data:', insertData)
  
  const { data, error } = await supabase
    .from('profiles')
    .insert(insertData)
    .select()
    .single()

  if (error) {
    // If profile already exists, update it instead
    if (error.code === '23505') {
      console.log('Profile already exists, updating instead...')
      return await updateProfile(userId, profileData)
    }
    
    console.error('Error creating profile:', error)
    console.error('Error details:', JSON.stringify(error, null, 2))
    return null
  }

  console.log('Profile created successfully:', data)
  return data
}

export async function updateProfile(userId: string, profileData: Partial<ProfileData>): Promise<Profile | null> {
  try {
    const response = await fetch('/api/profile', {
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