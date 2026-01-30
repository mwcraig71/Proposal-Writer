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

  const handleAddTeamMemberToList = (event) => {
    event.stopPropagation()
    if (data.onAddTeamMemberToList) {
      data.onAddTeamMemberToList(id)
    }
  }

  const handleRemoveTeamMemberFromList = (event, index) => {
    event.stopPropagation()
    if (data.onRemoveTeamMemberFromList) {
      data.onRemoveTeamMemberFromList(id, index)
    }
  }

  const handleDelete = (event) => {
    event.stopPropagation()
    if (data.onDeleteNode) {
      data.onDeleteNode(id)
    }
  }

  const isTaskLead = data.isTaskLead
  const isTeamMember = data.isTeamMember
  const isActualTeamMember = data.isActualTeamMember
  const connectFromSide = data.connectFromSide

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
        id="top"
        className="w-3 h-3 bg-red-600 border-2 border-white"
      />
      {connectFromSide === 'right' && (
        <Handle
          type="target"
          position={Position.Right}
          id="right"
          className="w-3 h-3 bg-red-600 border-2 border-white"
        />
      )}
      {connectFromSide === 'left' && (
        <Handle
          type="target"
          position={Position.Left}
          id="left"
          className="w-3 h-3 bg-red-600 border-2 border-white"
        />
      )}
      <div className="text-center">
        {isTaskLead && (
          <div className="text-[10px] text-red-600 font-bold uppercase tracking-wide mb-1">Task Lead</div>
        )}
        {isTeamMember && !isActualTeamMember && (
          <div className="text-[10px] text-gray-600 font-bold uppercase tracking-wide mb-1">Team Leader</div>
        )}
        {isActualTeamMember && (
          <div className="text-[10px] text-gray-500 font-bold uppercase tracking-wide mb-1">Team Member</div>
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
        {isTaskLead && (
          <button
            onClick={handleAddTeamMember}
            className="mt-2 text-[9px] px-2 py-0.5 text-white rounded transition-colors bg-red-600 hover:bg-red-700"
            title="Add a team leader under this task lead"
          >
            + Team Leader
          </button>
        )}
        {isTeamMember && !isActualTeamMember && (
          <>
            {data.teamMembers && data.teamMembers.length > 0 && (
              <div className="mt-2 border-t border-gray-300 pt-2">
                <div className="text-[9px] text-gray-500 uppercase font-bold mb-1">Team Members:</div>
                {data.teamMembers.map((member, index) => (
                  <div key={index} className="flex items-center justify-between text-xs text-gray-700 py-0.5 hover:bg-gray-100 rounded px-1">
                    <span>{member}</span>
                    <button
                      onClick={(e) => handleRemoveTeamMemberFromList(e, index)}
                      className="text-red-500 hover:text-red-700 text-[10px] ml-1"
                      title="Remove team member"
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            )}
            <button
              onClick={handleAddTeamMemberToList}
              className="mt-2 text-[9px] px-2 py-0.5 text-white rounded transition-colors bg-gray-600 hover:bg-gray-700"
              title="Add a team member to this team leader"
            >
              + Team Member
            </button>
          </>
        )}
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
