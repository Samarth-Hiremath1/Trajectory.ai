'use client'

interface WaveformLoaderProps {
  size?: string
  stroke?: string
  speed?: string
  color?: string
  message?: string
  className?: string
}

export function WaveformLoader({
  size = "35",
  color = "#6366f1", // indigo-500
  message,
  className = ""
}: WaveformLoaderProps) {
  const sizeNum = parseInt(size)
  
  return (
    <div className={`flex flex-col items-center justify-center space-y-3 ${className}`}>
      {/* Custom waveform animation using CSS */}
      <div 
        className="flex items-center space-x-1"
        style={{ height: `${sizeNum}px` }}
      >
        {[...Array(5)].map((_, i) => (
          <div
            key={i}
            className="rounded-full animate-pulse"
            style={{
              width: `${sizeNum / 8}px`,
              height: `${sizeNum / 2 + (i % 2) * (sizeNum / 4)}px`,
              backgroundColor: color,
              animationDelay: `${i * 0.1}s`,
              animationDuration: '1s'
            }}
          />
        ))}
      </div>
      {message && (
        <p className="text-sm text-gray-600 text-center animate-pulse">
          {message}
        </p>
      )}
    </div>
  )
}

// Roadmap generation specific loader
export function RoadmapGenerationLoader({ progress }: { progress?: number }) {
  const messages = [
    "Analyzing your career background...",
    "Researching target role requirements...", 
    "Generating personalized roadmap phases...",
    "Curating learning resources...",
    "Finalizing your career roadmap..."
  ]
  
  const currentMessage = progress 
    ? messages[Math.min(Math.floor((progress / 100) * messages.length), messages.length - 1)]
    : "Generating your personalized career roadmap..."

  return (
    <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-lg p-8 text-center">
      <WaveformLoader 
        size="45"
        stroke="4"
        speed="1.2"
        color="#6366f1"
        message={currentMessage}
        className="min-h-[120px]"
      />
      {progress && (
        <div className="mt-4">
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-indigo-600 h-2 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
          <p className="text-xs text-gray-500 mt-2">{Math.round(progress)}% complete</p>
        </div>
      )}
    </div>
  )
}

// Resume upload specific loader
export function ResumeUploadLoader({ progress }: { progress?: number }) {
  const messages = [
    "Uploading your resume...",
    "Extracting text content...",
    "Analyzing your experience...", 
    "Processing skills and achievements...",
    "Updating your AI context..."
  ]
  
  const currentMessage = progress 
    ? messages[Math.min(Math.floor((progress / 100) * messages.length), messages.length - 1)]
    : "Processing your resume..."

  return (
    <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg p-8 text-center">
      <WaveformLoader 
        size="40"
        stroke="3.5"
        speed="1.1" 
        color="#3b82f6"
        message={currentMessage}
        className="min-h-[100px]"
      />
      {progress && (
        <div className="mt-4">
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
          <p className="text-xs text-gray-500 mt-2">{Math.round(progress)}% complete</p>
        </div>
      )}
    </div>
  )
}