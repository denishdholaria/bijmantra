/**
 * 3D Breeding Simulator Visualization
 * Interactive simulation of breeding populations in 3D genetic space
 */
import { useRef, useState, useMemo, useEffect } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls, Text, Html, Line } from '@react-three/drei'
import * as THREE from 'three'

interface Individual {
  id: string
  x: number  // Trait 1 (e.g., Yield)
  y: number  // Trait 2 (e.g., Quality)
  z: number  // Trait 3 (e.g., Resistance)
  generation: number
  selected: boolean
  fitness: number
}

interface SimulationState {
  generation: number
  population: Individual[]
  selectionIntensity: number
  heritability: number
  isRunning: boolean
}

interface BreedingSimulator3DProps {
  state: SimulationState
  onIndividualClick?: (individual: Individual) => void
  showTrails?: boolean
}

// Generate random individual
function generateIndividual(id: string, generation: number, parents?: Individual[]): Individual {
  let x, y, z
  
  if (parents && parents.length >= 2) {
    // Offspring: midparent value + random variation
    const [p1, p2] = parents
    const h2 = 0.5 // heritability
    x = (p1.x + p2.x) / 2 + (Math.random() - 0.5) * (1 - h2) * 2
    y = (p1.y + p2.y) / 2 + (Math.random() - 0.5) * (1 - h2) * 2
    z = (p1.z + p2.z) / 2 + (Math.random() - 0.5) * (1 - h2) * 2
  } else {
    // Random founder
    x = (Math.random() - 0.5) * 4
    y = (Math.random() - 0.5) * 4
    z = (Math.random() - 0.5) * 4
  }
  
  // Clamp to bounds
  x = Math.max(-2, Math.min(2, x))
  y = Math.max(-2, Math.min(2, y))
  z = Math.max(-2, Math.min(2, z))
  
  // Fitness = distance to ideal (2, 2, 2)
  const fitness = Math.sqrt((2 - x) ** 2 + (2 - y) ** 2 + (2 - z) ** 2)
  
  return { id, x, y, z, generation, selected: false, fitness }
}

// Population cloud component
function PopulationCloud({ 
  population, 
  onIndividualClick,
  showTrails
}: { 
  population: Individual[]
  onIndividualClick?: (ind: Individual) => void
  showTrails?: boolean
}) {
  const pointsRef = useRef<THREE.Points>(null)
  const [hovered, setHovered] = useState<string | null>(null)
  
  // Create positions and colors arrays
  const { positions, colors, sizes } = useMemo(() => {
    const pos = new Float32Array(population.length * 3)
    const col = new Float32Array(population.length * 3)
    const siz = new Float32Array(population.length)
    
    population.forEach((ind, i) => {
      pos[i * 3] = ind.x
      pos[i * 3 + 1] = ind.y
      pos[i * 3 + 2] = ind.z
      
      // Color based on fitness (green = high, red = low)
      const fitnessNorm = 1 - Math.min(ind.fitness / 6, 1)
      col[i * 3] = 1 - fitnessNorm     // R
      col[i * 3 + 1] = fitnessNorm     // G
      col[i * 3 + 2] = 0.3             // B
      
      // Size based on selection
      siz[i] = ind.selected ? 0.15 : 0.08
    })
    
    return { positions: pos, colors: col, sizes: siz }
  }, [population])

  // Animate points
  useFrame((state) => {
    if (pointsRef.current) {
      pointsRef.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.1) * 0.1
    }
  })

  // Create geometry with attributes
  const geometry = useMemo(() => {
    const geo = new THREE.BufferGeometry()
    geo.setAttribute('position', new THREE.BufferAttribute(positions, 3))
    geo.setAttribute('color', new THREE.BufferAttribute(colors, 3))
    return geo
  }, [positions, colors])

  return (
    <group>
      <points ref={pointsRef} geometry={geometry}>
        <pointsMaterial
          size={0.1}
          vertexColors
          transparent
          opacity={0.8}
          sizeAttenuation
        />
      </points>
      
      {/* Selected individuals as larger spheres */}
      {population.filter(ind => ind.selected).map(ind => (
        <mesh key={ind.id} position={[ind.x, ind.y, ind.z]}>
          <sphereGeometry args={[0.08, 16, 16]} />
          <meshStandardMaterial color="#22c55e" emissive="#22c55e" emissiveIntensity={0.5} />
        </mesh>
      ))}
    </group>
  )
}


