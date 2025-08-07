'use client'

import React from 'react'

interface AnalysisItem {
  title: string
  description: string
}

interface StrengthsAnalysisProps {
  analysis: {
    roadmap_rationale?: string
    strengths: AnalysisItem[]
    weaknesses: AnalysisItem[]
    transferable_skills: AnalysisItem[]
    challenges: AnalysisItem[]
    advantages: AnalysisItem[]
  }
  currentRole: string
  targetRole: string
}

export default function StrengthsAnalysis({ analysis, currentRole, targetRole }: StrengthsAnalysisProps) {
  if (!analysis || Object.keys(analysis).length === 0) {
    return null
  }

  const renderSection = (title: string, items: AnalysisItem[], icon: string, bgColor: string) => {
    if (!items || items.length === 0) return null

    return (
      <div className={`${bgColor} rounded-lg p-4 mb-4`}>
        <h3 className="text-lg font-semibold mb-3 flex items-center">
          <span className="mr-2">{icon}</span>
          {title}
        </h3>
        <ul className="space-y-2">
          {items.map((item, index) => (
            <li key={index} className="flex flex-col">
              <span className="font-medium text-gray-800">{item.title}</span>
              {item.description && (
                <span className="text-sm text-gray-600 mt-1">{item.description}</span>
              )}
            </li>
          ))}
        </ul>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-2">
          Career Transition Analysis
        </h2>
        <p className="text-gray-600 mb-4">
          Based on your background, here's an analysis of your transition from{' '}
          <span className="font-semibold text-blue-600">{currentRole}</span> to{' '}
          <span className="font-semibold text-green-600">{targetRole}</span>
        </p>
        
        {/* Detailed "Why" Description */}
        {analysis.roadmap_rationale && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
            <h3 className="text-lg font-semibold text-blue-800 mb-2 flex items-center">
              <span className="mr-2">🎯</span>
              Why This Roadmap Was Created For You
            </h3>
            <div className="text-gray-700 leading-relaxed whitespace-pre-line">
              {analysis.roadmap_rationale}
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {renderSection(
          'Current Strengths',
          analysis.strengths,
          '💪',
          'bg-green-50 border border-green-200'
        )}

        {renderSection(
          'Areas for Improvement',
          analysis.weaknesses,
          '🎯',
          'bg-orange-50 border border-orange-200'
        )}

        {renderSection(
          'Transferable Skills',
          analysis.transferable_skills,
          '🔄',
          'bg-blue-50 border border-blue-200'
        )}

        {renderSection(
          'Key Challenges',
          analysis.challenges,
          '⚠️',
          'bg-red-50 border border-red-200'
        )}

        {renderSection(
          'Competitive Advantages',
          analysis.advantages,
          '⭐',
          'bg-purple-50 border border-purple-200'
        )}
      </div>

      <div className="mt-6 p-4 bg-gray-50 rounded-lg">
        <p className="text-sm text-gray-600">
          💡 <strong>Tip:</strong> This analysis helps explain the "why" behind each step in your roadmap. 
          Use it to understand which areas need the most focus and how your existing skills give you an advantage.
        </p>
      </div>
    </div>
  )
}