import React, { useState, useCallback, useRef, useEffect } from 'react'
import {
  ReactFlow,
  ReactFlowProvider,
  addEdge,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  Panel,
  useReactFlow,
  getNodesBounds,
  getViewportForBounds
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import dagre from 'dagre'
import { toPng, toJpeg } from 'html-to-image'
import { jsPDF } from 'jspdf'
import CustomNode from './CustomNode'
import JunctionNode from './JunctionNode'

const nodeTypes = { custom: CustomNode, junction: JunctionNode }

const nodeWidth = 192
const nodeHeight = 100
const junctionSize = 4

const EDGE_COLOR = '#374151'
const getStrokeWidth = (weight) => weight === 'thin' ? 1 : weight === 'thick' ? 4 : 2
const edgeStyle = (weight = 'medium') => ({ stroke: EDGE_COLOR, strokeWidth: getStrokeWidth(weight) })

const FIRM_COLORS = [
  { bg: 'bg-red-50', border: 'border-red-600', text: 'text-red-700', label: 'bg-red-600', hex: '#dc2626' },
  { bg: 'bg-blue-50', border: 'border-blue-600', text: 'text-blue-700', label: 'bg-blue-600', hex: '#2563eb' },
  { bg: 'bg-green-50', border: 'border-green-600', text: 'text-green-700', label: 'bg-green-600', hex: '#16a34a' },
  { bg: 'bg-purple-50', border: 'border-purple-600', text: 'text-purple-700', label: 'bg-purple-600', hex: '#9333ea' },
  { bg: 'bg-orange-50', border: 'border-orange-600', text: 'text-orange-700', label: 'bg-orange-600', hex: '#ea580c' },
  { bg: 'bg-teal-50', border: 'border-teal-600', text: 'text-teal-700', label: 'bg-teal-600', hex: '#0d9488' },
  { bg: 'bg-pink-50', border: 'border-pink-600', text: 'text-pink-700', label: 'bg-pink-600', hex: '#db2777' },
  { bg: 'bg-yellow-50', border: 'border-yellow-600', text: 'text-yellow-700', label: 'bg-yellow-600', hex: '#ca8a04' },
]

const hexToColorObj = (hex) => ({
  hex,
  useInline: true,
  borderStyle: { borderColor: hex },
  bgStyle: { backgroundColor: hex + '18' },
  textStyle: { color: hex },
  labelStyle: { backgroundColor: hex },
})

const getLayoutedElements = (nodes, edges, direction = 'TB') => {
  const pmNode = nodes.find(n => n.id === 'pm')
  const junctionNode = nodes.find(n => n.id === 'junction')
  const safetyNode = nodes.find(n => n.id === 'safety')
  const qaqcNode = nodes.find(n => n.id === 'qaqc')
  
  const serviceNodes = nodes.filter(n => n.data?.isTaskLead)
  const teamNodes = nodes.filter(n => n.data?.isTeamMember)
  const branchNodes = nodes.filter(n => n.data?.parentId && !n.data?.isTaskLead && !n.data?.isTeamMember && n.id !== 'junction')
  
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

    if (node.data?.parentId && !node.data?.isTaskLead && !node.data?.isTeamMember) {
      const parentNode = nodes.find(n => n.id === node.data.parentId)
      if (parentNode) {
        const siblingsUnderSameParent = branchNodes.filter(n => n.data.parentId === node.data.parentId)
        const siblingIndex = siblingsUnderSameParent.findIndex(n => n.id === node.id)
        const totalSiblings = siblingsUnderSameParent.length
        const spacing = nodeWidth + 20
        const parentPos = parentNode.position || { x: centerX, y: 200 }
        const totalWidth = totalSiblings * spacing - 20
        const startX = parentPos.x + (nodeWidth / 2) - (totalWidth / 2)
        return { 
          ...node, 
          position: { 
            x: startX + siblingIndex * spacing, 
            y: parentPos.y + nodeHeight + 40
          } 
        }
      }
    }
    
    return node
  })

  return { nodes: layoutedNodes, edges }
}

const initialNodes = [
  { id: 'pm', type: 'custom', data: { role: 'Project Manager (PM)', assignedStaff: null, isTaskLead: false, canDelete: false, isPM: true }, position: { x: 400, y: 0 } },
  { id: 'junction', type: 'junction', data: {}, position: { x: 400, y: 100 } },
  { id: 'safety', type: 'custom', data: { role: 'Safety Officer', assignedStaff: null, isTaskLead: false, canDelete: true, connectFromSide: 'right' }, position: { x: 150, y: 100 } },
  { id: 'qaqc', type: 'custom', data: { role: 'QA/QC Manager', assignedStaff: null, isTaskLead: false, canDelete: true, connectFromSide: 'left' }, position: { x: 650, y: 100 } },
  { id: 'topside', type: 'custom', data: { role: 'Top Side Inspection Task Lead', assignedStaff: null, isTaskLead: true, parentId: 'junction', canDelete: true, notes: '' }, position: { x: 0, y: 250 } },
  { id: 'underwater', type: 'custom', data: { role: 'Underwater Inspection Task Lead', assignedStaff: null, isTaskLead: true, parentId: 'junction', canDelete: true, notes: '' }, position: { x: 200, y: 250 } },
  { id: 'loadrating', type: 'custom', data: { role: 'Load Rating Task Lead', assignedStaff: null, isTaskLead: true, parentId: 'junction', canDelete: true, notes: '' }, position: { x: 400, y: 250 } },
  { id: 'loadtesting', type: 'custom', data: { role: 'Load Testing Task Lead', assignedStaff: null, isTaskLead: true, parentId: 'junction', canDelete: true, notes: '' }, position: { x: 600, y: 250 } },
  { id: 'ndt', type: 'custom', data: { role: 'NDT Task Lead', assignedStaff: null, isTaskLead: true, parentId: 'junction', canDelete: true, notes: '' }, position: { x: 800, y: 250 } },
]

