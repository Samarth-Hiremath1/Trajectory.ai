'use client'

import { useState } from 'react'
import { supabase } from '@/lib/supabase'

export default function TestConnectionPage() {
  const [result, setResult] = useState<string>('')
  const [loading, setLoading] = useState(false)

  const testConnection = async () => {
    setLoading(true)
    setResult('Testing connection...')

    try {
      // Test 1: Check if client is created
      console.log('Supabase client:', supabase)
      setResult(prev => prev + '\n✓ Supabase client created')

      // Test 2: Check environment variables
      const url = process.env.NEXT_PUBLIC_SUPABASE_URL
      const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
      console.log('Environment variables:', { url: url?.substring(0, 30) + '...', key: key?.substring(0, 30) + '...' })
      setResult(prev => prev + `\n✓ Environment variables loaded: ${url ? 'URL OK' : 'URL MISSING'}, ${key ? 'KEY OK' : 'KEY MISSING'}`)

      // Test 3: Try to get session (this should work even without auth)
      const { data: sessionData, error: sessionError } = await supabase.auth.getSession()
      console.log('Session test:', { sessionData, sessionError })
      
      if (sessionError) {
        setResult(prev => prev + `\n❌ Session test failed: ${sessionError.message}`)
      } else {
        setResult(prev => prev + '\n✓ Session test passed (no active session)')
      }

      // Test 4: Try a simple database query (this might fail due to RLS, but should show connection)
      const { data: profileData, error: profileError } = await supabase
        .from('profiles')
        .select('id')
        .limit(1)
      
      console.log('Database test:', { profileData, profileError })
      
      if (profileError) {
        if (profileError.message.includes('JWT')) {
          setResult(prev => prev + '\n✓ Database connection OK (JWT auth required as expected)')
        } else {
          setResult(prev => prev + `\n❌ Database test failed: ${profileError.message}`)
        }
      } else {
        setResult(prev => prev + '\n✓ Database test passed')
      }

    } catch (error) {
      console.error('Connection test error:', error)
      setResult(prev => prev + `\n❌ Connection test failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-2xl font-bold mb-6">Supabase Connection Test</h1>
        
        <button
          onClick={testConnection}
          disabled={loading}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded mb-4 disabled:opacity-50"
        >
          {loading ? 'Testing...' : 'Test Connection'}
        </button>

        <div className="bg-white p-4 rounded border">
          <h2 className="font-semibold mb-2">Test Results:</h2>
          <pre className="whitespace-pre-wrap text-sm font-mono bg-gray-100 p-3 rounded">
            {result || 'Click "Test Connection" to run tests'}
          </pre>
        </div>

        <div className="mt-6 text-sm text-gray-600">
          <p>This page helps debug Supabase connection issues.</p>
          <p>Check the browser console for detailed logs.</p>
        </div>
      </div>
    </div>
  )
}