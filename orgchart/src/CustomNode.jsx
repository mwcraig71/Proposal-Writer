import React from 'react'
import { Handle, Position } from '@xyflow/react'

function CustomNode({ data, selected }) {
  return (
    <div
      className={`
        w-44 min-h-[60px] p-3 rounded bg-white border-2 shadow-md
        ${selected ? 'border-blue-500 shadow-lg' : 'border-blue-800'}
        ${data.assignedStaff ? 'bg-green-50' : 'bg-white'}
      `}
    >
      <Handle
        type="target"
        position={Position.Top}
        className="w-3 h-3 bg-blue-600 border-2 border-white"
      />
      <div className="text-center">
        <div className="font-semibold text-gray-800 text-sm leading-tight break-words">
          {data.role}
        </div>
        {data.assignedStaff && (
          <div className="mt-1 text-xs text-green-700 font-medium border-t border-green-200 pt-1">
            {data.assignedStaff}
          </div>
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
