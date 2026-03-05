import React from 'react'
import { Handle, Position } from '@xyflow/react'

function PICNode({ data, selected, id }) {
  const handleStaffDragStart = (event) => {
    if (!data.assignedStaff) return
    event.stopPropagation()
    const staffData = {
      name: data.assignedStaff,
      staffId: data.staffId,
      firmId: data.staffFirmId,
      firmName: data.staffFirmName,
      fromNodeId: id
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

  const firmColor = data.staffFirmId && data.firmColorMap ? data.firmColorMap[data.staffFirmId] : null
  const staffTextStyle = firmColor?.useInline ? firmColor.textStyle : {}
  const staffTextColor = firmColor ? (firmColor.useInline ? '' : firmColor.text) : 'text-red-700'

  return (
    <div
      className={`w-52 min-h-[70px] p-3 rounded-xl border-2 shadow-md relative bg-white ${
        selected ? 'border-red-500 ring-2 ring-red-300' : 'border-gray-800'
      }`}
      style={{
        borderStyle: 'solid',
        background: 'linear-gradient(135deg, #fff 0%, #f8f8f8 100%)'
      }}
    >
      {data.canDelete && (
        <button
          onClick={(e) => { e.stopPropagation(); data.onDeleteNode?.(id) }}
          className="absolute -top-2 -right-2 w-5 h-5 bg-red-600 text-white rounded-full text-xs font-bold hover:bg-red-700 flex items-center justify-center shadow"
          title="Delete PIC node"
        >
          ×
        </button>
      )}
      <Handle type="target" position={Position.Top} id="top" className="w-3 h-3 bg-gray-700 border-2 border-white" />
      <Handle type="target" position={Position.Left} id="left" className="w-3 h-3 bg-gray-700 border-2 border-white" />
      <Handle type="target" position={Position.Right} id="right" className="w-3 h-3 bg-gray-700 border-2 border-white" />

      <div className="text-center">
        <div className="text-[10px] text-gray-500 font-bold uppercase tracking-wide mb-1">
          {data.isKeyIndividual && <span className="text-red-600 mr-0.5">★</span>}
          Principal-in-Charge
        </div>
        <div className="font-semibold text-gray-900 text-sm leading-tight break-words">
          {data.role || 'Principal-in-Charge'}
        </div>
        {data.assignedStaff && (
          <div
            className={`mt-1 text-xs font-medium border-t pt-1 cursor-grab hover:opacity-75 rounded px-1 transition-colors ${staffTextColor} border-gray-300`}
            style={staffTextStyle}
            draggable
            onDragStart={handleStaffDragStart}
            title="Drag to reassign to another role"
          >
            {data.isKeyIndividual && <span className="text-red-600 mr-0.5">★</span>}
            {resolveStaffName(data.assignedStaff, data.staffId)}
            {data.staffFirmName && (
              <div className="text-[9px] opacity-70 font-normal">{data.staffFirmName}</div>
            )}
          </div>
        )}
        <div className="flex gap-1 justify-center mt-2">
          {data.assignedStaff && (
            <button
              onClick={(e) => { e.stopPropagation(); data.onToggleKeyIndividual?.(id) }}
              className={`text-[9px] px-2 py-0.5 rounded transition-colors ${
                data.isKeyIndividual ? 'bg-red-100 text-red-600' : 'bg-gray-100 text-gray-500 hover:text-red-500'
              }`}
              title="Toggle Key Individual"
            >★ Key</button>
          )}
        </div>
      </div>

      <Handle type="source" position={Position.Bottom} id="bottom" className="w-3 h-3 bg-gray-700 border-2 border-white" />
      <Handle type="source" position={Position.Left} id="left-source" className="w-3 h-3 bg-gray-700 border-2 border-white" />
      <Handle type="source" position={Position.Right} id="right-source" className="w-3 h-3 bg-gray-700 border-2 border-white" />
    </div>
  )
}

export default PICNode
