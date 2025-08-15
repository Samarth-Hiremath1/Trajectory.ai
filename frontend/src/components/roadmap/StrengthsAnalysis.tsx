'use client'

import React, { useState } from 'react'
import { 
  ChevronDownIcon, 
  ChevronRightIcon,
  LightBulbIcon,
  StarIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon,
  ShieldCheckIcon,
  TrophyIcon
} from '@heroicons/react/24/outline'

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
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['rationale']))

  if (!analysis || Object.keys(analysis).length === 0) {
    return null
  }

  const toggleSection = (sectionId: string) => {
    const newExpanded = new Set(expandedSections)
    if (newExpanded.has(sectionId)) {
      newExpanded.delete(sectionId)
    } else {
      newExpanded.add(sectionId)
    }
    setExpandedSections(newExpanded)
  }

  const CollapsibleSection = ({ 
    title, 
    items, 
    icon, 
    sectionId, 
    bgColor,
    borderColor,
    iconColor 
  }: { 
    title: string
    items: AnalysisItem[]
    icon: React.ReactNode
    sectionId: string
    bgColor: string
    borderColor: string
    iconColor: string
  }) => {
    if (!items || items.length === 0) return null
    
    const isExpanded = expandedSections.has(sectionId)
    
    return (
      <div className={`${bgColor} ${borderColor} border-2 rounded-xl overflow-hidden shadow-sm hover:shadow-md transition-all duration-200`}>
        <button
          onClick={() => toggleSection(sectionId)}
          className="w-full px-6 py-4 flex items-center justify-between text-left hover:bg-white/50 transition-colors duration-200"
        >
          <div className="flex items-center space-x-3">
            <div className={`p-2 rounded-lg ${iconColor}`}>
              {icon}
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
              <p className="text-sm text-gray-600">{items.length} item{items.length !== 1 ? 's' : ''}</p>
            </div>
          </div>
          {isExpanded ? (
            <ChevronDownIcon className="w-5 h-5 text-gray-500" />
          ) : (
            <ChevronRightIcon className="w-5 h-5 text-gray-500" />
          )}
        </button>
        
        {isExpanded && (
          <div className="px-6 pb-6 bg-white/30 backdrop-blur-sm">
            <ul className="space-y-4">
              {items.map((item, index) => (
                <li key={index} className="bg-white/60 rounded-lg p-4 border border-white/50">
                  <h4 className="font-semibold text-gray-900 mb-2">{item.title.replace(/\*\*/g, '')}</h4>
                  {item.description && (
                    <p className="text-sm text-gray-700 leading-relaxed">{item.description.replace(/\*\*/g, '')}</p>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="bg-white border border-slate-200 rounded-2xl p-8 mb-8 shadow-sm">
        <h2 className="text-3xl font-bold text-slate-900 mb-3">Career Transition Analysis</h2>
        <p className="text-slate-600 text-lg leading-relaxed mb-6">
          Based on your background, here&apos;s a comprehensive analysis of your transition from{' '}
          <span className="font-semibold bg-slate-100 text-slate-700 px-3 py-1 rounded-full">{currentRole}</span> to{' '}
          <span className="font-semibold bg-sky-100 text-sky-700 px-3 py-1 rounded-full">{targetRole}</span>
        </p>
        
        {/* Networking Tip */}
        <div className="border-t border-slate-200 pt-4 mt-2">
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0 mt-1">
              <span className="text-gray-400 text-sm">💡</span>
            </div>
            <p className="text-slate-600 text-base leading-relaxed">
              <span className="font-bold text-slate-700">Pro Tip:</span> Consider starting with networking—connecting with professionals in your target field can provide valuable insights. 
              Resources like{' '}
              <a 
                href="https://adplist.org/" 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-800 underline font-medium"
              >
                ADPList
              </a>
              {' '}and{' '}
              <a 
                href="https://www.linkedin.com/" 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-800 underline font-medium"
              >
                LinkedIn
              </a>
              {' '}can help you connect with mentors and industry professionals.
            </p>
          </div>
        </div>
      </div>

      <div className="space-y-6">
        {/* Collapsible "Why This Roadmap Was Created" Section */}
        {analysis.roadmap_rationale && (
          <div className="bg-sky-50 border-2 border-sky-200 rounded-xl overflow-hidden shadow-sm hover:shadow-md transition-all duration-200">
            <button
              onClick={() => toggleSection('rationale')}
              className="w-full px-6 py-4 flex items-center justify-between text-left hover:bg-white/50 transition-colors duration-200"
            >
              <div className="flex items-center space-x-3">
                <div className="p-2 rounded-lg bg-sky-100">
                  <LightBulbIcon className="w-6 h-6 text-sky-600" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-slate-900">Why This Roadmap Was Created For You</h3>
                  <p className="text-sm text-slate-600">Personalized rationale and context</p>
                </div>
              </div>
              {expandedSections.has('rationale') ? (
                <ChevronDownIcon className="w-5 h-5 text-slate-500" />
              ) : (
                <ChevronRightIcon className="w-5 h-5 text-slate-500" />
              )}
            </button>
            
            {expandedSections.has('rationale') && (
              <div className="px-6 pb-6 bg-white/50">
                <div className="bg-white rounded-lg p-6 border border-slate-200">
                  <div className="text-slate-800 leading-relaxed whitespace-pre-line text-base">
                    {analysis.roadmap_rationale}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Analysis Sections Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <CollapsibleSection
            title="Current Strengths"
            items={analysis.strengths}
            icon={<StarIcon className="w-6 h-6 text-emerald-600" />}
            sectionId="strengths"
            bgColor="bg-emerald-50"
            borderColor="border-emerald-200"
            iconColor="bg-emerald-100"
          />

          <CollapsibleSection
            title="Areas for Improvement"
            items={analysis.weaknesses}
            icon={<ExclamationTriangleIcon className="w-6 h-6 text-amber-600" />}
            sectionId="weaknesses"
            bgColor="bg-amber-50"
            borderColor="border-amber-200"
            iconColor="bg-amber-100"
          />

          <CollapsibleSection
            title="Transferable Skills"
            items={analysis.transferable_skills}
            icon={<ArrowPathIcon className="w-6 h-6 text-sky-600" />}
            sectionId="transferable"
            bgColor="bg-sky-50"
            borderColor="border-sky-200"
            iconColor="bg-sky-100"
          />

          <CollapsibleSection
            title="Key Challenges"
            items={analysis.challenges}
            icon={<ShieldCheckIcon className="w-6 h-6 text-rose-600" />}
            sectionId="challenges"
            bgColor="bg-rose-50"
            borderColor="border-rose-200"
            iconColor="bg-rose-100"
          />

          <div className="lg:col-span-2">
            <CollapsibleSection
              title="Competitive Advantages"
              items={analysis.advantages}
              icon={<TrophyIcon className="w-6 h-6 text-violet-600" />}
              sectionId="advantages"
              bgColor="bg-violet-50"
              borderColor="border-violet-200"
              iconColor="bg-violet-100"
            />
          </div>
        </div>


      </div>
    </div>
  )
}