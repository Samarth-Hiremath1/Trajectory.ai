'use client'

import { useState, useRef, useEffect } from 'react'
import { ChevronDownIcon } from '@heroicons/react/24/outline'

type TaskStatus = 'pending' | 'in_progress' | 'completed' | 'skipped'

interface StatusOption {
  value: TaskStatus
  label: string
  color: string
  bgColor: string
}

interface StatusDropdownProps {
  value: TaskStatus
  onChange: (status: TaskStatus) => void
  className?: string
}

const statusOptions: StatusOption[] = [
  { value: 'pending', label: 'Pending', color: 'text-gray-600', bgColor: 'bg-gray-400' },
  { value: 'in_progress', label: 'In Progress', color: 'text-yellow-600', bgColor: 'bg-yellow-400' },
  { value: 'completed', label: 'Complete', color: 'text-green-600', bgColor: 'bg-green-400' },
  { value: 'skipped', label: 'Skip', color: 'text-gray-800', bgColor: 'bg-black' }
]

export function StatusDropdown({ value, onChange, className = '' }: StatusDropdownProps) {
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const currentOption = statusOptions.find(option => option.value === value) || statusOptions[0]

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleSelect = (status: TaskStatus) => {
    onChange(status)
    setIsOpen(false)
  }

  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-2 bg-white border border-gray-300 rounded-md px-3 py-2 text-sm font-medium hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 min-w-[140px]"
      >
        <div className={`w-3 h-3 rounded-full ${currentOption.bgColor}`} />
        <span className={currentOption.color}>{currentOption.label}</span>
        <ChevronDownIcon className="w-4 h-4 text-gray-400 ml-auto" />
      </button>

      {isOpen && (
        <div className="absolute z-50 mt-1 w-full bg-white border border-gray-300 rounded-md shadow-lg">
          <div className="py-1">
            {statusOptions.map((option) => (
              <button
                key={option.value}
                onClick={() => handleSelect(option.value)}
                className={`flex items-center space-x-2 w-full px-3 py-2 text-sm hover:bg-gray-100 ${
                  option.value === value ? 'bg-gray-50' : ''
                }`}
              >
                <div className={`w-3 h-3 rounded-full ${option.bgColor}`} />
                <span className={option.color}>{option.label}</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}