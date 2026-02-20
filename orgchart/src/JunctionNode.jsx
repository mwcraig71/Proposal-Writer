import React from 'react'
import { Handle, Position } from '@xyflow/react'

function JunctionNode({ selected }) {
  return (
    <div 
      className={`w-2 h-2 rounded-full ${selected ? 'bg-red-400 border border-red-500 shadow-lg' : 'bg-transparent'} cursor-move`}
      title="Junction point (hidden in exports)"
      style={{ opacity: selected ? 0.8 : 0 }}
    >
      <Handle
        type="target"
        position={Position.Top}
        id="top"
        className="w-1 h-1 border-0"
        style={{ top: -2, opacity: 0, background: 'transparent' }}
      />
      <Handle
        type="target"
        position={Position.Left}
        id="left"
        className="w-1 h-1 border-0"
        style={{ left: -2, opacity: 0, background: 'transparent' }}
      />
      <Handle
        type="target"
        position={Position.Right}
        id="right"
        className="w-1 h-1 border-0"
        style={{ right: -2, opacity: 0, background: 'transparent' }}
      />
      <Handle
        type="source"
        position={Position.Bottom}
        id="bottom"
        className="w-1 h-1 border-0"
        style={{ bottom: -2, opacity: 0, background: 'transparent' }}
      />
      <Handle
        type="source"
        position={Position.Left}
        id="left-source"
        className="w-1 h-1 border-0"
        style={{ left: -2, opacity: 0, background: 'transparent' }}
      />
      <Handle
        type="source"
        position={Position.Right}
        id="right-source"
        className="w-1 h-1 border-0"
        style={{ right: -2, opacity: 0, background: 'transparent' }}
      />
    </div>
  )
}

export default JunctionNode
