import React from 'react'
import { Handle, Position } from '@xyflow/react'

function CustomNode({ data, selected, id }) {
  const handleStaffDragStart = (event) => {
    if (!data.assignedStaff) return
    event.stopPropagation()
    const staffData = {
      name: data.assignedStaff,
      staffId: data.staffId,
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

  const handleDelete = (event) => {
    event.stopPropagation()
    if (data.onDeleteNode) {
      data.onDeleteNode(id)
    }
  }

  const handleEditNotes = (event) => {
    event.stopPropagation()
    if (data.onEditNotes) {
      data.onEditNotes(id, data.notes || '')
    }
  }

  const isTaskLead = data.isTaskLead
  const isTeamMember = data.isTeamMember
  const isTopLevel = !isTaskLead && !isTeamMember

  return (
    <div
      className={`
        w-48 min-h-[70px] p-3 rounded border-2 shadow-md relative
        ${selected ? 'border-red-500 shadow-lg ring-2 ring-red-300' : isTaskLead ? 'border-red-600' : isTeamMember ? 'border-gray-600' : 'border-gray-900'}
        ${data.assignedStaff ? (isTeamMember ? 'bg-gray-100' : 'bg-red-50') : (isTaskLead ? 'bg-white' : 'bg-gray-50')}
      `}
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
        className="w-3 h-3 bg-red-600 border-2 border-white"
      />
      <div className="text-center">
        {isTaskLead && (
          <div className="text-[10px] text-red-600 font-bold uppercase tracking-wide mb-1">Task Lead</div>
        )}
        {isTeamMember && (
          <div className="text-[10px] text-gray-600 font-bold uppercase tracking-wide mb-1">Team Member</div>
        )}
        <div className="font-semibold text-gray-900 text-sm leading-tight break-words">
          {data.role}
        </div>
        {data.assignedStaff && (
          <div
            className="mt-1 text-xs text-red-700 font-medium border-t border-red-200 pt-1 cursor-grab hover:bg-red-100 rounded px-1 transition-colors"
            draggable
            onDragStart={handleStaffDragStart}
            title="Drag to reassign to another role"
          >
            {data.assignedStaff}
          </div>
        )}
        {data.notes && (
          <div className="mt-1 text-[10px] text-gray-500 italic border-t border-gray-200 pt-1 truncate" title={data.notes}>
            {data.notes.length > 30 ? data.notes.substring(0, 30) + '...' : data.notes}
          </div>
        )}
        <div className="mt-2 flex gap-1 justify-center flex-wrap">
          {isTaskLead && (
            <button
              onClick={handleAddTeamMember}
              className="text-[9px] px-2 py-0.5 bg-red-600 text-white rounded hover:bg-red-700 transition-colors"
              title="Add a team member under this task lead"
            >
              + Team
            </button>
          )}
          <button
            onClick={handleEditNotes}
            className="text-[9px] px-2 py-0.5 bg-gray-600 text-white rounded hover:bg-gray-700 transition-colors"
            title="Add/edit notes"
          >
            Notes
          </button>
        </div>
      </div>
      <Handle
        type="source"
        position={Position.Bottom}
        className="w-3 h-3 bg-red-600 border-2 border-white"
      />
    </div>
  )
}

export default CustomNode
