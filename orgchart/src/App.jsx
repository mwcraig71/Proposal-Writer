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
import JunctionNode from './JunctionNode'

const nodeTypes = { custom: CustomNode, junction: JunctionNode }

const nodeWidth = 192
const nodeHeight = 100
const junctionSize = 12

const getLayoutedElements = (nodes, edges, direction = 'TB') => {
  const pmNode = nodes.find(n => n.id === 'pm')
  const junctionNode = nodes.find(n => n.id === 'junction')
  const safetyNode = nodes.find(n => n.id === 'safety')
  const qaqcNode = nodes.find(n => n.id === 'qaqc')
  
  const serviceNodes = nodes.filter(n => n.data?.isTaskLead)
  const teamNodes = nodes.filter(n => n.data?.isTeamMember)
  
  const centerX = 500
  const pmY = 20
  const junctionY = pmY + nodeHeight + 30
  const staffY = junctionY - (nodeHeight / 2) + (junctionSize / 2)
  const serviceY = junctionY + 80
  
  const layoutedNodes = nodes.map((node) => {
    if (node.id === 'pm') {
      return { ...node, position: { x: centerX - nodeWidth / 2, y: pmY } }
    }
    if (node.id === 'junction') {
      return { ...node, position: { x: centerX - junctionSize / 2, y: junctionY } }
    }
    if (node.id === 'safety') {
      return { ...node, position: { x: centerX - nodeWidth - 100, y: staffY } }
    }
    if (node.id === 'qaqc') {
      return { ...node, position: { x: centerX + 100, y: staffY } }
    }
    
    if (node.data?.isTaskLead) {
      const serviceIndex = serviceNodes.findIndex(n => n.id === node.id)
      const totalServices = serviceNodes.length
      const spacing = nodeWidth + 20
      const totalWidth = totalServices * spacing - 20
      const startX = centerX - totalWidth / 2
      return { ...node, position: { x: startX + serviceIndex * spacing, y: serviceY } }
    }
    
    if (node.data?.isTeamMember) {
      const parentNode = nodes.find(n => n.id === node.data.parentId)
      if (parentNode) {
        const siblingsUnderSameParent = teamNodes.filter(n => n.data.parentId === node.data.parentId)
        const siblingIndex = siblingsUnderSameParent.findIndex(n => n.id === node.id)
        const parentPos = parentNode.position || { x: centerX, y: serviceY }
        return { 
          ...node, 
          position: { 
            x: parentPos.x + (siblingIndex * 50) - ((siblingsUnderSameParent.length - 1) * 25), 
            y: parentPos.y + nodeHeight + 40 + (siblingIndex * 20)
          } 
        }
      }
    }
    
    return node
  })

  return { nodes: layoutedNodes, edges }
}

const initialNodes = [
  { id: 'pm', type: 'custom', data: { role: 'Project Manager (PM)', assignedStaff: null, isTaskLead: false, canDelete: false, notes: '' }, position: { x: 400, y: 0 } },
  { id: 'junction', type: 'junction', data: {}, position: { x: 400, y: 100 } },
  { id: 'safety', type: 'custom', data: { role: 'Safety Officer', assignedStaff: null, isTaskLead: false, canDelete: false, connectFromSide: 'right' }, position: { x: 150, y: 100 } },
  { id: 'qaqc', type: 'custom', data: { role: 'QA/QC Manager', assignedStaff: null, isTaskLead: false, canDelete: false, connectFromSide: 'left' }, position: { x: 650, y: 100 } },
  { id: 'topside', type: 'custom', data: { role: 'Top Side Inspection Task Lead', assignedStaff: null, isTaskLead: true, parentId: 'junction', canDelete: true, notes: '' }, position: { x: 0, y: 250 } },
  { id: 'underwater', type: 'custom', data: { role: 'Underwater Inspection Task Lead', assignedStaff: null, isTaskLead: true, parentId: 'junction', canDelete: true, notes: '' }, position: { x: 200, y: 250 } },
  { id: 'loadrating', type: 'custom', data: { role: 'Load Rating Task Lead', assignedStaff: null, isTaskLead: true, parentId: 'junction', canDelete: true, notes: '' }, position: { x: 400, y: 250 } },
  { id: 'loadtesting', type: 'custom', data: { role: 'Load Testing Task Lead', assignedStaff: null, isTaskLead: true, parentId: 'junction', canDelete: true, notes: '' }, position: { x: 600, y: 250 } },
  { id: 'ndt', type: 'custom', data: { role: 'NDT Task Lead', assignedStaff: null, isTaskLead: true, parentId: 'junction', canDelete: true, notes: '' }, position: { x: 800, y: 250 } },
]

