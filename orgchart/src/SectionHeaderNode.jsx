import React, { useState } from 'react'
import { Handle, Position } from '@xyflow/react'

function SectionHeaderNode({ data, selected, id }) {
  const [showColorPicker, setShowColorPicker] = useState(false)
  const bgColor = data.bgColor || '#991b1b'
  const width = data.width || 600
  const height = data.height || 36

  const PRESET_COLORS = ['#991b1b', '#1e3a5f', '#065f46', '#92400e', '#5b21b6', '#9f1239', '#374151', '#0f766e', '#1d4ed8', '#6d28d9']

  return (
    <div
      className={`relative ${selected ? 'ring-2 ring-blue-400' : ''}`}
      style={{
        width: `${width}px`,
        height: `${height}px`,
        backgroundColor: bgColor,
        borderRadius: '4px',
        padding: '6px 16px',
        textAlign: 'center',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
    >
      {data.canDelete && (
        <button
          onClick={(e) => { e.stopPropagation(); data.onDeleteNode?.(id) }}
          className="absolute -top-2 -right-2 w-5 h-5 bg-red-600 text-white rounded-full text-xs font-bold hover:bg-red-700 flex items-center justify-center shadow z-10"
          title="Delete this header"
        >
          ×
        </button>
      )}

      <button
        onClick={(e) => { e.stopPropagation(); setShowColorPicker(!showColorPicker) }}
        className="absolute top-1 left-2 w-4 h-4 rounded-full border border-white/50 hover:scale-110 transition-transform z-10"
        style={{ backgroundColor: 'rgba(255,255,255,0.3)' }}
        title="Change color"
      >
        <span className="text-[8px]">🎨</span>
      </button>

      {showColorPicker && (
        <div className="absolute top-8 left-0 z-50 bg-white rounded shadow-lg border border-gray-200 p-2" style={{ width: '160px' }}>
          <div className="flex flex-wrap gap-1 mb-2">
            {PRESET_COLORS.map(color => (
              <button
                key={color}
                onClick={(e) => { e.stopPropagation(); data.onChangeNodeColor?.(id, color); setShowColorPicker(false) }}
                className="w-5 h-5 rounded-full border-2 hover:scale-110 transition-transform"
                style={{ backgroundColor: color, borderColor: bgColor === color ? '#000' : '#d1d5db' }}
              />
            ))}
          </div>
          <input
            type="color"
            value={bgColor}
            onChange={(e) => { e.stopPropagation(); data.onChangeNodeColor?.(id, e.target.value) }}
            onClick={(e) => e.stopPropagation()}
            className="w-full h-6 cursor-pointer rounded border border-gray-300"
            title="Custom color"
          />
        </div>
      )}

      <Handle type="target" position={Position.Top} id="top" className="w-3 h-3 bg-blue-600 border-2 border-white" />
      <Handle type="target" position={Position.Left} id="left" className="w-3 h-3 bg-blue-600 border-2 border-white" />
      <Handle type="target" position={Position.Right} id="right" className="w-3 h-3 bg-blue-600 border-2 border-white" />

      <span className="text-white font-bold text-sm uppercase tracking-wider">
        {data.label || 'SECTION HEADER'}
      </span>

      <div
        data-resize="true"
        className="nodrag nopan absolute bottom-0 right-0 w-5 h-5 cursor-se-resize"
        style={{ background: 'linear-gradient(135deg, transparent 50%, rgba(255,255,255,0.5) 50%)', borderBottomRightRadius: '4px' }}
        onMouseDown={(e) => {
          e.preventDefault()
          e.stopPropagation()
          const startX = e.clientX
          const startY = e.clientY
          const origW = width
          const origH = height
          const onMove = (ev) => {
            const newWidth = Math.max(200, origW + (ev.clientX - startX))
            const newHeight = Math.max(24, origH + (ev.clientY - startY))
            data.onResizeNode?.(id, newWidth, newHeight)
          }
          const onUp = () => {
            document.removeEventListener('mousemove', onMove)
            document.removeEventListener('mouseup', onUp)
          }
          document.addEventListener('mousemove', onMove)
          document.addEventListener('mouseup', onUp)
        }}
      />

      <Handle type="source" position={Position.Bottom} id="bottom" className="w-3 h-3 bg-blue-600 border-2 border-white" />
      <Handle type="source" position={Position.Left} id="left-source" className="w-3 h-3 bg-blue-600 border-2 border-white" />
      <Handle type="source" position={Position.Right} id="right-source" className="w-3 h-3 bg-blue-600 border-2 border-white" />
    </div>
  )
}

export default SectionHeaderNode
