import React from 'react'
import { Handle, Position } from '@xyflow/react'

function SectionHeaderNode({ data, selected, id }) {
  const bgColor = data.bgColor || '#991b1b'
  const width = data.width || 600

  return (
    <div
      className={`relative ${selected ? 'ring-2 ring-blue-400' : ''}`}
      style={{
        width: `${width}px`,
        backgroundColor: bgColor,
        borderRadius: '4px',
        padding: '6px 16px',
        textAlign: 'center',
        minHeight: '28px',
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
      <Handle type="target" position={Position.Top} id="top" className="w-3 h-3 bg-blue-600 border-2 border-white" />
      <Handle type="target" position={Position.Left} id="left" className="w-3 h-3 bg-blue-600 border-2 border-white" />
      <Handle type="target" position={Position.Right} id="right" className="w-3 h-3 bg-blue-600 border-2 border-white" />

      <span className="text-white font-bold text-sm uppercase tracking-wider">
        {data.label || 'SECTION HEADER'}
      </span>

      <div
        data-resize="true"
        className="absolute top-0 right-0 w-4 h-full cursor-ew-resize"
        style={{ background: 'transparent' }}
        onMouseDown={(e) => {
          e.preventDefault()
          e.stopPropagation()
          const startX = e.clientX
          const origW = width
          const onMove = (ev) => {
            const newWidth = Math.max(200, origW + (ev.clientX - startX))
            data.onResizeHeader?.(id, newWidth)
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
