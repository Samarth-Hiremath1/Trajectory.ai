import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://placeholder.supabase.co'
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'placeholder-key'

// Create client for database operations only (auth handled by NextAuth)
export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    persistSession: false, // Don't persist auth sessions since we use NextAuth
  },
  global: {
    headers: {
      'X-Client-Info': 'trajectory-ai-frontend'
    }
  }
})

// Database types for TypeScript
export interface Profile {
  id: string
  user_id: string
  name?: string
  education: Record<string, unknown>
  career_background: string
  current_role: string
  target_roles: string[]
  additional_details: string
  created_at: string
  updated_at: string
}

export interface Database {
  public: {
    Tables: {
      profiles: {
        Row: Profile
        Insert: Omit<Profile, 'id' | 'created_at' | 'updated_at'>
        Update: Partial<Omit<Profile, 'id' | 'user_id' | 'created_at'>>
      }
    }
  }
}