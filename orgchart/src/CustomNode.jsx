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

  const isTaskLead = data.isTaskLead
  const isTeamMember = data.isTeamMember

  return (
    <div
      className={`
        w-44 min-h-[60px] p-3 rounded border-2 shadow-md
        ${selected ? 'border-blue-500 shadow-lg' : isTaskLead ? 'border-orange-600' : isTeamMember ? 'border-green-600' : 'border-blue-800'}
        ${data.assignedStaff ? (isTeamMember ? 'bg-green-100' : 'bg-green-50') : (isTaskLead ? 'bg-orange-50' : 'bg-white')}
      `}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3 bg-blue-600 border-2 border-white"
      />
      <div className="text-center">
        {isTaskLead && (
          <div className="text-[10px] text-orange-600 font-bold uppercase tracking-wide mb-1">Task Lead</div>
        )}
        {isTeamMember && (
          <div className="text-[10px] text-green-600 font-bold uppercase tracking-wide mb-1">Team Member</div>
        )}
        <div className="font-semibold text-gray-800 text-sm leading-tight break-words">
          {data.role}
        </div>
        {data.assignedStaff && (
          <div
            className="mt-1 text-xs text-green-700 font-medium border-t border-green-200 pt-1 cursor-grab hover:bg-green-100 rounded px-1 transition-colors"
            draggable
            onDragStart={handleStaffDragStart}
            title="Drag to reassign to another role"
          >
            {data.assignedStaff}
          </div>
        )}
        {isTaskLead && (
          <button
            onClick={handleAddTeamMember}
            className="mt-2 text-[10px] px-2 py-1 bg-orange-500 text-white rounded hover:bg-orange-600 transition-colors"
            title="Add a team member under this task lead"
          >
            + Add Team Member
          </button>
        )}
      </div>
      <Handle
        type="source"
        position={Position.Bottom}
        className="w-3 h-3 bg-blue-600 border-2 border-white"
      />
    </div>
  )
}

export default CustomNode
