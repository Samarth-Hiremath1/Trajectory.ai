'use client'

interface QuickActionsProps {
  profile: any
  onEditProfile: () => void
  onStartOnboarding: () => void
}

export function QuickActions({ profile, onEditProfile, onStartOnboarding }: QuickActionsProps) {
  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
      <div className="space-y-3">
        {!profile ? (
          <div className="bg-yellow-50 border border-yellow-200 rounded p-3">
            <p className="text-yellow-800 mb-2">Complete your profile setup to get started!</p>
            <button
              onClick={onStartOnboarding}
              className="bg-yellow-600 hover:bg-yellow-700 text-white px-3 py-1 rounded text-sm font-medium"
            >
              Start Onboarding
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="bg-green-50 border border-green-200 rounded p-3">
              <p className="text-green-800">Profile complete! Ready for AI features.</p>
            </div>
            
            <div className="flex flex-wrap gap-2">
              <button
                onClick={onEditProfile}
                className="text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-2 rounded font-medium"
              >
                Edit Profile
              </button>
              
              <button
                onClick={() => {
                  // Scroll to chat section
                  const chatTab = document.querySelector('[data-tab="chat"]') as HTMLButtonElement
                  if (chatTab) {
                    chatTab.click()
                    chatTab.scrollIntoView({ behavior: 'smooth' })
                  }
                }}
                className="text-sm bg-indigo-100 hover:bg-indigo-200 text-indigo-700 px-3 py-2 rounded font-medium"
              >
                Start Chat
              </button>
              
              <button
                onClick={() => {
                  // Scroll to roadmap section
                  const roadmapTab = document.querySelector('[data-tab="roadmap"]') as HTMLButtonElement
                  if (roadmapTab) {
                    roadmapTab.click()
                    roadmapTab.scrollIntoView({ behavior: 'smooth' })
                  }
                }}
                className="text-sm bg-purple-100 hover:bg-purple-200 text-purple-700 px-3 py-2 rounded font-medium"
              >
                View Roadmaps
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}