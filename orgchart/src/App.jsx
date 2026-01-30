import React, { useState, useCallback, useRef, useEffect } from 'react'
import {
  ReactFlow,
  ReactFlowProvider,
  addEdge,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  Panel
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import dagre from 'dagre'
import CustomNode from './CustomNode'

const nodeTypes = { custom: CustomNode }

const nodeWidth = 180
const nodeHeight = 80

const getLayoutedElements = (nodes, edges, direction = 'TB') => {
  const dagreGraph = new dagre.graphlib.Graph()
  dagreGraph.setDefaultEdgeLabel(() => ({}))
  dagreGraph.setGraph({ rankdir: direction, nodesep: 50, ranksep: 80 })

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: nodeWidth, height: nodeHeight })
  })

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target)
  })

  dagre.layout(dagreGraph)

  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id)
    return {
      ...node,
      position: {
        x: nodeWithPosition.x - nodeWidth / 2,
        y: nodeWithPosition.y - nodeHeight / 2,
      },
    }
  })

  return { nodes: layoutedNodes, edges }
}

const initialNodes = [
  { id: 'pm', type: 'custom', data: { role: 'Project Manager (PM)', assignedStaff: null }, position: { x: 0, y: 0 } },
  { id: 'safety', type: 'custom', data: { role: 'Safety Officer', assignedStaff: null }, position: { x: 0, y: 0 } },
  { id: 'qaqc', type: 'custom', data: { role: 'QA/QC Manager', assignedStaff: null }, position: { x: 0, y: 0 } },
  { id: 'topside', type: 'custom', data: { role: 'Top Side Inspection', assignedStaff: null }, position: { x: 0, y: 0 } },
  { id: 'underwater', type: 'custom', data: { role: 'Underwater Inspection', assignedStaff: null }, position: { x: 0, y: 0 } },
  { id: 'loadrating', type: 'custom', data: { role: 'Load Rating', assignedStaff: null }, position: { x: 0, y: 0 } },
  { id: 'loadtesting', type: 'custom', data: { role: 'Load Testing', assignedStaff: null }, position: { x: 0, y: 0 } },
  { id: 'ndt', type: 'custom', data: { role: 'NDT', assignedStaff: null }, position: { x: 0, y: 0 } },
]

const initialEdges = [
  { id: 'e-pm-safety', source: 'pm', target: 'safety', type: 'smoothstep' },
  { id: 'e-safety-qaqc', source: 'safety', target: 'qaqc', type: 'smoothstep' },
  { id: 'e-qaqc-topside', source: 'qaqc', target: 'topside', type: 'smoothstep' },
  { id: 'e-qaqc-underwater', source: 'qaqc', target: 'underwater', type: 'smoothstep' },
  { id: 'e-qaqc-loadrating', source: 'qaqc', target: 'loadrating', type: 'smoothstep' },
  { id: 'e-qaqc-loadtesting', source: 'qaqc', target: 'loadtesting', type: 'smoothstep' },
  { id: 'e-qaqc-ndt', source: 'qaqc', target: 'ndt', type: 'smoothstep' },
]

const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(initialNodes, initialEdges)