// Axis labels and grid
function AxisLabels() {
  return (
    <group>
      {/* X axis - Yield */}
      <Text position={[2.5, 0, 0]} fontSize={0.2} color="#ef4444">
        Yield →
      </Text>
      
      {/* Y axis - Quality */}
      <Text position={[0, 2.5, 0]} fontSize={0.2} color="#22c55e">
        Quality →
      </Text>
      
      {/* Z axis - Resistance */}
      <Text position={[0, 0, 2.5]} fontSize={0.2} color="#3b82f6">
        Resistance →
      </Text>
      
      {/* Target point */}
      <mesh position={[2, 2, 2]}>
        <sphereGeometry args={[0.15, 32, 32]} />
        <meshStandardMaterial color="#fbbf24" emissive="#fbbf24" emissiveIntensity={0.8} />
      </mesh>
      <Text position={[2, 2.4, 2]} fontSize={0.15} color="#fbbf24">
        🎯 Ideal
      </Text>
      
      {/* Grid */}
      <gridHelper args={[6, 12, '#334155', '#1e293b']} rotation={[0, 0, 0]} position={[0, -2, 0]} />
      <gridHelper args={[6, 12, '#334155', '#1e293b']} rotation={[Math.PI / 2, 0, 0]} position={[0, 0, -2]} />
    </group>
  )
}

// Generation history trail
function GenerationTrail({ history }: { history: { gen: number; meanX: number; meanY: number; meanZ: number }[] }) {
  const points = useMemo(() => {
    if (history.length < 2) return null
    
    const pts = history.map(h => new THREE.Vector3(h.meanX, h.meanY, h.meanZ))
    const curve = new THREE.CatmullRomCurve3(pts)
    return curve.getPoints(50)
  }, [history])
  
  if (!points) return null
  
  return (
    <Line
      points={points}
      color="#fbbf24"
      lineWidth={2}
      transparent
      opacity={0.6}
    />
  )
}

// Main scene
function SimulatorScene({ state, onIndividualClick, showTrails }: BreedingSimulator3DProps) {
  const [history, setHistory] = useState<{ gen: number; meanX: number; meanY: number; meanZ: number }[]>([])
  
  // Track generation history
  useEffect(() => {
    if (state.population.length > 0) {
      const meanX = state.population.reduce((s, i) => s + i.x, 0) / state.population.length
      const meanY = state.population.reduce((s, i) => s + i.y, 0) / state.population.length
      const meanZ = state.population.reduce((s, i) => s + i.z, 0) / state.population.length
      
      setHistory(prev => {
        const newHistory = [...prev, { gen: state.generation, meanX, meanY, meanZ }]
        return newHistory.slice(-20) // Keep last 20 generations
      })
    }
  }, [state.generation, state.population])

  return (
    <>
      {/* Lighting */}
      <ambientLight intensity={0.4} />
      <pointLight position={[10, 10, 10]} intensity={1} />
      <pointLight position={[-10, -10, 10]} intensity={0.5} color="#3b82f6" />
      
      {/* Axis labels and grid */}
      <AxisLabels />
      
      {/* Population */}
      <PopulationCloud 
        population={state.population} 
        onIndividualClick={onIndividualClick}
        showTrails={showTrails}
      />
      
      {/* Generation trail */}
      {showTrails && <GenerationTrail history={history} />}
      
      {/* Camera controls */}
      <OrbitControls 
        enablePan={true}
        enableZoom={true}
        enableRotate={true}
        autoRotate={state.isRunning}
        autoRotateSpeed={0.5}
        minDistance={4}
        maxDistance={15}
      />
    </>
  )
}

// Main exported component
export function BreedingSimulator3D({ state, onIndividualClick, showTrails = true }: BreedingSimulator3DProps) {
  return (
    <div className="w-full h-full min-h-[500px] bg-slate-900 rounded-lg overflow-hidden relative">
      <Canvas
        camera={{ position: [5, 5, 5], fov: 50 }}
        gl={{ antialias: true }}
      >
        <color attach="background" args={['#0f172a']} />
        <fog attach="fog" args={['#0f172a', 8, 20]} />
        <SimulatorScene
          state={state}
          onIndividualClick={onIndividualClick}
          showTrails={showTrails}
        />
      </Canvas>
      
      {/* Generation indicator */}
      <div className="absolute top-4 left-4 bg-background/80 backdrop-blur rounded-lg p-3">
        <p className="text-2xl font-bold text-primary">Gen {state.generation}</p>
        <p className="text-xs text-muted-foreground">Population: {state.population.length}</p>
        <p className="text-xs text-muted-foreground">Selected: {state.population.filter(i => i.selected).length}</p>
      </div>
      
      {/* Legend */}
      <div className="absolute bottom-4 left-4 bg-background/80 backdrop-blur rounded-lg p-3 text-xs">
        <p className="font-bold mb-2">Fitness Color</p>
        <div className="flex items-center gap-2">
          <div className="w-16 h-2 rounded bg-gradient-to-r from-red-500 to-green-500" />
        </div>
        <div className="flex justify-between text-muted-foreground mt-1">
          <span>Low</span>
          <span>High</span>
        </div>
      </div>
      
      {/* Status */}
      {state.isRunning && (
        <div className="absolute top-4 right-4 bg-green-500/20 border border-green-500 rounded-lg px-3 py-1">
          <p className="text-green-500 text-sm font-medium animate-pulse">● Simulating...</p>
        </div>
      )}
    </div>
  )
}

export { generateIndividual }
export type { Individual, SimulationState }
