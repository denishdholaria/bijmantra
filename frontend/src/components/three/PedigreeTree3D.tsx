/**
 * 3D Pedigree Tree Visualization
 * Interactive 3D visualization of germplasm lineage using Three.js
 */
import { useRef, useState, useMemo, useCallback } from 'react'
import { Canvas, useFrame, ThreeEvent } from '@react-three/fiber'
import { OrbitControls, Text, Line, Html } from '@react-three/drei'
import * as THREE from 'three'

interface PedigreeNode {
  id: string
  name: string
  generation: number
  type: 'root' | 'parent' | 'offspring'
  x?: number
  y?: number
  z?: number
  parentIds?: string[]
  traits?: string[]
  year?: number
}

interface PedigreeEdge {
  from: string
  to: string
}

interface PedigreeTree3DProps {
  nodes: PedigreeNode[]
  edges: PedigreeEdge[]
  onNodeClick?: (node: PedigreeNode) => void
  selectedNodeId?: string
}

// Individual node sphere component
function NodeSphere({ 
  node, 
  position, 
  isSelected, 
  isHovered,
  onClick, 
  onHover 
}: { 
  node: PedigreeNode
  position: [number, number, number]
  isSelected: boolean
  isHovered: boolean
  onClick: () => void
  onHover: (hovered: boolean) => void
}) {
  const meshRef = useRef<THREE.Mesh>(null)
  
  // Animate on hover/select
  useFrame(() => {
    if (meshRef.current) {
      const targetScale = isSelected ? 1.4 : isHovered ? 1.2 : 1
      meshRef.current.scale.lerp(new THREE.Vector3(targetScale, targetScale, targetScale), 0.1)
    }
  })

  // Color based on generation and type
  const color = useMemo(() => {
    if (isSelected) return '#22c55e' // green
    if (node.type === 'root') return '#3b82f6' // blue
    if (node.generation <= 1) return '#8b5cf6' // purple (F1)
    if (node.generation <= 3) return '#f59e0b' // amber (F2-F3)
    return '#06b6d4' // cyan (later generations)
  }, [node, isSelected])

  return (
    <group position={position}>
      <mesh
        ref={meshRef}
        onClick={(e: ThreeEvent<MouseEvent>) => { e.stopPropagation(); onClick() }}
        onPointerOver={() => onHover(true)}
        onPointerOut={() => onHover(false)}
      >
        <sphereGeometry args={[0.3, 32, 32]} />
        <meshStandardMaterial 
          color={color} 
          emissive={isHovered ? color : '#000000'}
          emissiveIntensity={isHovered ? 0.3 : 0}
        />
      </mesh>
      
      {/* Label */}
      <Text
        position={[0, 0.5, 0]}
        fontSize={0.2}
        color="#ffffff"
        anchorX="center"
        anchorY="bottom"
      >
        {node.name}
      </Text>
      
      {/* Generation indicator */}
      <Text
        position={[0, -0.5, 0]}
        fontSize={0.12}
        color="#94a3b8"
        anchorX="center"
        anchorY="top"
      >
        {node.type === 'root' ? 'Root' : `F${node.generation}`}
      </Text>

      {/* Info popup on hover */}
      {isHovered && (
        <Html position={[0.5, 0.5, 0]} distanceFactor={10}>
          <div className="bg-background/95 backdrop-blur border rounded-lg p-2 shadow-lg min-w-[120px]">
            <p className="font-bold text-sm">{node.name}</p>
            <p className="text-xs text-muted-foreground">Gen: F{node.generation}</p>
            {node.year && <p className="text-xs text-muted-foreground">Year: {node.year}</p>}
            {node.traits && node.traits.length > 0 && (
              <p className="text-xs text-primary mt-1">{node.traits.slice(0, 2).join(', ')}</p>
            )}
          </div>
        </Html>
      )}
    </group>
  )
}

// Connection line between nodes
function ConnectionLine({ 
  start, 
  end, 
  isHighlighted 
}: { 
  start: [number, number, number]
  end: [number, number, number]
  isHighlighted: boolean
}) {
  const points = useMemo(() => {
    // Create a curved line using quadratic bezier
    const midY = (start[1] + end[1]) / 2
    const controlPoint: [number, number, number] = [
      (start[0] + end[0]) / 2,
      midY - 0.5,
      (start[2] + end[2]) / 2
    ]
    
    const curve = new THREE.QuadraticBezierCurve3(
      new THREE.Vector3(...start),
      new THREE.Vector3(...controlPoint),
      new THREE.Vector3(...end)
    )
    
    return curve.getPoints(20)
  }, [start, end])

  return (
    <Line
      points={points}
      color={isHighlighted ? '#22c55e' : '#64748b'}
      lineWidth={isHighlighted ? 3 : 1.5}
      opacity={isHighlighted ? 1 : 0.6}
      transparent
    />
  )
}

