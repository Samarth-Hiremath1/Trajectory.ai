'use client'

export function TypingIndicator() {
  return (
    <div className="flex justify-start mb-4">
      <div className="flex max-w-xs lg:max-w-md">
        {/* Avatar */}
        <div className="flex-shrink-0 mr-3">
          <div className="w-8 h-8 rounded-full bg-gray-300 text-gray-700 flex items-center justify-center text-sm font-medium">
            🤖
          </div>
        </div>

        {/* Typing Animation */}
        <div className="flex flex-col items-start">
          <div className="px-4 py-3 rounded-lg bg-gray-100">
            <div className="flex space-x-1">
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
            </div>
          </div>
          <div className="mt-1 text-xs text-gray-500">
            AI is typing...
          </div>
        </div>
      </div>
    </div>
  )
}