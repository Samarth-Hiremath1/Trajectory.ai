'use client'

import { useState } from 'react'
import { ChevronLeftIcon, ChevronRightIcon } from '@heroicons/react/24/outline'

interface CalendarEvent {
  id: string
  title: string
  date: Date
  type: 'milestone' | 'learning' | 'practice' | 'review'
  description?: string
  completed?: boolean
  skipped?: boolean
  roadmapId?: string
  phaseNumber?: number
}

interface SimpleCalendarComponentProps {
  events: CalendarEvent[]
  onEventClick?: (event: CalendarEvent) => void
  onDateClick?: (date: Date) => void
  onEventComplete?: (eventId: string) => void
}

export function SimpleCalendarComponent({ 
  events, 
  onEventClick, 
  onDateClick, 
  onEventComplete
}: SimpleCalendarComponentProps) {
  const [currentDate, setCurrentDate] = useState(new Date())
  const [selectedDate, setSelectedDate] = useState<Date | null>(null)

  const today = new Date()
  const currentMonth = currentDate.getMonth()
  const currentYear = currentDate.getFullYear()

  // Get first day of the month and number of days
  const firstDayOfMonth = new Date(currentYear, currentMonth, 1)
  const lastDayOfMonth = new Date(currentYear, currentMonth + 1, 0)
  const firstDayWeekday = firstDayOfMonth.getDay()
  const daysInMonth = lastDayOfMonth.getDate()

  // Generate calendar days
  const calendarDays = []
  
  // Add empty cells for days before the first day of the month
  for (let i = 0; i < firstDayWeekday; i++) {
    calendarDays.push(null)
  }
  
  // Add days of the month
  for (let day = 1; day <= daysInMonth; day++) {
    calendarDays.push(new Date(currentYear, currentMonth, day))
  }

  const navigateMonth = (direction: 'prev' | 'next') => {
    setCurrentDate(prev => {
      const newDate = new Date(prev)
      if (direction === 'prev') {
        newDate.setMonth(prev.getMonth() - 1)
      } else {
        newDate.setMonth(prev.getMonth() + 1)
      }
      return newDate
    })
  }

  const getEventsForDate = (date: Date) => {
    return events.filter(event => 
      event.date.toDateString() === date.toDateString()
    )
  }

  const isToday = (date: Date) => {
    return date.toDateString() === today.toDateString()
  }

  const isSelected = (date: Date) => {
    return selectedDate && date.toDateString() === selectedDate.toDateString()
  }

  const handleDateClick = (date: Date) => {
    setSelectedDate(date)
    onDateClick?.(date)
  }

  const handleEventClick = (event: CalendarEvent, e: React.MouseEvent) => {
    e.stopPropagation()
    setSelectedDate(event.date)
    onEventClick?.(event)
  }

  const getEventTypeColor = (type: CalendarEvent['type']) => {
    switch (type) {
      case 'milestone':
        return 'bg-red-500'
      case 'learning':
        return 'bg-blue-500'
      case 'practice':
        return 'bg-green-500'
      case 'review':
        return 'bg-yellow-500'
      default:
        return 'bg-gray-500'
    }
  }

  const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ]

  const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

  return (
    <div className="bg-white rounded-lg shadow p-6 h-full flex flex-col">
      <div className="flex items-center justify-between mb-6 flex-shrink-0">
        <h3 className="text-lg font-semibold text-gray-900">
          Career Development Calendar
        </h3>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => navigateMonth('prev')}
            className="p-2 hover:bg-gray-100 rounded-full"
          >
            <ChevronLeftIcon className="h-5 w-5 text-gray-600" />
          </button>
          <h4 className="text-lg font-medium text-gray-900 min-w-[200px] text-center">
            {monthNames[currentMonth]} {currentYear}
          </h4>
          <button
            onClick={() => navigateMonth('next')}
            className="p-2 hover:bg-gray-100 rounded-full"
          >
            <ChevronRightIcon className="h-5 w-5 text-gray-600" />
          </button>
        </div>
      </div>

      {/* Calendar Grid */}
      <div className="grid grid-cols-7 gap-1 mb-4 flex-shrink-0">
        {/* Day headers */}
        {dayNames.map(day => (
          <div key={day} className="p-2 text-center text-sm font-medium text-gray-500">
            {day}
          </div>
        ))}
        
        {/* Calendar days */}
        {calendarDays.map((date, index) => {
          if (!date) {
            return <div key={index} className="p-2 h-24"></div>
          }

          const dayEvents = getEventsForDate(date)
          const isCurrentDay = isToday(date)
          const isSelectedDay = isSelected(date)

          return (
            <div
              key={date.toISOString()}
              onClick={() => handleDateClick(date)}
              className={`p-2 h-24 border border-gray-200 cursor-pointer hover:bg-gray-50 ${
                isCurrentDay ? 'bg-blue-50 border-blue-200' : ''
              } ${isSelectedDay ? 'bg-indigo-50 border-indigo-300' : ''}`}
            >
              <div className={`text-sm font-medium mb-1 ${
                isCurrentDay ? 'text-blue-600' : 'text-gray-900'
              }`}>
                {date.getDate()}
              </div>
              
              {/* Event indicators */}
              <div className="space-y-1">
                {dayEvents.slice(0, 2).map(event => (
                  <div
                    key={event.id}
                    onClick={(e) => handleEventClick(event, e)}
                    className={`text-xs px-1 py-0.5 rounded text-white truncate cursor-pointer hover:opacity-80 ${
                      getEventTypeColor(event.type)
                    } ${event.completed || event.skipped ? 'opacity-50 line-through' : ''}`}
                    title={event.title}
                  >
                    {event.title}
                  </div>
                ))}
                {dayEvents.length > 2 && (
                  <div className="text-xs text-gray-500">
                    +{dayEvents.length - 2} more
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* Selected date events */}
      {selectedDate && (
        <div className="border-t pt-4 flex-1 overflow-y-auto">
          <h4 className="font-medium text-gray-900 mb-3">
            Events for {selectedDate.toLocaleDateString()}
          </h4>
          <div className="space-y-2">
            {getEventsForDate(selectedDate).map(event => (
              <div
                key={event.id}
                className={`flex items-center justify-between p-3 border rounded-lg ${
                  event.completed || event.skipped ? 'bg-gray-50 opacity-75' : 'bg-white'
                }`}
              >
                <div className="flex items-center space-x-3">
                  <div className={`w-3 h-3 rounded-full ${getEventTypeColor(event.type)}`}></div>
                  <div>
                    <p className={`font-medium ${event.completed || event.skipped ? 'line-through text-gray-500' : 'text-gray-900'}`}>
                      {event.title}
                    </p>
                    {event.description && (
                      <p className="text-sm text-gray-600">{event.description}</p>
                    )}
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  {!event.completed && !event.skipped && onEventComplete && (
                    <button
                      onClick={() => onEventComplete(event.id)}
                      className="text-sm bg-green-100 hover:bg-green-200 text-green-700 px-2 py-1 rounded"
                    >
                      Complete
                    </button>
                  )}
                  {event.completed && (
                    <span className="text-sm text-green-600 font-medium">
                      ✓ Completed
                    </span>
                  )}
                  {event.skipped && (
                    <span className="text-sm text-gray-600 font-medium">
                      ⊘ Skipped
                    </span>
                  )}
                  <button
                    onClick={() => onEventClick?.(event)}
                    className="text-sm bg-gray-100 hover:bg-gray-200 text-gray-700 px-2 py-1 rounded"
                  >
                    View
                  </button>
                </div>
              </div>
            ))}
            {getEventsForDate(selectedDate).length === 0 && (
              <p className="text-gray-500 text-sm">No events scheduled for this date.</p>
            )}
          </div>
        </div>
      )}


    </div>
  )
}