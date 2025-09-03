'use client'

import { useState, useEffect, useCallback } from 'react'
import { PlusIcon, PencilIcon, TrashIcon, TagIcon } from '@heroicons/react/24/outline'

interface Note {
  id: string
  title: string
  content: string
  tags: string[]
  category: 'general' | 'learning' | 'interview' | 'networking' | 'goal'
  roadmapId?: string
  phaseNumber?: number
  createdAt: Date
  updatedAt: Date
  pinned: boolean
}

interface NotesComponentProps {
  userId: string
  roadmapId?: string
  phaseNumber?: number
}

export function NotesComponent({ userId, roadmapId, phaseNumber }: NotesComponentProps) {
  const [notes, setNotes] = useState<Note[]>([])
  const [showAddForm, setShowAddForm] = useState(false)
  const [editingNote, setEditingNote] = useState<Note | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [filterCategory, setFilterCategory] = useState<Note['category'] | 'all'>('all')
  const [loading, setLoading] = useState(true)

  const [newNote, setNewNote] = useState({
    title: '',
    content: '',
    category: 'general' as Note['category'],
    tags: [] as string[],
    tagInput: ''
  })

  const loadNotes = useCallback(async () => {
    try {
      setLoading(true)
      // In a real app, this would be an API call
      const savedNotes = localStorage.getItem(`notes-${userId}`)
      if (savedNotes) {
        const parsedNotes = JSON.parse(savedNotes).map((note: any) => ({
          ...note,
          createdAt: new Date(note.createdAt),
          updatedAt: new Date(note.updatedAt)
        }))
        setNotes(parsedNotes)
      }
    } catch (error) {
      console.error('Error loading notes:', error)
    } finally {
      setLoading(false)
    }
  }, [userId])

  useEffect(() => {
    loadNotes()
  }, [loadNotes])

  const saveNotes = (updatedNotes: Note[]) => {
    localStorage.setItem(`notes-${userId}`, JSON.stringify(updatedNotes))
    setNotes(updatedNotes)
  }

  const handleAddNote = () => {
    if (!newNote.title.trim() || !newNote.content.trim()) return

    const note: Note = {
      id: Date.now().toString(),
      title: newNote.title,
      content: newNote.content,
      category: newNote.category,
      tags: newNote.tags,
      roadmapId,
      phaseNumber,
      createdAt: new Date(),
      updatedAt: new Date(),
      pinned: false
    }

    const updatedNotes = [note, ...notes]
    saveNotes(updatedNotes)

    setNewNote({
      title: '',
      content: '',
      category: 'general',
      tags: [],
      tagInput: ''
    })
    setShowAddForm(false)
  }

  const handleEditNote = (note: Note) => {
    setEditingNote(note)
    setNewNote({
      title: note.title,
      content: note.content,
      category: note.category,
      tags: note.tags,
      tagInput: ''
    })
    setShowAddForm(true)
  }

  const handleUpdateNote = () => {
    if (!editingNote || !newNote.title.trim() || !newNote.content.trim()) return

    const updatedNote: Note = {
      ...editingNote,
      title: newNote.title,
      content: newNote.content,
      category: newNote.category,
      tags: newNote.tags,
      updatedAt: new Date()
    }

    const updatedNotes = notes.map(note => 
      note.id === editingNote.id ? updatedNote : note
    )
    saveNotes(updatedNotes)

    setEditingNote(null)
    setNewNote({
      title: '',
      content: '',
      category: 'general',
      tags: [],
      tagInput: ''
    })
    setShowAddForm(false)
  }

  const handleDeleteNote = (noteId: string) => {
    if (confirm('Are you sure you want to delete this note?')) {
      const updatedNotes = notes.filter(note => note.id !== noteId)
      saveNotes(updatedNotes)
    }
  }

  const handleTogglePin = (noteId: string) => {
    const updatedNotes = notes.map(note =>
      note.id === noteId ? { ...note, pinned: !note.pinned } : note
    )
    saveNotes(updatedNotes)
  }

  const handleAddTag = () => {
    if (newNote.tagInput.trim() && !newNote.tags.includes(newNote.tagInput.trim())) {
      setNewNote(prev => ({
        ...prev,
        tags: [...prev.tags, prev.tagInput.trim()],
        tagInput: ''
      }))
    }
  }

  const handleRemoveTag = (tagToRemove: string) => {
    setNewNote(prev => ({
      ...prev,
      tags: prev.tags.filter(tag => tag !== tagToRemove)
    }))
  }

  const filteredNotes = notes.filter(note => {
    const matchesSearch = note.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         note.content.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         note.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()))
    
    const matchesCategory = filterCategory === 'all' || note.category === filterCategory
    
    const matchesContext = !roadmapId || note.roadmapId === roadmapId
    
    return matchesSearch && matchesCategory && matchesContext
  }).sort((a, b) => {
    // Pinned notes first, then by updated date
    if (a.pinned && !b.pinned) return -1
    if (!a.pinned && b.pinned) return 1
    return b.updatedAt.getTime() - a.updatedAt.getTime()
  })

  const getCategoryColor = (category: Note['category']) => {
    switch (category) {
      case 'learning':
        return 'bg-blue-100 text-blue-800'
      case 'interview':
        return 'bg-red-100 text-red-800'
      case 'networking':
        return 'bg-green-100 text-green-800'
      case 'goal':
        return 'bg-purple-100 text-purple-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getCategoryIcon = (category: Note['category']) => {
    switch (category) {
      case 'learning':
        return '📚'
      case 'interview':
        return '💼'
      case 'networking':
        return '🤝'
      case 'goal':
        return '🎯'
      default:
        return '📝'
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 rounded w-1/4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow p-6 h-full flex flex-col">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Career Notes</h3>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="bg-indigo-600 hover:bg-indigo-700 text-white px-3 py-2 rounded-md text-sm font-medium flex items-center space-x-2"
        >
          <PlusIcon className="w-4 h-4" />
          <span>Add Note</span>
        </button>
      </div>

      {/* Search and Filter */}
      <div className="flex flex-col sm:flex-row gap-4 mb-6">
        <div className="flex-1">
          <input
            type="text"
            placeholder="Search notes..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
        <select
          value={filterCategory}
          onChange={(e) => setFilterCategory(e.target.value as any)}
          className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
        >
          <option value="all">All Categories</option>
          <option value="general">General</option>
          <option value="learning">Learning</option>
          <option value="interview">Interview</option>
          <option value="networking">Networking</option>
          <option value="goal">Goals</option>
        </select>
      </div>

      {/* Add/Edit Note Form */}
      {showAddForm && (
        <div className="border border-gray-200 rounded-lg p-4 mb-6 bg-gray-50 flex-shrink-0">
          <h4 className="font-medium text-gray-900 mb-3">
            {editingNote ? 'Edit Note' : 'Add New Note'}
          </h4>
          
          <div className="space-y-4">
            <input
              type="text"
              placeholder="Note title..."
              value={newNote.title}
              onChange={(e) => setNewNote(prev => ({ ...prev, title: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            
            <textarea
              placeholder="Write your note here..."
              value={newNote.content}
              onChange={(e) => setNewNote(prev => ({ ...prev, content: e.target.value }))}
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
            
            <div className="flex flex-col sm:flex-row gap-4">
              <select
                value={newNote.category}
                onChange={(e) => setNewNote(prev => ({ ...prev, category: e.target.value as Note['category'] }))}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="general">General</option>
                <option value="learning">Learning</option>
                <option value="interview">Interview</option>
                <option value="networking">Networking</option>
                <option value="goal">Goals</option>
              </select>
              
              <div className="flex-1 flex space-x-2">
                <input
                  type="text"
                  placeholder="Add tag..."
                  value={newNote.tagInput}
                  onChange={(e) => setNewNote(prev => ({ ...prev, tagInput: e.target.value }))}
                  onKeyPress={(e) => e.key === 'Enter' && handleAddTag()}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
                <button
                  onClick={handleAddTag}
                  className="px-3 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-md"
                >
                  Add
                </button>
              </div>
            </div>
            
            {newNote.tags.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {newNote.tags.map(tag => (
                  <span
                    key={tag}
                    className="inline-flex items-center px-2 py-1 text-xs bg-indigo-100 text-indigo-800 rounded-full"
                  >
                    {tag}
                    <button
                      onClick={() => handleRemoveTag(tag)}
                      className="ml-1 text-indigo-600 hover:text-indigo-800"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            )}
            
            <div className="flex justify-end space-x-2">
              <button
                onClick={() => {
                  setShowAddForm(false)
                  setEditingNote(null)
                  setNewNote({
                    title: '',
                    content: '',
                    category: 'general',
                    tags: [],
                    tagInput: ''
                  })
                }}
                className="px-4 py-2 text-gray-700 bg-gray-200 hover:bg-gray-300 rounded-md"
              >
                Cancel
              </button>
              <button
                onClick={editingNote ? handleUpdateNote : handleAddNote}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md"
              >
                {editingNote ? 'Update' : 'Add'} Note
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Notes List */}
      <div className="flex-1 min-h-0">
        <div className="space-y-4 h-full overflow-y-auto">
          {filteredNotes.map(note => (
            <div
              key={note.id}
              className={`border rounded-lg p-4 ${note.pinned ? 'border-yellow-300 bg-yellow-50' : 'border-gray-200 bg-white'}`}
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <span className="text-lg">{getCategoryIcon(note.category)}</span>
                  <h4 className="font-medium text-gray-900">{note.title}</h4>
                  <span className={`px-2 py-1 text-xs rounded-full ${getCategoryColor(note.category)}`}>
                    {note.category}
                  </span>
                  {note.pinned && (
                    <span className="text-yellow-500">📌</span>
                  )}
                </div>
                
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => handleTogglePin(note.id)}
                    className="text-gray-400 hover:text-yellow-500"
                    title={note.pinned ? 'Unpin' : 'Pin'}
                  >
                    📌
                  </button>
                  <button
                    onClick={() => handleEditNote(note)}
                    className="text-gray-400 hover:text-indigo-600"
                  >
                    <PencilIcon className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDeleteNote(note.id)}
                    className="text-gray-400 hover:text-red-600"
                  >
                    <TrashIcon className="w-4 h-4" />
                  </button>
                </div>
              </div>
              
              <p className="text-gray-700 mb-3 whitespace-pre-wrap">{note.content}</p>
              
              {note.tags.length > 0 && (
                <div className="flex flex-wrap gap-1 mb-2">
                  {note.tags.map(tag => (
                    <span
                      key={tag}
                      className="inline-flex items-center px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded"
                    >
                      <TagIcon className="w-3 h-3 mr-1" />
                      {tag}
                    </span>
                  ))}
                </div>
              )}
              
              <div className="text-xs text-gray-500">
                Created: {note.createdAt.toLocaleDateString()} • 
                Updated: {note.updatedAt.toLocaleDateString()}
              </div>
            </div>
          ))}
          
          {filteredNotes.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              {searchTerm || filterCategory !== 'all' 
                ? 'No notes match your search criteria.' 
                : 'No notes yet. Add your first note to get started!'}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}