// Main scene component
function PedigreeScene({ 
  nodes, 
  edges, 
  onNodeClick, 
  selectedNodeId 
}: PedigreeTree3DProps) {
  const [hoveredNodeId, setHoveredNodeId] = useState<string | null>(null)
  
  // Calculate node positions in 3D space
  const positionedNodes = useMemo(() => {
    const nodeMap = new Map<string, PedigreeNode & { position: [number, number, number] }>()
    
    // Group nodes by generation
    const generations = new Map<number, PedigreeNode[]>()
    nodes.forEach(node => {
      const gen = node.generation
      if (!generations.has(gen)) generations.set(gen, [])
      generations.get(gen)!.push(node)
    })
    
    // Position nodes in a tree layout
    const sortedGens = Array.from(generations.keys()).sort((a, b) => a - b)
    
    sortedGens.forEach((gen, genIndex) => {
      const genNodes = generations.get(gen)!
      const yPos = -genIndex * 2 // Generations go down
      
      genNodes.forEach((node, nodeIndex) => {
        const totalInGen = genNodes.length
        const xSpread = Math.max(totalInGen - 1, 1) * 1.5
        const xPos = totalInGen === 1 ? 0 : (nodeIndex / (totalInGen - 1) - 0.5) * xSpread
        const zPos = (Math.random() - 0.5) * 0.5 // Slight z variation
        
        nodeMap.set(node.id, {
          ...node,
          position: [xPos, yPos, zPos]
        })
      })
    })
    
    return nodeMap
  }, [nodes])

  // Get highlighted edges (connected to selected/hovered node)
  const highlightedEdges = useMemo(() => {
    const activeId = selectedNodeId || hoveredNodeId
    if (!activeId) return new Set<string>()
    
    const highlighted = new Set<string>()
    edges.forEach(edge => {
      if (edge.from === activeId || edge.to === activeId) {
        highlighted.add(`${edge.from}-${edge.to}`)
      }
    })
    return highlighted
  }, [edges, selectedNodeId, hoveredNodeId])

  return (
    <>
      {/* Lighting */}
      <ambientLight intensity={0.5} />
      <pointLight position={[10, 10, 10]} intensity={1} />
      <pointLight position={[-10, -10, -10]} intensity={0.5} />
      
      {/* Connection lines */}
      {edges.map(edge => {
        const fromNode = positionedNodes.get(edge.from)
        const toNode = positionedNodes.get(edge.to)
        if (!fromNode || !toNode) return null
        
        const edgeKey = `${edge.from}-${edge.to}`
        return (
          <ConnectionLine
            key={edgeKey}
            start={fromNode.position}
            end={toNode.position}
            isHighlighted={highlightedEdges.has(edgeKey)}
          />
        )
      })}
      
      {/* Nodes */}
      {Array.from(positionedNodes.values()).map(node => (
        <NodeSphere
          key={node.id}
          node={node}
          position={node.position}
          isSelected={selectedNodeId === node.id}
          isHovered={hoveredNodeId === node.id}
          onClick={() => onNodeClick?.(node)}
          onHover={(hovered) => setHoveredNodeId(hovered ? node.id : null)}
        />
      ))}
      
      {/* Camera controls */}
      <OrbitControls 
        enablePan={true}
        enableZoom={true}
        enableRotate={true}
        minDistance={3}
        maxDistance={20}
      />
    </>
  )
}


// Main exported component
export function PedigreeTree3D({ nodes, edges, onNodeClick, selectedNodeId }: PedigreeTree3DProps) {
  return (
    <div className="w-full h-full min-h-[500px] bg-slate-900 rounded-lg overflow-hidden">
      <Canvas
        camera={{ position: [0, 0, 8], fov: 50 }}
        gl={{ antialias: true }}
      >
        <color attach="background" args={['#0f172a']} />
        <fog attach="fog" args={['#0f172a', 10, 30]} />
        <PedigreeScene
          nodes={nodes}
          edges={edges}
          onNodeClick={onNodeClick}
          selectedNodeId={selectedNodeId}
        />
      </Canvas>
      
      {/* Legend */}
      <div className="absolute bottom-4 left-4 bg-background/80 backdrop-blur rounded-lg p-3 text-xs">
        <p className="font-bold mb-2">Legend</p>
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-blue-500" />
            <span>Root/Founder</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-purple-500" />
            <span>F1 Generation</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-amber-500" />
            <span>F2-F3 Generation</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-cyan-500" />
            <span>Later Generations</span>
          </div>
        </div>
      </div>
      
      {/* Controls hint */}
      <div className="absolute top-4 right-4 bg-background/80 backdrop-blur rounded-lg p-2 text-xs text-muted-foreground">
        <p>🖱️ Drag to rotate</p>
        <p>🔍 Scroll to zoom</p>
        <p>👆 Click node for details</p>
      </div>
    </div>
  )
}

export type { PedigreeNode, PedigreeEdge }
