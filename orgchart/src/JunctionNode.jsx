import React from 'react'
import { Handle, Position } from '@xyflow/react'

function JunctionNode() {
  return (
    <div className="w-3 h-3 bg-gray-900 rounded-full">
      <Handle
        type="target"
        position={Position.Top}
        className="w-2 h-2 bg-gray-900 border-0 opacity-0"
        style={{ top: -4 }}
      />
      <Handle
        type="source"
        position={Position.Bottom}
        className="w-2 h-2 bg-gray-900 border-0 opacity-0"
        style={{ bottom: -4 }}
      />
      <Handle
        type="source"
        position={Position.Left}
        id="left"
        className="w-2 h-2 bg-gray-900 border-0 opacity-0"
        style={{ left: -4 }}
      />
      <Handle
        type="source"
        position={Position.Right}
        id="right"
        className="w-2 h-2 bg-gray-900 border-0 opacity-0"
        style={{ right: -4 }}
      />
    </div>
  )
}

export default JunctionNode
