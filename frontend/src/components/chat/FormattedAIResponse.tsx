'use client'

import React from 'react'

interface FormattedAIResponseProps {
  content: string
}

export function FormattedAIResponse({ content }: FormattedAIResponseProps) {
  // Split content into paragraphs and format
  const formatContent = (text: string) => {
    // Split by double newlines to get paragraphs
    const paragraphs = text.split('\n\n').filter(p => p.trim())
    
    return paragraphs.map((paragraph, index) => {
      const trimmedParagraph = paragraph.trim()
      
      // Check if it's a header (starts with ##, ###, etc.)
      if (trimmedParagraph.match(/^#{1,3}\s+/)) {
        const headerText = trimmedParagraph.replace(/^#{1,3}\s+/, '')
        return (
          <h3 key={index} className="font-semibold text-gray-900 mt-4 mb-2 first:mt-0">
            {headerText}
          </h3>
        )
      }
      
      // Check if it's a bullet list
      if (trimmedParagraph.includes('\n-') || trimmedParagraph.startsWith('-')) {
        const listItems = trimmedParagraph
          .split('\n')
          .filter(line => line.trim().startsWith('-'))
          .map(line => line.replace(/^-\s*/, '').trim())
        
        return (
          <ul key={index} className="list-disc list-inside space-y-1 my-2">
            {listItems.map((item, itemIndex) => (
              <li key={itemIndex} className="text-gray-800">
                {formatInlineText(item)}
              </li>
            ))}
          </ul>
        )
      }
      
      // Check if it's a numbered list
      if (trimmedParagraph.match(/^\d+\./)) {
        const listItems = trimmedParagraph
          .split('\n')
          .filter(line => line.trim().match(/^\d+\./))
          .map(line => line.replace(/^\d+\.\s*/, '').trim())
        
        return (
          <ol key={index} className="list-decimal list-inside space-y-1 my-2">
            {listItems.map((item, itemIndex) => (
              <li key={itemIndex} className="text-gray-800">
                {formatInlineText(item)}
              </li>
            ))}
          </ol>
        )
      }
      
      // Regular paragraph
      return (
        <p key={index} className="text-gray-800 mb-3 leading-relaxed">
          {formatInlineText(trimmedParagraph)}
        </p>
      )
    })
  }
  
  // Format inline text with bold, italic, etc.
  const formatInlineText = (text: string) => {
    // Split by bold markers (**text**)
    const parts = text.split(/(\*\*[^*]+\*\*)/g)
    
    return parts.map((part, index) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        const boldText = part.slice(2, -2)
        return (
          <strong key={index} className="font-semibold text-gray-900">
            {boldText}
          </strong>
        )
      }
      
      // Check for italic (*text*)
      if (part.startsWith('*') && part.endsWith('*') && !part.startsWith('**')) {
        const italicText = part.slice(1, -1)
        return (
          <em key={index} className="italic">
            {italicText}
          </em>
        )
      }
      
      // Check for code (`code`)
      if (part.startsWith('`') && part.endsWith('`')) {
        const codeText = part.slice(1, -1)
        return (
          <code key={index} className="bg-gray-200 px-1 py-0.5 rounded text-sm font-mono">
            {codeText}
          </code>
        )
      }
      
      return part
    })
  }
  
  return (
    <div className="prose prose-sm max-w-none">
      {formatContent(content)}
    </div>
  )
}