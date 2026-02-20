import React from 'react'
import { Handle, Position } from '@xyflow/react'

function CustomNode({ data, selected, id }) {
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

  const handleAddTeamMember = (event) => {
    event.stopPropagation()
    if (data.onAddTeamMember) {
      data.onAddTeamMember(id)
    }
  }

  const handleAddDPM = (event) => {
    event.stopPropagation()
    if (data.onAddDPM) {
      data.onAddDPM(id)
    }
  }

  const handleDelete = (event) => {
    event.stopPropagation()
    if (data.onDeleteNode) {
      data.onDeleteNode(id)
    }
  }

  const handleAddBranch = (event) => {
    event.stopPropagation()
    if (data.onAddChildBranch) {
      data.onAddChildBranch(id)
    }
  }

  const isTaskLead = data.isTaskLead
  const isTeamMember = data.isTeamMember

  const firmColor = data.staffFirmId && data.firmColorMap ? data.firmColorMap[data.staffFirmId] : null
  const useInline = firmColor?.useInline

  let borderClass = 'border-gray-900'
  let bgClass = 'bg-gray-50'
  let inlineStyle = {}
  
  if (selected) {
    borderClass = 'border-red-500 shadow-lg ring-2 ring-red-300'
  } else if (data.assignedStaff && firmColor) {
    if (useInline) {
      borderClass = ''
      bgClass = ''
      inlineStyle = { ...firmColor.borderStyle, ...firmColor.bgStyle }
    } else {
      borderClass = firmColor.border
      bgClass = firmColor.bg
    }
  } else if (isTaskLead) {
    borderClass = 'border-red-600'
    bgClass = data.assignedStaff ? 'bg-red-50' : 'bg-white'
  } else if (isTeamMember) {
    borderClass = 'border-gray-600'
    bgClass = data.assignedStaff ? 'bg-gray-100' : 'bg-gray-50'
  } else if (data.assignedStaff) {
    bgClass = 'bg-red-50'
  }

  const staffTextColor = firmColor ? (useInline ? '' : firmColor.text) : 'text-red-700'
  const staffTextStyle = firmColor?.useInline ? firmColor.textStyle : {}

  return (
    <div
      className={`w-48 min-h-[70px] p-3 rounded border-2 shadow-md relative ${borderClass} ${bgClass}`}
      style={inlineStyle}
    >
      {data.canDelete && (
        <button
          onClick={handleDelete}
          className="absolute -top-2 -right-2 w-5 h-5 bg-red-600 text-white rounded-full text-xs font-bold hover:bg-red-700 flex items-center justify-center shadow"
          title="Delete this node"
        >
          ×
        </button>
      )}
      <Handle
        type="target"
        position={Position.Top}
        id="top"
        className="w-3 h-3 bg-red-600 border-2 border-white"
      />
      <Handle
        type="target"
        position={Position.Left}
        id="left"
        className="w-3 h-3 bg-red-600 border-2 border-white"
      />
      <Handle
        type="target"
        position={Position.Right}
        id="right"
        className="w-3 h-3 bg-red-600 border-2 border-white"
      />
      <div className="text-center">
        {isTaskLead && (
          <div className="text-[10px] text-red-600 font-bold uppercase tracking-wide mb-1">Task Lead</div>
        )}
        {isTeamMember && (
          <div className="text-[10px] text-gray-600 font-bold uppercase tracking-wide mb-1">Team Leader</div>
        )}
        <div className="font-semibold text-gray-900 text-sm leading-tight break-words">
          {data.role}
        </div>
        {data.assignedStaff && !isTeamMember && !data.useStaffList && (
          <div
            className={`mt-1 text-xs font-medium border-t pt-1 cursor-grab hover:opacity-75 rounded px-1 transition-colors ${staffTextColor} ${firmColor ? 'border-current' : 'border-red-200'}`}
            style={staffTextStyle}
            draggable
            onDragStart={handleStaffDragStart}
            title="Drag to reassign to another role"
          >
            {data.assignedStaff}
            {data.staffFirmName && (
              <div className="text-[9px] opacity-70 font-normal">{data.staffFirmName}</div>
            )}
          </div>
        )}
        {(isTeamMember || data.useStaffList) && data.staffList && data.staffList.length > 0 && (
          <div className="mt-1 border-t border-gray-300 pt-1">
            {data.staffList.map((staffEntry, index) => {
              const staffName = typeof staffEntry === 'string' ? staffEntry : staffEntry.name
              const staffFirmId = typeof staffEntry === 'object' ? staffEntry.firm_id : null
              const entryFirmColor = staffFirmId && data.firmColorMap ? data.firmColorMap[staffFirmId] : null
              const entryTextStyle = entryFirmColor?.useInline ? entryFirmColor.textStyle : {}
              const entryTextClass = entryFirmColor ? (entryFirmColor.useInline ? '' : entryFirmColor.text) : 'text-red-700'
              return (
              <div key={index} className="flex items-center justify-between text-xs text-gray-700 py-0.5 hover:bg-gray-100 rounded px-1">
                <span className={`font-medium ${entryTextClass}`} style={entryTextStyle}>{staffName}</span>
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    if (data.onRemoveStaffFromList) {
                      data.onRemoveStaffFromList(id, index)
                    }
                  }}
                  className="text-red-500 hover:text-red-700 text-[10px] ml-1"
                  title="Remove staff"
                >
                  ×
                </button>
              </div>
              )
            })}
          </div>
        )}
        <div className="flex gap-1 justify-center mt-2 flex-wrap">
          {data.isPM && (
            <button
              onClick={handleAddDPM}
              className="text-[9px] px-2 py-0.5 text-white rounded transition-colors bg-gray-800 hover:bg-gray-900"
              title="Add a Deputy Project Manager"
            >
              + DPM
            </button>
          )}
          {isTaskLead && (
            <button
              onClick={handleAddTeamMember}
              className="text-[9px] px-2 py-0.5 text-white rounded transition-colors bg-red-600 hover:bg-red-700"
              title="Add a team leader under this task lead"
            >
              + Team Leader
            </button>
          )}
          {!isTeamMember && !data.isPM && (
            <button
              onClick={handleAddBranch}
              className="text-[9px] px-2 py-0.5 text-white rounded transition-colors bg-gray-600 hover:bg-gray-700"
              title="Add a child branch under this node"
            >
              + Branch
            </button>
          )}
        </div>
      </div>
      <Handle
        type="source"
        position={Position.Bottom}
        id="bottom"
        className="w-3 h-3 bg-red-600 border-2 border-white"
      />
      <Handle
        type="source"
        position={Position.Left}
        id="left-source"
        className="w-3 h-3 bg-red-600 border-2 border-white"
      />
      <Handle
        type="source"
        position={Position.Right}
        id="right-source"
        className="w-3 h-3 bg-red-600 border-2 border-white"
      />
    </div>
  )
}

export default CustomNode