const initialEdges = [
  { id: 'e-pm-junction', source: 'pm', target: 'junction', type: 'smoothstep', style: edgeStyle() },
  { id: 'e-junction-safety', source: 'junction', sourceHandle: 'left', target: 'safety', targetHandle: 'right', type: 'smoothstep', style: edgeStyle() },
  { id: 'e-junction-qaqc', source: 'junction', sourceHandle: 'right', target: 'qaqc', targetHandle: 'left', type: 'smoothstep', style: edgeStyle() },
  { id: 'e-junction-topside', source: 'junction', target: 'topside', type: 'smoothstep', style: edgeStyle() },
  { id: 'e-junction-underwater', source: 'junction', target: 'underwater', type: 'smoothstep', style: edgeStyle() },
  { id: 'e-junction-loadrating', source: 'junction', target: 'loadrating', type: 'smoothstep', style: edgeStyle() },
  { id: 'e-junction-loadtesting', source: 'junction', target: 'loadtesting', type: 'smoothstep', style: edgeStyle() },
  { id: 'e-junction-ndt', source: 'junction', target: 'ndt', type: 'smoothstep', style: edgeStyle() },
]

const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(initialNodes, initialEdges)

function OrgChartFlow() {
  const reactFlowWrapper = useRef(null)
  const [nodes, setNodes, onNodesChange] = useNodesState(layoutedNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(layoutedEdges)
  const [reactFlowInstance, setReactFlowInstance] = useState(null)
  const [staff, setStaff] = useState([])
  const [firms, setFirms] = useState([])
  const [selectedFirmFilter, setSelectedFirmFilter] = useState('')
  const [draggedStaff, setDraggedStaff] = useState(null)
  const [globalNotes, setGlobalNotes] = useState('')
  const [saveStatus, setSaveStatus] = useState('')
  const [firmColorMap, setFirmColorMap] = useState({})
  const [firmLogoMap, setFirmLogoMap] = useState({})
  const [legendItems, setLegendItems] = useState([])
  const [savedCharts, setSavedCharts] = useState([])
  const [selectedSavedChartId, setSelectedSavedChartId] = useState('')
  const [showSaveAsModal, setShowSaveAsModal] = useState(false)
  const [saveAsName, setSaveAsName] = useState('')
  const [showPdfModal, setShowPdfModal] = useState(false)
  const [pdfOrientation, setPdfOrientation] = useState('landscape')
  const [isExportingPdf, setIsExportingPdf] = useState(false)
  const [connectionDirection, setConnectionDirection] = useState('top-bottom')
  const [lineWeight, setLineWeight] = useState('medium')
  const [borderStyle, setBorderStyle] = useState('default')
  const [exportAspectRatio, setExportAspectRatio] = useState('0.773')

  const switchConnectionDirection = useCallback((direction) => {
    setConnectionDirection(direction)
    setEdges(currentEdges => currentEdges.map(edge => {
      const updated = { ...edge }
      if (direction === 'top-bottom') {
        delete updated.sourceHandle
        delete updated.targetHandle
      } else if (direction === 'left-side') {
        updated.sourceHandle = 'left-source'
        updated.targetHandle = 'left'
      } else if (direction === 'right-side') {
        updated.sourceHandle = 'right-source'
        updated.targetHandle = 'right'
      }
      return updated
    }))
  }, [setEdges])

  useEffect(() => {
    setEdges(eds => eds.map(e => ({ ...e, style: edgeStyle(lineWeight) })))
  }, [lineWeight, setEdges])

  const DIRECTION_CYCLE = [
    { sourceHandle: undefined, targetHandle: undefined, label: 'top-bottom' },
    { sourceHandle: 'left-source', targetHandle: 'left', label: 'left' },
    { sourceHandle: 'right-source', targetHandle: 'right', label: 'right' },
  ]

  const onEdgeClick = useCallback((event, edge) => {
    event.stopPropagation()
    setEdges(currentEdges => currentEdges.map(e => {
      if (e.id !== edge.id) return e
      const currentIdx = DIRECTION_CYCLE.findIndex(d =>
        d.sourceHandle === (e.sourceHandle || undefined) && d.targetHandle === (e.targetHandle || undefined)
      )
      const nextIdx = (currentIdx + 1) % DIRECTION_CYCLE.length
      const next = DIRECTION_CYCLE[nextIdx]
      const updated = { ...e }
      if (next.sourceHandle) {
        updated.sourceHandle = next.sourceHandle
      } else {
        delete updated.sourceHandle
      }
      if (next.targetHandle) {
        updated.targetHandle = next.targetHandle
      } else {
        delete updated.targetHandle
      }
      return updated
    }))
  }, [setEdges])

  const onEdgeContextMenu = useCallback((event, edge) => {
    event.preventDefault()
    event.stopPropagation()
    if (window.confirm('Delete this connection line?')) {
      setEdges(eds => eds.filter(e => e.id !== edge.id))
    }
  }, [setEdges])

  const captureChartImage = useCallback(async (format = 'png') => {
    const flowEl = document.querySelector('.react-flow__viewport')
    if (!flowEl) {
      throw new Error('Could not find the chart to export.')
    }

    const visibleNodes = nodes.filter(n => n.type !== 'junction')
    const nodesBounds = getNodesBounds(visibleNodes.length > 0 ? visibleNodes : nodes)
    const padding = 60
    const rawWidth = nodesBounds.width + padding * 2
    const rawHeight = nodesBounds.height + padding * 2

    const ratio = parseFloat(exportAspectRatio)
    let chartWidth, chartHeight
    if (rawHeight / rawWidth > ratio) {
      chartHeight = rawHeight
      chartWidth = chartHeight / ratio
    } else {
      chartWidth = rawWidth
      chartHeight = chartWidth * ratio
    }

    const viewport = getViewportForBounds(
      nodesBounds,
      chartWidth,
      chartHeight,
      0.5,
      2,
      padding
    )

    const strokeWidth = getStrokeWidth(lineWeight)
    const edgePaths = flowEl.querySelectorAll('.react-flow__edge-path')
    const originalStyles = []
    edgePaths.forEach(path => {
      originalStyles.push({
        el: path,
        stroke: path.style.stroke,
        strokeWidth: path.style.strokeWidth,
        attrStroke: path.getAttribute('stroke'),
        attrStrokeWidth: path.getAttribute('stroke-width')
      })
      path.style.stroke = EDGE_COLOR
      path.style.strokeWidth = `${strokeWidth}px`
      path.setAttribute('stroke', EDGE_COLOR)
      path.setAttribute('stroke-width', strokeWidth)
    })

    const styleEl = document.createElement('style')
    styleEl.id = 'export-hide-styles'
    styleEl.textContent = `
      .react-flow__handle { opacity: 0 !important; }
      .react-flow__node button { display: none !important; }
      .react-flow__controls { display: none !important; }
      .react-flow__panel { display: none !important; }
      .react-flow__attribution { display: none !important; }
      .react-flow__node-junction { opacity: 0 !important; }
      .react-flow__edge-path { stroke: ${EDGE_COLOR} !important; stroke-width: ${strokeWidth}px !important; }
    `
    document.head.appendChild(styleEl)

    await new Promise(r => setTimeout(r, 150))

    const restoreStyles = () => {
      document.getElementById('export-hide-styles')?.remove()
      originalStyles.forEach(({ el, stroke, strokeWidth: sw, attrStroke, attrStrokeWidth }) => {
        el.style.stroke = stroke
        el.style.strokeWidth = sw
        if (attrStroke !== null) el.setAttribute('stroke', attrStroke)
        else el.removeAttribute('stroke')
        if (attrStrokeWidth !== null) el.setAttribute('stroke-width', attrStrokeWidth)
        else el.removeAttribute('stroke-width')
      })
    }

    try {
      const captureOpts = {
        width: chartWidth,
        height: chartHeight,
        pixelRatio: 3,
        backgroundColor: '#ffffff',
        style: {
          width: `${chartWidth}px`,
          height: `${chartHeight}px`,
          transform: `translate(${viewport.x}px, ${viewport.y}px) scale(${viewport.zoom})`,
        },
        filter: (node) => {
          if (node?.classList?.contains('react-flow__minimap')) return false
          if (node?.classList?.contains('react-flow__controls')) return false
          return true
        }
      }

      let imgData
      if (format === 'jpeg') {
        imgData = await toJpeg(flowEl, { ...captureOpts, quality: 0.95 })
      } else {
        imgData = await toPng(flowEl, captureOpts)
      }

      restoreStyles()
      return { imgData, chartWidth, chartHeight }
    } catch (err) {
      restoreStyles()
      throw err
    }
  }, [nodes, exportAspectRatio, lineWeight])

  const exportToPdf = useCallback(async () => {
    setIsExportingPdf(true)
    setShowPdfModal(false)

    try {
      const { imgData } = await captureChartImage('png')

      const pdf = new jsPDF({
        orientation: pdfOrientation,
        unit: 'pt',
        format: 'letter'
      })

      const pageWidth = pdf.internal.pageSize.getWidth()
      const pageHeight = pdf.internal.pageSize.getHeight()
      const margin = 30

      const availWidth = pageWidth - margin * 2
      const availHeight = pageHeight - margin * 2

      const img = new Image()
      img.src = imgData
      await new Promise(resolve => { img.onload = resolve })

      const imgRatio = img.width / img.height
      const pageRatio = availWidth / availHeight

      let pdfImgWidth, pdfImgHeight
      if (imgRatio > pageRatio) {
        pdfImgWidth = availWidth
        pdfImgHeight = availWidth / imgRatio
      } else {
        pdfImgHeight = availHeight
        pdfImgWidth = availHeight * imgRatio
      }

      const xOffset = margin + (availWidth - pdfImgWidth) / 2
      const yOffset = margin + (availHeight - pdfImgHeight) / 2

      pdf.addImage(imgData, 'PNG', xOffset, yOffset, pdfImgWidth, pdfImgHeight)

      const chartName = savedCharts.find(c => String(c.id) === String(selectedSavedChartId))?.name
      const fileName = chartName || 'Org Chart'
      pdf.save(`${fileName} - Org Chart.pdf`)
    } catch (err) {
      console.error('PDF export error:', err)
      document.getElementById('export-hide-styles')?.remove()
      alert('Failed to export PDF. Please try again.')
    }

    setIsExportingPdf(false)
  }, [captureChartImage, pdfOrientation, savedCharts, selectedSavedChartId])

  const exportToJpg = useCallback(async () => {
    setIsExportingPdf(true)
    try {
      const { imgData } = await captureChartImage('jpeg')
      const link = document.createElement('a')
      const chartName = savedCharts.find(c => String(c.id) === String(selectedSavedChartId))?.name
      link.download = `${chartName || 'Org Chart'} - Org Chart.jpg`
      link.href = imgData
      link.click()
    } catch (err) {
      console.error('JPG export error:', err)
      document.getElementById('export-hide-styles')?.remove()
      alert('Failed to export JPG. Please try again.')
    }
    setIsExportingPdf(false)
  }, [captureChartImage, savedCharts, selectedSavedChartId])

  const exportToCsv = useCallback(() => {
    const parentMap = {}
    edges.forEach(edge => {
      parentMap[edge.target] = edge.source
    })

    const getParentRole = (nodeId) => {
      let parentId = parentMap[nodeId]
      while (parentId) {
        const parentNode = nodes.find(n => n.id === parentId)
        if (!parentNode) return -1
        if (parentNode.type === 'junction') {
          parentId = parentMap[parentId]
          continue
        }
        return parentNode.data.role || 'Unknown'
      }
      return -1
    }

    const rows = ['"Name","Supervisor","Title"']

    nodes
      .filter(n => n.type !== 'junction')
      .forEach(node => {
        const role = (node.data.role || '').replace(/"/g, '""')
        const supervisor = getParentRole(node.id)
        const supervisorStr = supervisor === -1 ? '-1' : `"${String(supervisor).replace(/"/g, '""')}"`
        const title = (node.data.assignedStaff || '').replace(/"/g, '""')

        rows.push(`"${role}",${supervisorStr},"${title}"`)

        if (node.data.staffList && node.data.staffList.length > 0) {
          node.data.staffList.forEach(member => {
            const memberName = (member.name || '').replace(/"/g, '""')
            rows.push(`"Team Member","${role}","${memberName}"`)
          })
        }
      })

    const csvContent = rows.join('\n')
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    const chartName = savedCharts.find(c => String(c.id) === String(selectedSavedChartId))?.name
    link.href = url
    link.download = `${chartName || 'Org Chart'} - SmartDraw.csv`
    link.click()
    URL.revokeObjectURL(url)
  }, [nodes, edges, savedCharts, selectedSavedChartId])

  useEffect(() => {
    fetch('/api/employees')
      .then(res => res.json())
      .then(data => {
        setStaff(data)
      })
      .catch(err => console.error('Failed to fetch staff:', err))
    
    fetch('/api/firms/list')
      .then(res => res.json())
      .then(data => {
        setFirms(data)
        const colorMap = {}
        const logoMap = {}
        let fallbackIndex = 0
        data.forEach(f => {
          if (f.brand_color) {
            colorMap[f.id] = hexToColorObj(f.brand_color)
          } else {
            colorMap[f.id] = FIRM_COLORS[fallbackIndex % FIRM_COLORS.length]
            fallbackIndex++
          }
          if (f.logo_url) {
            logoMap[f.id] = f.logo_url
          }
        })
        setFirmColorMap(colorMap)
        setFirmLogoMap(logoMap)
        const strinteg = data.find(f => f.name.toLowerCase().includes('strinteg'))
        if (strinteg) {
          setSelectedFirmFilter(String(strinteg.id))
        }
      })
      .catch(err => console.error('Failed to fetch firms:', err))
    
    fetch('/api/saved-orgcharts')
      .then(res => res.json())
      .then(data => setSavedCharts(data))
      .catch(err => console.error('Failed to fetch saved charts:', err))
  }, [])

  const filteredStaff = (selectedFirmFilter
    ? staff.filter(s => String(s.firm_id) === selectedFirmFilter)
    : [...staff].sort((a, b) => {
        const firmA = (a.firm_name || 'zzz').toLowerCase()
        const firmB = (b.firm_name || 'zzz').toLowerCase()
        if (firmA !== firmB) return firmA.localeCompare(firmB)
        return (a.name || '').localeCompare(b.name || '')
      })
  )

  const loadSavedChart = useCallback((chartId) => {
    if (!chartId) return
    
    fetch(`/api/saved-orgcharts/${chartId}`)
      .then(res => res.json())
      .then(data => {
        if (data.org_chart_data) {
          const chartData = JSON.parse(data.org_chart_data)
          setNodes(chartData.nodes || layoutedNodes)
          const loadedWeight = chartData.lineWeight || 'medium'
          const loadedEdges = (chartData.edges || layoutedEdges).map(e => ({
            ...e,
            style: edgeStyle(loadedWeight)
          }))
          setEdges(loadedEdges)
          if (chartData.legendItems) {
            setLegendItems(chartData.legendItems)
          }
          if (chartData.lineWeight) setLineWeight(chartData.lineWeight)
          if (chartData.borderStyle) setBorderStyle(chartData.borderStyle)
          if (chartData.exportAspectRatio) setExportAspectRatio(chartData.exportAspectRatio)
        }
        if (data.org_chart_notes) {
          setGlobalNotes(data.org_chart_notes)
        }
        setSaveStatus(`Loaded: ${data.name}`)
        setTimeout(() => setSaveStatus(''), 2000)
      })
      .catch(err => {
        console.error('Failed to load saved chart:', err)
        setSaveStatus('Failed to load')
        setTimeout(() => setSaveStatus(''), 2000)
      })
  }, [setNodes, setEdges])

  const saveOrgChart = useCallback(() => {
    if (!selectedSavedChartId) {
      setSaveStatus('Select a chart first')
      setTimeout(() => setSaveStatus(''), 2000)
      return
    }

    const chartData = JSON.stringify({ nodes, edges, legendItems, lineWeight, borderStyle, exportAspectRatio })
    
    fetch(`/api/saved-orgcharts/${selectedSavedChartId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        org_chart_data: chartData,
        org_chart_notes: globalNotes
      })
    })
      .then(res => res.json())
      .then(data => {
        setSaveStatus('Saved!')
        setTimeout(() => setSaveStatus(''), 2000)
      })
      .catch(err => {
        console.error('Failed to save chart:', err)
        setSaveStatus('Failed to save')
        setTimeout(() => setSaveStatus(''), 2000)
      })
  }, [selectedSavedChartId, nodes, edges, globalNotes, legendItems, lineWeight, borderStyle, exportAspectRatio])

  const saveAsNewChart = useCallback(() => {
    if (!saveAsName.trim()) return

    const chartData = JSON.stringify({ nodes, edges, legendItems, lineWeight, borderStyle, exportAspectRatio })
    
    fetch('/api/saved-orgcharts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: saveAsName.trim(),
        org_chart_data: chartData,
        org_chart_notes: globalNotes
      })
    })
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          setSaveStatus(`Saved as "${data.name}"`)
          setShowSaveAsModal(false)
          setSaveAsName('')
          setSelectedSavedChartId(String(data.id))
          fetch('/api/saved-orgcharts')
            .then(res => res.json())
            .then(charts => setSavedCharts(charts))
        }
        setTimeout(() => setSaveStatus(''), 2000)
      })
      .catch(err => {
        console.error('Failed to save:', err)
        setSaveStatus('Failed to save')
        setTimeout(() => setSaveStatus(''), 2000)
      })
  }, [saveAsName, nodes, edges, globalNotes, legendItems, lineWeight, borderStyle, exportAspectRatio])

  const deleteSavedChart = useCallback(() => {
    if (!selectedSavedChartId) return
    const chart = savedCharts.find(c => String(c.id) === selectedSavedChartId)
    if (!confirm(`Delete saved chart "${chart?.name}"?`)) return

    fetch(`/api/saved-orgcharts/${selectedSavedChartId}`, { method: 'DELETE' })
      .then(res => res.json())
      .then(() => {
        setSelectedSavedChartId('')
        fetch('/api/saved-orgcharts')
          .then(res => res.json())
          .then(charts => setSavedCharts(charts))
        setSaveStatus('Deleted')
        setTimeout(() => setSaveStatus(''), 2000)
      })
  }, [selectedSavedChartId, savedCharts])

  const handleSavedChartChange = (e) => {
    const chartId = e.target.value
    setSelectedSavedChartId(chartId)
    if (chartId) {
      loadSavedChart(chartId)
    }
  }

  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge({ ...params, type: 'smoothstep', style: edgeStyle(lineWeight) }, eds)),
    [setEdges, lineWeight]
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
                return { ...node, data: { ...node.data, assignedStaff: null, staffId: null, staffFirmId: null, staffFirmName: null } }
              }
              if (node.id === dropTargetNode.id) {
                if (node.data.isTeamMember || node.data.useStaffList) {
                  const currentList = node.data.staffList || []
                  return { ...node, data: { ...node.data, staffList: [...currentList, { name: staffInfo.name, id: staffInfo.staffId, firm_id: staffInfo.firmId, firm_name: staffInfo.firmName }] } }
                }
                return { ...node, data: { ...node.data, assignedStaff: staffInfo.name, staffId: staffInfo.staffId, staffFirmId: staffInfo.firmId, staffFirmName: staffInfo.firmName } }
              }
              return node
            })
          )
        } else if (!dropTargetNode) {
          setNodes((nds) => {
            const updated = nds.map((node) => {
              if (node.id === staffInfo.fromNodeId) {
                return { ...node, data: { ...node.data, assignedStaff: null, staffId: null, staffFirmId: null, staffFirmName: null } }
              }
              return node
            })
            const newNode = {
              id: `node-${Date.now()}`,
              type: 'custom',
              position,
              data: { role: 'New Role', assignedStaff: staffInfo.name, staffId: staffInfo.staffId, staffFirmId: staffInfo.firmId, staffFirmName: staffInfo.firmName },
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
              if (node.data.isTeamMember || node.data.useStaffList) {
                const currentList = node.data.staffList || []
                return {
                  ...node,
                  data: {
                    ...node.data,
                    staffList: [...currentList, { name: staffMember.name, id: staffMember.id, firm_id: staffMember.firm_id, firm_name: staffMember.firm_name }],
                  },
                }
              }
              return {
                ...node,
                data: {
                  ...node.data,
                  assignedStaff: staffMember.name,
                  staffId: staffMember.id,
                  staffFirmId: staffMember.firm_id,
                  staffFirmName: staffMember.firm_name,
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
          data: { role: 'New Role', assignedStaff: staffMember.name, staffId: staffMember.id, staffFirmId: staffMember.firm_id, staffFirmName: staffMember.firm_name, canDelete: true },
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
          return { ...node, data: { ...node.data, assignedStaff: null, staffFirmId: null, staffFirmName: null } }
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

  const addDPM = useCallback((pmNodeId) => {
    const pmNode = nodes.find(n => n.id === pmNodeId)
    if (!pmNode) return

    const newNodeId = `dpm-${Date.now()}`
    const newNode = {
      id: newNodeId,
      type: 'custom',
      position: { x: pmNode.position.x + 220, y: pmNode.position.y },
      data: { 
        role: 'Deputy Project Manager (DPM)', 
        assignedStaff: null, 
        isDPM: true,
        canDelete: true,
        connectFromSide: 'left'
      },
    }
    const newEdge = {
      id: `e-pm-${newNodeId}`,
      source: pmNodeId,
      target: newNodeId,
      sourceHandle: 'bottom',
      targetHandle: 'left',
      type: 'smoothstep',
      style: edgeStyle(lineWeight)
    }
    
    setNodes((nds) => [...nds, newNode])
    setEdges((eds) => [...eds, newEdge])
  }, [nodes, setNodes, setEdges, lineWeight])

  const addTeamMember = useCallback((parentNodeId) => {
    const parentNode = nodes.find(n => n.id === parentNodeId)
    if (!parentNode) return

    const newNodeId = `team-${Date.now()}`
    const newNode = {
      id: newNodeId,
      type: 'custom',
      position: { x: parentNode.position.x, y: parentNode.position.y + 120 },
      data: { 
        role: 'Team Leader', 
        assignedStaff: null, 
        isTeamMember: true,
        parentId: parentNodeId,
        canDelete: true,
        staffList: []
      },
    }
    const newEdge = {
      id: `e-${parentNodeId}-${newNodeId}`,
      source: parentNodeId,
      target: newNodeId,
      type: 'smoothstep',
      style: edgeStyle(lineWeight)
    }
    
    setNodes((nds) => [...nds, newNode])
    setEdges((eds) => [...eds, newEdge])
    
    setTimeout(() => {
      const { nodes: layouted } = getLayoutedElements([...nodes, newNode], [...edges, newEdge])
      setNodes(layouted)
    }, 50)
  }, [nodes, edges, setNodes, setEdges, lineWeight])

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
      type: 'smoothstep',
      style: edgeStyle(lineWeight)
    }
    
    setNodes((nds) => [...nds, newNode])
    setEdges((eds) => [...eds, newEdge])
    
    setTimeout(() => {
      const { nodes: layouted } = getLayoutedElements([...nodes, newNode], [...edges, newEdge])
      setNodes(layouted)
    }, 50)
  }, [nodes, edges, setNodes, setEdges, lineWeight])

  const addChildBranch = useCallback((parentNodeId) => {
    const parentNode = nodes.find(n => n.id === parentNodeId)
    if (!parentNode) return

    const branchName = prompt('Enter branch/role name:', 'New Branch')
    if (!branchName || branchName.trim() === '') return

    const newNodeId = `branch-${Date.now()}`
    const newNode = {
      id: newNodeId,
      type: 'custom',
      position: { x: parentNode.position.x + 50, y: parentNode.position.y + 120 },
      data: { 
        role: branchName.trim(), 
        assignedStaff: null, 
        parentId: parentNodeId,
        canDelete: true,
        useStaffList: true,
        staffList: [],
      },
    }
    const newEdge = {
      id: `e-${parentNodeId}-${newNodeId}`,
      source: parentNodeId,
      target: newNodeId,
      type: 'smoothstep',
      style: edgeStyle(lineWeight)
    }
    
    setNodes((nds) => [...nds, newNode])
    setEdges((eds) => [...eds, newEdge])

    setTimeout(() => {
      const { nodes: layouted } = getLayoutedElements([...nodes, newNode], [...edges, newEdge])
      setNodes(layouted)
    }, 50)
  }, [nodes, edges, setNodes, setEdges, lineWeight])

  const removeStaffFromList = useCallback((nodeId, index) => {
    setNodes((nds) =>
      nds.map((node) => {
        if (node.id === nodeId) {
          const currentList = node.data.staffList || []
          return {
            ...node,
            data: {
              ...node.data,
              staffList: currentList.filter((_, i) => i !== index)
            }
          }
        }
        return node
      })
    )
  }, [setNodes])

  const nodesWithCallbacks = nodes.map(node => ({
    ...node,
    data: {
      ...node.data,
      onAddTeamMember: addTeamMember,
      onDeleteNode: deleteNode,
      onAddDPM: addDPM,
      onRemoveStaffFromList: removeStaffFromList,
      onAddChildBranch: addChildBranch,
      firmColorMap: firmColorMap,
      borderStyle: borderStyle,
    }
  }))

  const legendFirms = [...new Set(
    nodes
      .filter(n => n.data?.staffFirmId)
      .map(n => n.data.staffFirmId)
  )].map(firmId => {
    const staffMember = staff.find(s => s.firm_id === firmId)
    return {
      firmId,
      firmName: staffMember?.firm_name || 'Unknown',
      color: firmColorMap[firmId] || FIRM_COLORS[0],
      logoUrl: firmLogoMap[firmId] || null
    }
  })

  React.useEffect(() => {
    if (legendFirms.length > 0 && legendItems.length === 0) {
      setLegendItems(legendFirms.map((f, i) => ({
        firmId: f.firmId,
        x: 20,
        y: 20 + i * 60,
        width: 180,
        height: 50,
      })))
    }
  }, [legendFirms.length])

  return (
    <div className="flex h-screen w-full">
      <div className="w-64 bg-gray-100 border-r border-gray-300 flex flex-col">
        <div className="p-4 bg-gray-900 text-white">
          <h2 className="text-lg font-bold">Available Staff</h2>
          <p className="text-sm text-gray-400">Drag to assign</p>
        </div>
        <div className="p-2 border-b border-gray-300">
          <select
            value={selectedFirmFilter}
            onChange={(e) => setSelectedFirmFilter(e.target.value)}
            className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:border-red-500"
          >
            <option value="">All Firms</option>
            {firms.map(f => (
              <option key={f.id} value={f.id}>{f.name}</option>
            ))}
          </select>
        </div>
        <div className="flex-1 overflow-y-auto p-2">
          {filteredStaff.length === 0 ? (
            <p className="text-gray-500 text-sm p-2">No staff available{selectedFirmFilter ? ' for this firm' : '. Add employees in the main app.'}.</p>
          ) : (
            filteredStaff.map((person) => {
              const firmColor = firmColorMap[person.firm_id]
              const isInline = firmColor?.useInline
              const sidebarStyle = isInline ? { borderColor: firmColor.hex, backgroundColor: firmColor.hex + '18' } : {}
              const sidebarClass = firmColor ? (isInline ? '' : `${firmColor.border} ${firmColor.bg}`) : 'border-gray-200 bg-white hover:border-red-500'
              const nameStyle = isInline ? { color: firmColor.hex } : {}
              const nameClass = firmColor ? (isInline ? '' : firmColor.text) : 'text-gray-400'
              return (
                <div
                  key={person.id}
                  className={`staff-item p-3 mb-2 rounded shadow hover:shadow-md border-2 transition-all cursor-grab ${sidebarClass}`}
                  style={sidebarStyle}
                  draggable
                  onDragStart={(e) => onDragStart(e, person)}
                >
                  <div className="font-medium text-gray-800 text-sm">{person.name}</div>
                  {person.title && (
                    <div className="text-xs text-gray-500">{person.title}</div>
                  )}
                  {person.firm_name && (
                    <div className={`text-[10px] font-semibold mt-0.5 ${nameClass}`} style={nameStyle}>
                      {person.firm_name}
                    </div>
                  )}
                </div>
              )
            })
          )}
        </div>
      </div>

      <div className={`flex-1 relative line-weight-${lineWeight}`} ref={reactFlowWrapper}>
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
          onEdgeClick={onEdgeClick}
          onEdgeContextMenu={onEdgeContextMenu}
          nodeTypes={nodeTypes}
          fitView
          defaultEdgeOptions={{ type: 'smoothstep', style: edgeStyle(lineWeight) }}
          edgesReconnectable
        >
          <Controls />
          <Background variant="dots" gap={12} size={1} />
          <Panel position="top-left" className="bg-white p-3 rounded shadow max-w-sm">
            <div className="flex flex-col gap-2">
              <button
                onClick={() => {
                  if (window.history.length > 1) {
                    window.history.back();
                  } else {
                    window.location.href = window.location.origin;
                  }
                }}
                className="flex items-center gap-1.5 text-sm text-gray-600 hover:text-gray-900 mb-1 font-medium cursor-pointer bg-transparent border-none p-0"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
                Back to SF330
              </button>
              <div className="flex items-center gap-1">
                <select
                  value={selectedSavedChartId}
                  onChange={handleSavedChartChange}
                  className="flex-1 px-2 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:border-red-500"
                >
                  <option value="">Open Saved Chart...</option>
                  {savedCharts.map(c => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
                {selectedSavedChartId && (
                  <button
                    onClick={deleteSavedChart}
                    className="px-2 py-1.5 bg-red-100 text-red-600 rounded text-xs hover:bg-red-200"
                    title="Delete saved chart"
                  >
                    ×
                  </button>
                )}
              </div>

              <div className="flex items-center gap-1">
                <button
                  onClick={saveOrgChart}
                  disabled={!selectedSavedChartId}
                  className={`flex-1 px-3 py-1.5 rounded shadow font-medium transition-colors text-sm ${
                    selectedSavedChartId
                      ? 'bg-green-600 text-white hover:bg-green-700' 
                      : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  }`}
                >
                  Save
                </button>
                <button
                  onClick={() => setShowSaveAsModal(true)}
                  className="px-3 py-1.5 bg-blue-600 text-white rounded shadow font-medium hover:bg-blue-700 transition-colors text-sm"
                  title="Save as new chart with a custom name"
                >
                  Save As...
                </button>
              </div>

              {saveStatus && (
                <span className={`text-xs font-medium ${
                  saveStatus.includes('Failed') ? 'text-red-600' : 'text-green-600'
                }`}>
                  {saveStatus}
                </span>
              )}
            </div>
          </Panel>

          <Panel position="top-right" className="flex flex-col gap-2 items-end">
            <div className="flex gap-2 flex-wrap justify-end">
              <button
                onClick={addNewServiceType}
                className="px-3 py-2 bg-red-600 text-white rounded shadow hover:bg-red-700 transition-colors font-medium text-sm"
              >
                + Add Service Type
              </button>
              <button
                onClick={() => setShowPdfModal(true)}
                disabled={isExportingPdf}
                className={`px-3 py-2 rounded shadow transition-colors font-medium text-sm ${
                  isExportingPdf
                    ? 'bg-gray-400 text-gray-200 cursor-not-allowed'
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                }`}
              >
                {isExportingPdf ? 'Exporting...' : 'Save PDF'}
              </button>
              <button
                onClick={exportToJpg}
                disabled={isExportingPdf}
                className={`px-3 py-2 rounded shadow transition-colors font-medium text-sm ${
                  isExportingPdf
                    ? 'bg-gray-400 text-gray-200 cursor-not-allowed'
                    : 'bg-amber-600 text-white hover:bg-amber-700'
                }`}
              >
                Save JPG
              </button>
              <button
                onClick={exportToCsv}
                className="px-3 py-2 bg-emerald-600 text-white rounded shadow hover:bg-emerald-700 transition-colors font-medium text-sm"
              >
                CSV Export
              </button>
              <button
                onClick={onResetLayout}
                className="px-3 py-2 bg-gray-800 text-white rounded shadow hover:bg-gray-900 transition-colors font-medium text-sm"
              >
                Reset Layout
              </button>
            </div>
            <div className="flex gap-2 flex-wrap justify-end items-center">
              <div className="flex rounded shadow overflow-hidden">
                <button
                  onClick={() => switchConnectionDirection('top-bottom')}
                  className={`px-2 py-1.5 text-xs font-medium transition-colors ${connectionDirection === 'top-bottom' ? 'bg-indigo-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-100'}`}
                  title="Connect nodes top to bottom (vertical)"
                >
                  ↓ Top-Down
                </button>
                <button
                  onClick={() => switchConnectionDirection('left-side')}
                  className={`px-2 py-1.5 text-xs font-medium border-l transition-colors ${connectionDirection === 'left-side' ? 'bg-indigo-600 text-white border-indigo-700' : 'bg-white text-gray-700 hover:bg-gray-100 border-gray-300'}`}
                  title="Connect all nodes from left side"
                >
                  ← Left
                </button>
                <button
                  onClick={() => switchConnectionDirection('right-side')}
                  className={`px-2 py-1.5 text-xs font-medium border-l transition-colors ${connectionDirection === 'right-side' ? 'bg-indigo-600 text-white border-indigo-700' : 'bg-white text-gray-700 hover:bg-gray-100 border-gray-300'}`}
                  title="Connect all nodes from right side"
                >
                  Right →
                </button>
              </div>
              <div className="flex rounded shadow overflow-hidden" title="Line Weight">
                {[{k:'thin',l:'Thin'},{k:'medium',l:'Med'},{k:'thick',l:'Thick'}].map(w => (
                  <button
                    key={w.k}
                    onClick={() => setLineWeight(w.k)}
                    className={`px-2 py-1.5 text-xs font-medium transition-colors ${w.k !== 'thin' ? 'border-l' : ''} ${lineWeight === w.k ? 'bg-gray-800 text-white' : 'bg-white text-gray-700 hover:bg-gray-100 border-gray-300'}`}
                  >
                    {w.l}
                  </button>
                ))}
              </div>
              <div className="flex rounded shadow overflow-hidden" title="Border Style">
                {[{k:'default',l:'Default'},{k:'firm-colors',l:'Firm Colors'},{k:'black',l:'Black'},{k:'none',l:'None'}].map(b => (
                  <button
                    key={b.k}
                    onClick={() => setBorderStyle(b.k)}
                    className={`px-2 py-1.5 text-xs font-medium transition-colors ${b.k !== 'default' ? 'border-l' : ''} ${borderStyle === b.k ? 'bg-teal-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-100 border-gray-300'}`}
                  >
                    {b.l}
                  </button>
                ))}
              </div>
              <div className="flex rounded shadow overflow-hidden" title="Export Aspect Ratio (H:W)">
                {[{k:'0.773',l:'.773'},{k:'0.647',l:'.647'}].map(r => (
                  <button
                    key={r.k}
                    onClick={() => setExportAspectRatio(r.k)}
                    className={`px-2 py-1.5 text-xs font-medium transition-colors ${r.k !== '0.773' ? 'border-l' : ''} ${exportAspectRatio === r.k ? 'bg-purple-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-100 border-gray-300'}`}
                  >
                    {r.l}
                  </button>
                ))}
              </div>
            </div>
          </Panel>

          {legendFirms.length > 0 && (
            <Panel position="bottom-left" className="flex flex-col gap-0.5" style={{ pointerEvents: 'none' }}>
              <div className="text-[10px] font-bold text-gray-500 mb-0.5 pointer-events-none">Click &amp; drag legend items to reposition. Drag corner to resize.</div>
            </Panel>
          )}
        </ReactFlow>

        {legendFirms.map((firm) => {
          const item = legendItems.find(l => l.firmId === firm.firmId)
          if (!item) return null
          const borderColor = firm.color.useInline ? firm.color.hex : undefined
          const borderClass = firm.color.useInline ? '' : (firm.color.border || 'border-gray-300')
          return (
            <div
              key={`legend-${firm.firmId}`}
              className={`absolute bg-white rounded shadow-md border-2 flex items-center gap-2 p-2 cursor-move select-none overflow-hidden ${borderClass}`}
              style={{
                left: item.x,
                top: item.y,
                width: item.width,
                height: item.height,
                borderColor,
                zIndex: 50,
              }}
              onMouseDown={(e) => {
                if (e.target.dataset.resize) return
                e.preventDefault()
                const startX = e.clientX
                const startY = e.clientY
                const origX = item.x
                const origY = item.y
                const onMove = (ev) => {
                  setLegendItems(prev => prev.map(li =>
                    li.firmId === firm.firmId
                      ? { ...li, x: origX + (ev.clientX - startX), y: origY + (ev.clientY - startY) }
                      : li
                  ))
                }
                const onUp = () => {
                  document.removeEventListener('mousemove', onMove)
                  document.removeEventListener('mouseup', onUp)
                }
                document.addEventListener('mousemove', onMove)
                document.addEventListener('mouseup', onUp)
              }}
            >
              {firm.logoUrl && (
                <img
                  src={firm.logoUrl}
                  alt={firm.firmName}
                  className="object-contain flex-shrink-0"
                  style={{ maxHeight: item.height - 12, maxWidth: item.width * 0.4 }}
                  draggable={false}
                />
              )}
              {!firm.logoUrl && (
                <div
                  className={`w-5 h-5 rounded flex-shrink-0 ${firm.color.useInline ? '' : firm.color.label}`}
                  style={firm.color.useInline ? firm.color.labelStyle : {}}
                />
              )}
              <span className="text-xs font-semibold text-gray-800 truncate leading-tight">{firm.firmName}</span>
              <div
                data-resize="true"
                className="absolute bottom-0 right-0 w-4 h-4 cursor-se-resize"
                style={{ background: 'linear-gradient(135deg, transparent 50%, #9ca3af 50%)' }}
                onMouseDown={(e) => {
                  e.preventDefault()
                  e.stopPropagation()
                  const startX = e.clientX
                  const startY = e.clientY
                  const origW = item.width
                  const origH = item.height
                  const onMove = (ev) => {
                    setLegendItems(prev => prev.map(li =>
                      li.firmId === firm.firmId
                        ? { ...li, width: Math.max(80, origW + (ev.clientX - startX)), height: Math.max(30, origH + (ev.clientY - startY)) }
                        : li
                    ))
                  }
                  const onUp = () => {
                    document.removeEventListener('mousemove', onMove)
                    document.removeEventListener('mouseup', onUp)
                  }
                  document.addEventListener('mousemove', onMove)
                  document.addEventListener('mouseup', onUp)
                }}
              />
            </div>
          )
        })}
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
            nodes.filter(n => n.data?.assignedStaff).map((node) => {
              const firmColor = firmColorMap[node.data.staffFirmId]
              const isInline = firmColor?.useInline
              const assignedBorderStyle = isInline ? { borderLeftColor: firmColor.hex } : {}
              const assignedBorderClass = firmColor ? (isInline ? 'bg-white' : `${firmColor.border} bg-white`) : 'border-gray-300 bg-white'
              const assignedTextStyle = isInline ? firmColor.textStyle : {}
              const assignedTextClass = firmColor ? (isInline ? '' : firmColor.text) : 'text-red-600'
              return (
                <div
                  key={node.id}
                  className={`p-3 mb-2 rounded shadow border-l-4 ${assignedBorderClass}`}
                  style={assignedBorderStyle}
                >
                  <div className="font-medium text-gray-800 text-sm">{node.data.role}</div>
                  <div className={`text-xs font-medium ${assignedTextClass}`} style={assignedTextStyle}>{node.data.assignedStaff}</div>
                  {node.data.staffFirmName && (
                    <div className="text-[10px] text-gray-400">{node.data.staffFirmName}</div>
                  )}
                  <button
                    onClick={() => removeStaffFromNode(node.id)}
                    className="mt-1 text-xs text-gray-500 hover:text-red-600"
                  >
                    Remove
                  </button>
                </div>
              )
            })
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
              className="w-full h-24 p-2 border border-gray-300 rounded text-sm focus:outline-none focus:border-red-500 resize-none"
            />
          </div>
        </div>
      </div>

      {showPdfModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 w-96">
            <h3 className="text-lg font-bold text-gray-800 mb-4">Export Org Chart to PDF</h3>
            <p className="text-sm text-gray-600 mb-4">Choose the page orientation for your PDF:</p>
            <div className="flex gap-4 mb-6">
              <label
                className={`flex-1 flex flex-col items-center gap-2 p-4 border-2 rounded-lg cursor-pointer transition-colors ${
                  pdfOrientation === 'landscape' ? 'border-blue-600 bg-blue-50' : 'border-gray-300 hover:border-gray-400'
                }`}
              >
                <input
                  type="radio"
                  name="pdfOrientation"
                  value="landscape"
                  checked={pdfOrientation === 'landscape'}
                  onChange={() => setPdfOrientation('landscape')}
                  className="sr-only"
                />
                <div className={`w-16 h-10 border-2 rounded ${pdfOrientation === 'landscape' ? 'border-blue-600 bg-blue-100' : 'border-gray-400 bg-gray-100'}`}></div>
                <span className={`text-sm font-medium ${pdfOrientation === 'landscape' ? 'text-blue-700' : 'text-gray-600'}`}>Landscape</span>
              </label>
              <label
                className={`flex-1 flex flex-col items-center gap-2 p-4 border-2 rounded-lg cursor-pointer transition-colors ${
                  pdfOrientation === 'portrait' ? 'border-blue-600 bg-blue-50' : 'border-gray-300 hover:border-gray-400'
                }`}
              >
                <input
                  type="radio"
                  name="pdfOrientation"
                  value="portrait"
                  checked={pdfOrientation === 'portrait'}
                  onChange={() => setPdfOrientation('portrait')}
                  className="sr-only"
                />
                <div className={`w-10 h-14 border-2 rounded ${pdfOrientation === 'portrait' ? 'border-blue-600 bg-blue-100' : 'border-gray-400 bg-gray-100'}`}></div>
                <span className={`text-sm font-medium ${pdfOrientation === 'portrait' ? 'text-blue-700' : 'text-gray-600'}`}>Portrait</span>
              </label>
            </div>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowPdfModal(false)}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
              >
                Cancel
              </button>
              <button
                onClick={exportToPdf}
                className="px-4 py-2 bg-blue-600 text-white rounded font-medium hover:bg-blue-700"
              >
                Export PDF
              </button>
            </div>
          </div>
        </div>
      )}

      {showSaveAsModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 w-96">
            <h3 className="text-lg font-bold text-gray-800 mb-4">Save Org Chart As</h3>
            <input
              type="text"
              value={saveAsName}
              onChange={(e) => setSaveAsName(e.target.value)}
              placeholder="Enter chart name..."
              className="w-full px-3 py-2 border border-gray-300 rounded mb-4 focus:outline-none focus:border-red-500"
              autoFocus
              onKeyDown={(e) => { if (e.key === 'Enter') saveAsNewChart() }}
            />
            <div className="flex justify-end gap-2">
              <button
                onClick={() => { setShowSaveAsModal(false); setSaveAsName('') }}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
              >
                Cancel
              </button>
              <button
                onClick={saveAsNewChart}
                disabled={!saveAsName.trim()}
                className={`px-4 py-2 rounded font-medium ${
                  saveAsName.trim() ? 'bg-blue-600 text-white hover:bg-blue-700' : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                }`}
              >
                Save
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default function App() {
  return (
    <ReactFlowProvider>
      <OrgChartFlow />
    </ReactFlowProvider>
  )
}
