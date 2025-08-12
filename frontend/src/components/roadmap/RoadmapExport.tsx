'use client'

import { useState } from 'react'
import { Roadmap } from '@/types/roadmap'

interface RoadmapExportProps {
  roadmap: Roadmap
  className?: string
}

export function RoadmapExport({ roadmap, className = '' }: RoadmapExportProps) {
  const [isExporting, setIsExporting] = useState(false)
  const [showExportMenu, setShowExportMenu] = useState(false)

  const exportToDailyDashboard = async () => {
    try {
      setIsExporting(true)
      
      // Extract tasks and dates from roadmap phases
      const tasks = []
      let currentWeek = 1
      
      for (const phase of roadmap.phases) {
        // Add phase start as a task
        tasks.push({
          title: `Start Phase ${phase.phase_number}: ${phase.title}`,
          description: phase.description,
          dueDate: new Date(Date.now() + (currentWeek - 1) * 7 * 24 * 60 * 60 * 1000),
          category: 'Career Development',
          priority: 'high',
          source: 'roadmap'
        })
        
        // Add milestones as tasks
        for (const milestone of phase.milestones) {
          const milestoneWeek = currentWeek + milestone.estimated_completion_weeks - 1
          tasks.push({
            title: milestone.title,
            description: milestone.description || `Milestone for ${phase.title}`,
            dueDate: new Date(Date.now() + (milestoneWeek - 1) * 7 * 24 * 60 * 60 * 1000),
            category: 'Career Development',
            priority: milestone.estimated_completion_weeks <= 2 ? 'high' : 'medium',
            source: 'roadmap'
          })
        }
        
        currentWeek += phase.duration_weeks
      }
      
      // Store tasks in localStorage for daily dashboard
      const existingTasks = JSON.parse(localStorage.getItem('tasks') || '[]')
      const updatedTasks = [...existingTasks, ...tasks]
      localStorage.setItem('tasks', JSON.stringify(updatedTasks))
      
      setShowExportMenu(false)
      alert(`Successfully exported ${tasks.length} tasks to Daily Dashboard!`)
      
    } catch (error) {
      console.error('Export to daily dashboard error:', error)
      alert(`Export failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
    } finally {
      setIsExporting(false)
    }
  }

  const exportRoadmap = async (format: 'json' | 'markdown') => {
    if (!roadmap.id) {
      alert('Cannot export roadmap: No ID found')
      return
    }

    try {
      setIsExporting(true)
      
      const response = await fetch(`/api/roadmap/${roadmap.id}/export?format=${format}`)
      
      if (!response.ok) {
        throw new Error(`Export failed: ${response.statusText}`)
      }

      const data = await response.json()

      if (format === 'json') {
        // Download JSON file
        const blob = new Blob([JSON.stringify(data, null, 2)], { 
          type: 'application/json' 
        })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${roadmap.title.replace(/\s+/g, '_').toLowerCase()}_roadmap.json`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)
      } else if (format === 'markdown') {
        // Download Markdown file
        const blob = new Blob([data.content], { 
          type: 'text/markdown' 
        })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = data.filename || `${roadmap.title.replace(/\s+/g, '_').toLowerCase()}_roadmap.md`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)
      }

      setShowExportMenu(false)
    } catch (error) {
      console.error('Export error:', error)
      alert(`Export failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
    } finally {
      setIsExporting(false)
    }
  }

  const copyRoadmapLink = async () => {
    if (!roadmap.id) return

    try {
      const url = `${window.location.origin}/roadmap/${roadmap.id}`
      await navigator.clipboard.writeText(url)
      alert('Roadmap link copied to clipboard!')
    } catch (error) {
      console.error('Failed to copy link:', error)
      alert('Failed to copy link to clipboard')
    }
  }

  return (
    <div className={`relative ${className}`}>
      <button
        onClick={() => setShowExportMenu(!showExportMenu)}
        disabled={isExporting}
        className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
      >
        {isExporting ? (
          <>
            <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-gray-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Exporting...
          </>
        ) : (
          <>
            <svg className="-ml-1 mr-2 h-4 w-4 text-gray-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Export
          </>
        )}
      </button>

      {showExportMenu && (
        <div className="absolute right-0 mt-2 w-56 rounded-md shadow-lg bg-white ring-1 ring-black ring-opacity-5 z-10">
          <div className="py-1" role="menu" aria-orientation="vertical">
            <button
              onClick={() => exportRoadmap('json')}
              className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-gray-900"
              role="menuitem"
            >
              <svg className="mr-3 h-4 w-4 text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Export as JSON
            </button>
            
            <button
              onClick={() => exportRoadmap('markdown')}
              className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-gray-900"
              role="menuitem"
            >
              <svg className="mr-3 h-4 w-4 text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Export as Markdown
            </button>

            <div className="border-t border-gray-100"></div>
            
            <button
              onClick={exportToDailyDashboard}
              className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-gray-900"
              role="menuitem"
            >
              <svg className="mr-3 h-4 w-4 text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3a2 2 0 012-2h4a2 2 0 012 2v4m-6 0V6a2 2 0 012-2h2a2 2 0 012 2v1m-6 0h6m-6 0l-.5 8.5A2 2 0 0011.5 21h1a2 2 0 002-1.5L14 11m-6 0h6" />
              </svg>
              Export to Daily Dashboard
            </button>

            <div className="border-t border-gray-100"></div>
            
            <button
              onClick={copyRoadmapLink}
              className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-gray-900"
              role="menuitem"
            >
              <svg className="mr-3 h-4 w-4 text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
              Copy Share Link
            </button>
          </div>
        </div>
      )}

      {/* Click outside to close menu */}
      {showExportMenu && (
        <div 
          className="fixed inset-0 z-0" 
          onClick={() => setShowExportMenu(false)}
        ></div>
      )}
    </div>
  )
}