function OrgChartFlow() {
  const reactFlowWrapper = useRef(null)
  const [nodes, setNodes, onNodesChange] = useNodesState(layoutedNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(layoutedEdges)
  const [reactFlowInstance, setReactFlowInstance] = useState(null)
  const [staff, setStaff] = useState([])
  const [draggedStaff, setDraggedStaff] = useState(null)

  useEffect(() => {
    fetch('/api/employees')
      .then(res => res.json())
      .then(data => setStaff(data))
      .catch(err => console.error('Failed to fetch staff:', err))
  }, [])

  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge({ ...params, type: 'smoothstep' }, eds)),
    [setEdges]
  )

  const onResetLayout = useCallback(() => {
    const { nodes: layouted } = getLayoutedElements(nodes, edges)
    setNodes(layouted)
  }, [nodes, edges, setNodes])

  const onDragStart = (event, staffMember) => {
    setDraggedStaff(staffMember)
    event.dataTransfer.setData('application/reactflow', JSON.stringify(staffMember))
    event.dataTransfer.effectAllowed = 'move'
  }

  const onDragOver = useCallback((event) => {
    event.preventDefault()
    event.dataTransfer.dropEffect = 'move'
  }, [])

  const onDrop = useCallback(
    (event) => {
      event.preventDefault()

      if (!reactFlowInstance) return

      const staffData = event.dataTransfer.getData('application/reactflow')
      if (!staffData) return

      const staffMember = JSON.parse(staffData)
      const position = reactFlowInstance.screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      })

      const dropTargetNode = nodes.find((node) => {
        const nodeX = node.position.x
        const nodeY = node.position.y
        return (
          position.x >= nodeX &&
          position.x <= nodeX + nodeWidth &&
          position.y >= nodeY &&
          position.y <= nodeY + nodeHeight
        )
      })

      if (dropTargetNode) {
        setNodes((nds) =>
          nds.map((node) => {
            if (node.id === dropTargetNode.id) {
              return {
                ...node,
                data: {
                  ...node.data,
                  assignedStaff: staffMember.name,
                },
              }
            }
            return node
          })
        )
      } else {
        const newNode = {
          id: `node-${Date.now()}`,
          type: 'custom',
          position,
          data: { role: 'New Role', assignedStaff: staffMember.name },
        }
        setNodes((nds) => nds.concat(newNode))
      }

      setDraggedStaff(null)
    },
    [reactFlowInstance, nodes, setNodes]
  )

  const onNodeDoubleClick = useCallback((event, node) => {
    const newRole = prompt('Enter new role name:', node.data.role)
    if (newRole !== null && newRole.trim() !== '') {
      setNodes((nds) =>
        nds.map((n) => {
          if (n.id === node.id) {
            return { ...n, data: { ...n.data, role: newRole.trim() } }
          }
          return n
        })
      )
    }
  }, [setNodes])

  const removeStaffFromNode = useCallback((nodeId) => {
    setNodes((nds) =>
      nds.map((node) => {
        if (node.id === nodeId) {
          return { ...node, data: { ...node.data, assignedStaff: null } }
        }
        return node
      })
    )
  }, [setNodes])

  return (
    <div className="flex h-screen w-full">
      <div className="w-64 bg-gray-100 border-r border-gray-300 flex flex-col">
        <div className="p-4 bg-blue-800 text-white">
          <h2 className="text-lg font-bold">Available Staff</h2>
          <p className="text-sm text-blue-200">Drag to assign</p>
        </div>
        <div className="flex-1 overflow-y-auto p-2">
          {staff.length === 0 ? (
            <p className="text-gray-500 text-sm p-2">No staff available. Add employees in the main app.</p>
          ) : (
            staff.map((person) => (
              <div
                key={person.id}
                className="staff-item p-3 mb-2 bg-white rounded shadow hover:shadow-md border border-gray-200 hover:border-blue-400 transition-all"
                draggable
                onDragStart={(e) => onDragStart(e, person)}
              >
                <div className="font-medium text-gray-800 text-sm">{person.name}</div>
                {person.title && (
                  <div className="text-xs text-gray-500">{person.title}</div>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      <div className="flex-1" ref={reactFlowWrapper}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onInit={setReactFlowInstance}
          onDrop={onDrop}
          onDragOver={onDragOver}
          onNodeDoubleClick={onNodeDoubleClick}
          nodeTypes={nodeTypes}
          fitView
          defaultEdgeOptions={{ type: 'smoothstep' }}
        >
          <Controls />
          <Background variant="dots" gap={12} size={1} />
          <Panel position="top-right" className="flex gap-2">
            <button
              onClick={onResetLayout}
              className="px-4 py-2 bg-blue-600 text-white rounded shadow hover:bg-blue-700 transition-colors font-medium"
            >
              Reset Layout
            </button>
          </Panel>
        </ReactFlow>
      </div>

      <div className="w-64 bg-gray-50 border-l border-gray-300 flex flex-col">
        <div className="p-4 bg-green-800 text-white">
          <h2 className="text-lg font-bold">Assigned Staff</h2>
          <p className="text-sm text-green-200">Current assignments</p>
        </div>
        <div className="flex-1 overflow-y-auto p-2">
          {nodes.filter(n => n.data.assignedStaff).length === 0 ? (
            <p className="text-gray-500 text-sm p-2">No staff assigned yet. Drag staff from the left panel to a role.</p>
          ) : (
            nodes.filter(n => n.data.assignedStaff).map((node) => (
              <div
                key={node.id}
                className="p-3 mb-2 bg-white rounded shadow border border-gray-200"
              >
                <div className="font-medium text-gray-800 text-sm">{node.data.role}</div>
                <div className="text-xs text-green-600 font-medium">{node.data.assignedStaff}</div>
                <button
                  onClick={() => removeStaffFromNode(node.id)}
                  className="mt-1 text-xs text-red-500 hover:text-red-700"
                >
                  Remove
                </button>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}

function App() {
  return (
    <ReactFlowProvider>
      <OrgChartFlow />
    </ReactFlowProvider>
  )
}

export default App