const initialEdges = [
  { id: 'e-pm-junction', source: 'pm', target: 'junction', type: 'smoothstep' },
  { id: 'e-junction-safety', source: 'junction', sourceHandle: 'left', target: 'safety', targetHandle: 'right', type: 'smoothstep' },
  { id: 'e-junction-qaqc', source: 'junction', sourceHandle: 'right', target: 'qaqc', targetHandle: 'left', type: 'smoothstep' },
  { id: 'e-junction-topside', source: 'junction', target: 'topside', type: 'smoothstep' },
  { id: 'e-junction-underwater', source: 'junction', target: 'underwater', type: 'smoothstep' },
  { id: 'e-junction-loadrating', source: 'junction', target: 'loadrating', type: 'smoothstep' },
  { id: 'e-junction-loadtesting', source: 'junction', target: 'loadtesting', type: 'smoothstep' },
  { id: 'e-junction-ndt', source: 'junction', target: 'ndt', type: 'smoothstep' },
]

const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(initialNodes, initialEdges)

function OrgChartFlow() {
  const reactFlowWrapper = useRef(null)
  const [nodes, setNodes, onNodesChange] = useNodesState(layoutedNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(layoutedEdges)
  const [reactFlowInstance, setReactFlowInstance] = useState(null)
  const [staff, setStaff] = useState([])
  const [draggedStaff, setDraggedStaff] = useState(null)
  const [globalNotes, setGlobalNotes] = useState('')

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
    event.dataTransfer.setData('application/reactflow', JSON.stringify({
      ...staffMember,
      fromSidebar: true
    }))
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

      const reassignData = event.dataTransfer.getData('application/staff-reassign')
      if (reassignData) {
        const staffInfo = JSON.parse(reassignData)
        
        if (dropTargetNode && dropTargetNode.id !== staffInfo.fromNodeId) {
          setNodes((nds) =>
            nds.map((node) => {
              if (node.id === staffInfo.fromNodeId) {
                return { ...node, data: { ...node.data, assignedStaff: null, staffId: null } }
              }
              if (node.id === dropTargetNode.id) {
                return { ...node, data: { ...node.data, assignedStaff: staffInfo.name, staffId: staffInfo.staffId } }
              }
              return node
            })
          )
        } else if (!dropTargetNode) {
          setNodes((nds) => {
            const updated = nds.map((node) => {
              if (node.id === staffInfo.fromNodeId) {
                return { ...node, data: { ...node.data, assignedStaff: null, staffId: null } }
              }
              return node
            })
            const newNode = {
              id: `node-${Date.now()}`,
              type: 'custom',
              position,
              data: { role: 'New Role', assignedStaff: staffInfo.name, staffId: staffInfo.staffId },
            }
            return [...updated, newNode]
          })
        }
        return
      }

      const staffData = event.dataTransfer.getData('application/reactflow')
      if (!staffData) return

      const staffMember = JSON.parse(staffData)

      if (dropTargetNode) {
        setNodes((nds) =>
          nds.map((node) => {
            if (node.id === dropTargetNode.id) {
              return {
                ...node,
                data: {
                  ...node.data,
                  assignedStaff: staffMember.name,
                  staffId: staffMember.id,
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
          data: { role: 'New Role', assignedStaff: staffMember.name, staffId: staffMember.id },
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

  const deleteNode = useCallback((nodeId) => {
    const nodeToDelete = nodes.find(n => n.id === nodeId)
    if (!nodeToDelete || !nodeToDelete.data.canDelete) return
    
    if (!confirm(`Delete "${nodeToDelete.data.role}"? This will also remove any team members under it.`)) return

    const childNodes = nodes.filter(n => n.data.parentId === nodeId)
    const nodesToDelete = [nodeId, ...childNodes.map(n => n.id)]
    
    setNodes((nds) => nds.filter(n => !nodesToDelete.includes(n.id)))
    setEdges((eds) => eds.filter(e => !nodesToDelete.includes(e.source) && !nodesToDelete.includes(e.target)))
  }, [nodes, setNodes, setEdges])

  const addTeamMember = useCallback((parentNodeId) => {
    const parentNode = nodes.find(n => n.id === parentNodeId)
    if (!parentNode) return

    const newNodeId = `team-${Date.now()}`
    const newNode = {
      id: newNodeId,
      type: 'custom',
      position: { x: parentNode.position.x, y: parentNode.position.y + 120 },
      data: { 
        role: 'Team Member', 
        assignedStaff: null, 
        isTeamMember: true,
        parentId: parentNodeId,
        canDelete: true,
        notes: ''
      },
    }
    const newEdge = {
      id: `e-${parentNodeId}-${newNodeId}`,
      source: parentNodeId,
      target: newNodeId,
      type: 'smoothstep'
    }
    
    setNodes((nds) => [...nds, newNode])
    setEdges((eds) => [...eds, newEdge])
    
    setTimeout(() => {
      const { nodes: layouted } = getLayoutedElements([...nodes, newNode], [...edges, newEdge])
      setNodes(layouted)
    }, 50)
  }, [nodes, edges, setNodes, setEdges])

  const addNewServiceType = useCallback(() => {
    const serviceName = prompt('Enter new service type name:', 'New Service')
    if (!serviceName || serviceName.trim() === '') return

    const newNodeId = `service-${Date.now()}`
    const junctionNode = nodes.find(n => n.id === 'junction')
    const newNode = {
      id: newNodeId,
      type: 'custom',
      position: { x: junctionNode ? junctionNode.position.x + 200 : 400, y: junctionNode ? junctionNode.position.y + 120 : 300 },
      data: { 
        role: `${serviceName.trim()} Task Lead`, 
        assignedStaff: null, 
        isTaskLead: true,
        parentId: 'junction',
        canDelete: true,
        notes: ''
      },
    }
    const newEdge = {
      id: `e-junction-${newNodeId}`,
      source: 'junction',
      target: newNodeId,
      type: 'smoothstep'
    }
    
    setNodes((nds) => [...nds, newNode])
    setEdges((eds) => [...eds, newEdge])
    
    setTimeout(() => {
      const { nodes: layouted } = getLayoutedElements([...nodes, newNode], [...edges, newEdge])
      setNodes(layouted)
    }, 50)
  }, [nodes, edges, setNodes, setEdges, addTeamMember])

  const nodesWithCallbacks = nodes.map(node => ({
    ...node,
    data: {
      ...node.data,
      onAddTeamMember: addTeamMember,
      onDeleteNode: deleteNode
    }
  }))

  return (
    <div className="flex h-screen w-full">
      <div className="w-64 bg-gray-100 border-r border-gray-300 flex flex-col">
        <div className="p-4 bg-gray-900 text-white">
          <h2 className="text-lg font-bold">Available Staff</h2>
          <p className="text-sm text-gray-400">Drag to assign</p>
        </div>
        <div className="flex-1 overflow-y-auto p-2">
          {staff.length === 0 ? (
            <p className="text-gray-500 text-sm p-2">No staff available. Add employees in the main app.</p>
          ) : (
            staff.map((person) => (
              <div
                key={person.id}
                className="staff-item p-3 mb-2 bg-white rounded shadow hover:shadow-md border border-gray-200 hover:border-red-500 transition-all cursor-grab"
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
          nodes={nodesWithCallbacks}
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
              onClick={addNewServiceType}
              className="px-4 py-2 bg-red-600 text-white rounded shadow hover:bg-red-700 transition-colors font-medium"
            >
              + Add Service Type
            </button>
            <button
              onClick={onResetLayout}
              className="px-4 py-2 bg-gray-800 text-white rounded shadow hover:bg-gray-900 transition-colors font-medium"
            >
              Reset Layout
            </button>
          </Panel>
        </ReactFlow>
      </div>

      <div className="w-72 bg-gray-50 border-l border-gray-300 flex flex-col">
        <div className="p-4 bg-red-700 text-white">
          <h2 className="text-lg font-bold">Assigned Staff</h2>
          <p className="text-sm text-red-200">Current assignments</p>
        </div>
        <div className="flex-1 overflow-y-auto p-2">
          {nodes.filter(n => n.data?.assignedStaff).length === 0 ? (
            <p className="text-gray-500 text-sm p-2">No staff assigned yet. Drag staff from the left panel to a role.</p>
          ) : (
            nodes.filter(n => n.data?.assignedStaff).map((node) => (
              <div
                key={node.id}
                className="p-3 mb-2 bg-white rounded shadow border border-gray-200"
              >
                <div className="font-medium text-gray-800 text-sm">{node.data.role}</div>
                <div className="text-xs text-red-600 font-medium">{node.data.assignedStaff}</div>
                <button
                  onClick={() => removeStaffFromNode(node.id)}
                  className="mt-1 text-xs text-gray-500 hover:text-red-600"
                >
                  Remove
                </button>
              </div>
            ))
          )}
        </div>
        <div className="border-t border-gray-300">
          <div className="p-3 bg-gray-800 text-white">
            <h3 className="text-sm font-bold">Notes</h3>
          </div>
          <div className="p-2">
            <textarea
              value={globalNotes}
              onChange={(e) => setGlobalNotes(e.target.value)}
              placeholder="Add notes about this org chart..."
              className="w-full h-32 p-2 text-sm border border-gray-300 rounded resize-none focus:outline-none focus:border-red-500"
            />
          </div>
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
