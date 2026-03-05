import React, { useState } from 'react'
import { Handle, Position } from '@xyflow/react'

function DisciplineBlockNode({ data, selected, id }) {
  const [showColorPicker, setShowColorPicker] = useState(false)

  const handleStaffDragStart = (event, index) => {
    event.stopPropagation()
    const staffEntry = data.staffList?.[index]
    if (!staffEntry) return
    const staffData = {
      name: staffEntry.name,
      staffId: staffEntry.id,
      firmId: staffEntry.firm_id,
      firmName: staffEntry.firm_name,
      fromNodeId: id,
      fromIndex: index
    }
    event.dataTransfer.setData('application/staff-reassign', JSON.stringify(staffData))
    event.dataTransfer.effectAllowed = 'move'
  }

  const resolveStaffName = (name, staffId) => {
    if ((data.showPostNominal || data.showMiddleName) && staffId && data.staffDisplayMap && data.staffDisplayMap[staffId]) {
      return data.staffDisplayMap[staffId]
    }
    return name
  }

  const getFirmAbbrev = (firmId) => {
    if (!firmId || !data.firmAbbrevMap) return null
    return data.firmAbbrevMap[firmId] || null
  }

  const firmColor = data.headerColor || '#991b1b'
  const nodeWidth = data.width || 240
  const staffList = data.staffList || []
  const lead = staffList.length > 0 ? staffList[0] : null
  const teamMembers = staffList.slice(1)
  const keyIndividuals = data.keyIndividuals || {}

  const PRESET_COLORS = ['#991b1b', '#1e3a5f', '#065f46', '#92400e', '#5b21b6', '#9f1239', '#374151', '#0f766e', '#1d4ed8', '#6d28d9']

  return (
    <div
      className={`bg-white rounded shadow-md relative ${selected ? 'ring-2 ring-red-400' : ''}`}
      style={{ border: `2px solid ${firmColor}`, width: `${nodeWidth}px` }}
    >
      {data.canDelete && (
        <button
          onClick={(e) => { e.stopPropagation(); data.onDeleteNode?.(id) }}
          className="absolute -top-2 -right-2 w-5 h-5 bg-red-600 text-white rounded-full text-xs font-bold hover:bg-red-700 flex items-center justify-center shadow z-10"
          title="Delete this block"
        >
          ×
        </button>
      )}
      <Handle type="target" position={Position.Top} id="top" className="w-3 h-3 bg-red-600 border-2 border-white" />
      <Handle type="target" position={Position.Left} id="left" className="w-3 h-3 bg-red-600 border-2 border-white" />
      <Handle type="target" position={Position.Right} id="right" className="w-3 h-3 bg-red-600 border-2 border-white" />

      <div
        className="px-3 py-1.5 text-white text-xs font-bold uppercase tracking-wide text-center flex items-center justify-center gap-1"
        style={{ backgroundColor: firmColor }}
      >
        <span className="flex-1">{data.role || 'DISCIPLINE'}</span>
        <button
          onClick={(e) => { e.stopPropagation(); setShowColorPicker(!showColorPicker) }}
          className="w-4 h-4 rounded-full border border-white/50 flex-shrink-0 hover:scale-110 transition-transform"
          style={{ backgroundColor: 'rgba(255,255,255,0.3)' }}
          title="Change color"
        >
          <span className="text-[8px]">🎨</span>
        </button>
      </div>

      {showColorPicker && (
        <div className="absolute top-8 right-0 z-50 bg-white rounded shadow-lg border border-gray-200 p-2" style={{ width: '160px' }}>
          <div className="flex flex-wrap gap-1 mb-2">
            {PRESET_COLORS.map(color => (
              <button
                key={color}
                onClick={(e) => { e.stopPropagation(); data.onChangeNodeColor?.(id, color); setShowColorPicker(false) }}
                className="w-5 h-5 rounded-full border-2 hover:scale-110 transition-transform"
                style={{ backgroundColor: color, borderColor: firmColor === color ? '#000' : '#d1d5db' }}
              />
            ))}
          </div>
          <input
            type="color"
            value={firmColor}
            onChange={(e) => { e.stopPropagation(); data.onChangeNodeColor?.(id, e.target.value) }}
            onClick={(e) => e.stopPropagation()}
            className="w-full h-6 cursor-pointer rounded border border-gray-300"
            title="Custom color"
          />
        </div>
      )}

      <div className="px-3 py-2 text-xs">
        {lead ? (
          <div className="mb-1">
            <span className="font-bold text-gray-800">Lead - </span>
            <span
              className="font-semibold text-gray-900 cursor-grab hover:opacity-75"
              draggable
              onDragStart={(e) => handleStaffDragStart(e, 0)}
            >
              {keyIndividuals[lead.id || 0] && <span className="text-red-600 mr-0.5">★</span>}
              {resolveStaffName(lead.name, lead.id)}
              {lead.firm_id && getFirmAbbrev(lead.firm_id) && (
                <span className="text-gray-500"> ({getFirmAbbrev(lead.firm_id)})</span>
              )}
            </span>
            <div className="flex gap-0.5 mt-0.5">
              <button
                onClick={(e) => { e.stopPropagation(); data.onToggleKeyIndividual?.(id, lead.id || 0) }}
                className={`text-[9px] px-1 py-0 rounded ${keyIndividuals[lead.id || 0] ? 'text-red-600' : 'text-gray-400 hover:text-red-500'}`}
                title="Toggle Key Individual"
              >★</button>
              <button
                onClick={(e) => { e.stopPropagation(); data.onRemoveStaffFromList?.(id, 0) }}
                className="text-red-400 hover:text-red-600 text-[9px] px-1"
                title="Remove"
              >×</button>
            </div>
          </div>
        ) : (
          <div className="text-gray-400 italic text-center py-1">Drop staff here</div>
        )}

        {teamMembers.length > 0 && (
          <div className="border-t border-gray-200 pt-1 mt-1 space-y-0.5">
            {teamMembers.map((member, idx) => {
              const actualIndex = idx + 1
              const staffName = resolveStaffName(member.name, member.id)
              const abbrev = member.firm_id ? getFirmAbbrev(member.firm_id) : null
              const isKey = keyIndividuals[member.id || 0]
              return (
                <div key={actualIndex} className="flex items-start justify-between group">
                  <span
                    className="text-gray-700 cursor-grab hover:opacity-75 flex-1"
                    draggable
                    onDragStart={(e) => handleStaffDragStart(e, actualIndex)}
                  >
                    {isKey && <span className="text-red-600 mr-0.5">★</span>}
                    {staffName}
                    {abbrev && <span className="text-gray-500"> ({abbrev})</span>}
                  </span>
                  <div className="flex gap-0 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={(e) => { e.stopPropagation(); data.onToggleKeyIndividual?.(id, member.id || 0) }}
                      className={`text-[9px] px-0.5 ${isKey ? 'text-red-600' : 'text-gray-400 hover:text-red-500'}`}
                      title="Toggle Key Individual"
                    >★</button>
                    <button
                      onClick={(e) => { e.stopPropagation(); data.onRemoveStaffFromList?.(id, actualIndex) }}
                      className="text-red-400 hover:text-red-600 text-[9px] px-0.5"
                      title="Remove"
                    >×</button>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      <div
        data-resize="true"
        className="nodrag nopan absolute bottom-0 right-0 w-5 h-5 cursor-se-resize"
        style={{ background: 'linear-gradient(135deg, transparent 50%, #9ca3af 50%)', borderBottomRightRadius: '4px' }}
        onMouseDown={(e) => {
          e.preventDefault()
          e.stopPropagation()
          const startX = e.clientX
          const origW = nodeWidth
          const onMove = (ev) => {
            const newW = Math.max(180, origW + (ev.clientX - startX))
            data.onResizeNode?.(id, newW, null)
          }
          const onUp = () => {
            document.removeEventListener('mousemove', onMove)
            document.removeEventListener('mouseup', onUp)
          }
          document.addEventListener('mousemove', onMove)
          document.addEventListener('mouseup', onUp)
        }}
      />

      <Handle type="source" position={Position.Bottom} id="bottom" className="w-3 h-3 bg-red-600 border-2 border-white" />
      <Handle type="source" position={Position.Left} id="left-source" className="w-3 h-3 bg-red-600 border-2 border-white" />
      <Handle type="source" position={Position.Right} id="right-source" className="w-3 h-3 bg-red-600 border-2 border-white" />
    </div>
  )
}

export default DisciplineBlockNode
