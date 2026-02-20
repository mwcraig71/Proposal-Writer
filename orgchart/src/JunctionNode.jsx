import React from 'react'
import { Handle, Position } from '@xyflow/react'

function JunctionNode({ selected }) {
  return (
    <div 
      className={`w-6 h-6 bg-gray-800 rounded-full border-2 ${selected ? 'border-red-500 shadow-lg' : 'border-gray-600'} cursor-move`}
      title="Drag to reposition the junction point"
    >
      <Handle
        type="target"
        position={Position.Top}
        id="top"
        className="w-2 h-2 bg-red-600 border-0"
        style={{ top: -4 }}
      />
      <Handle
        type="target"
        position={Position.Left}
        id="left"
        className="w-2 h-2 bg-red-600 border-0"
        style={{ left: -4 }}
      />
      <Handle
        type="target"
        position={Position.Right}
        id="right"
        className="w-2 h-2 bg-red-600 border-0"
        style={{ right: -4 }}
      />
      <Handle
        type="source"
        position={Position.Bottom}
        id="bottom"
        className="w-2 h-2 bg-red-600 border-0"
        style={{ bottom: -4 }}
      />
      <Handle
        type="source"
        position={Position.Left}
        id="left-source"
        className="w-2 h-2 bg-red-600 border-0"
        style={{ left: -4 }}
      />
      <Handle
        type="source"
        position={Position.Right}
        id="right-source"
        className="w-2 h-2 bg-red-600 border-0"
        style={{ right: -4 }}
      />
    </div>
  )
}

export default JunctionNode
