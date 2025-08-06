'use client'

import { SessionProvider } from "next-auth/react"
import { AuthProvider } from "@/lib/auth-context"
import { ErrorBoundary } from "@/components/error/ErrorBoundary"

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ErrorBoundary>
      <SessionProvider>
        <AuthProvider>
          {children}
        </AuthProvider>
      </SessionProvider>
    </ErrorBoundary>
  )
}