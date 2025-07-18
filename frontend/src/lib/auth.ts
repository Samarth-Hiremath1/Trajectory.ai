import NextAuth from "next-auth"
import GoogleProvider from "next-auth/providers/google"
import CredentialsProvider from "next-auth/providers/credentials"
import type { Session, User } from "next-auth"
import type { JWT } from "next-auth/jwt"
import { supabase } from "./supabase"

declare module "next-auth" {
  interface Session {
    user: {
      id: string
      email: string
      name?: string | null
      image?: string | null
    }
  }
}

const authConfig = {
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
    CredentialsProvider({
      name: "credentials",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" }
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          return null
        }

        try {
          // Try to sign in first
          const { data, error } = await supabase.auth.signInWithPassword({
            email: credentials.email as string,
            password: credentials.password as string,
          })

          if (error) {
            // If user doesn't exist, try to sign them up
            if (error.message.includes('Invalid login credentials')) {
              const { data: signUpData, error: signUpError } = await supabase.auth.signUp({
                email: credentials.email as string,
                password: credentials.password as string,
              })

              if (signUpError) {
                console.error('Signup error:', signUpError)
                return null
              }

              if (signUpData.user) {
                return {
                  id: signUpData.user.id,
                  email: signUpData.user.email!,
                  name: signUpData.user.user_metadata?.full_name || null,
                  image: signUpData.user.user_metadata?.avatar_url || null,
                }
              }
            }
            return null
          }

          if (data.user) {
            return {
              id: data.user.id,
              email: data.user.email!,
              name: data.user.user_metadata?.full_name || null,
              image: data.user.user_metadata?.avatar_url || null,
            }
          }

          return null
        } catch (error) {
          console.error('Auth error:', error)
          return null
        }
      }
    })
  ],
  callbacks: {
    async session({ session, token }: { session: Session; token: JWT }) {
      if (token.sub && session.user) {
        session.user.id = token.sub
      }
      return session
    },
    async jwt({ token, user }: { token: JWT; user: User }) {
      if (user) {
        token.sub = user.id
      }
      return token
    },
  },
  pages: {
    signIn: '/login',
    error: '/login',
  },
  session: {
    strategy: "jwt" as const,
  },
}

export const { handlers, auth, signIn, signOut } = NextAuth(authConfig)