/**
 * Inspiration Scene - 3D Ambient Background
 * Floating particles, stars, and gentle animations for the Inspiration Museum
 * Creates a contemplative, late-night atmosphere
 */
import { useRef, useMemo } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { Points, PointMaterial } from '@react-three/drei'
import * as THREE from 'three'

// Floating particles (stars/fireflies)
function StarField({ count = 2000 }: { count?: number }) {
  const ref = useRef<THREE.Points>(null)
  
  const positions = useMemo(() => {
    const pos = new Float32Array(count * 3)
    for (let i = 0; i < count; i++) {
      // Spread particles in a sphere
      const theta = Math.random() * Math.PI * 2
      const phi = Math.acos(2 * Math.random() - 1)
      const r = 5 + Math.random() * 15
      
      pos[i * 3] = r * Math.sin(phi) * Math.cos(theta)
      pos[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta)
      pos[i * 3 + 2] = r * Math.cos(phi)
    }
    return pos
  }, [count])

  useFrame((state) => {
    if (ref.current) {
      // Gentle rotation
      ref.current.rotation.y = state.clock.elapsedTime * 0.02
      ref.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.01) * 0.1
    }
  })

  return (
    <Points ref={ref} positions={positions} stride={3} frustumCulled={false}>
      <PointMaterial
        transparent
        color="#fbbf24"
        size={0.03}
        sizeAttenuation={true}
        depthWrite={false}
        opacity={0.8}
      />
    </Points>
  )
}

// Fireflies - larger, glowing particles that pulse
function Fireflies({ count = 50 }: { count?: number }) {
  const ref = useRef<THREE.Points>(null)
  const initialPositions = useRef<Float32Array>()
  
  const positions = useMemo(() => {
    const pos = new Float32Array(count * 3)
    for (let i = 0; i < count; i++) {
      pos[i * 3] = (Math.random() - 0.5) * 20
      pos[i * 3 + 1] = (Math.random() - 0.5) * 10
      pos[i * 3 + 2] = (Math.random() - 0.5) * 10
    }
    initialPositions.current = pos.slice()
    return pos
  }, [count])

  useFrame((state) => {
    if (ref.current && initialPositions.current) {
      const positions = ref.current.geometry.attributes.position.array as Float32Array
      const time = state.clock.elapsedTime
      
      for (let i = 0; i < count; i++) {
        const i3 = i * 3
        // Gentle floating motion
        positions[i3] = initialPositions.current[i3] + Math.sin(time * 0.5 + i) * 0.5
        positions[i3 + 1] = initialPositions.current[i3 + 1] + Math.sin(time * 0.3 + i * 0.5) * 0.3
        positions[i3 + 2] = initialPositions.current[i3 + 2] + Math.cos(time * 0.4 + i * 0.7) * 0.4
      }
      ref.current.geometry.attributes.position.needsUpdate = true
    }
  })

  return (
    <Points ref={ref} positions={positions} stride={3} frustumCulled={false}>
      <PointMaterial
        transparent
        color="#f97316"
        size={0.08}
        sizeAttenuation={true}
        depthWrite={false}
        opacity={0.9}
        blending={THREE.AdditiveBlending}
      />
    </Points>
  )
}

// Gentle aurora/nebula effect
function Aurora() {
  const meshRef = useRef<THREE.Mesh>(null)
  
  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.z = state.clock.elapsedTime * 0.05
      const material = meshRef.current.material as THREE.MeshBasicMaterial
      material.opacity = 0.1 + Math.sin(state.clock.elapsedTime * 0.2) * 0.05
    }
  })

  return (
    <mesh ref={meshRef} position={[0, 2, -10]}>
      <planeGeometry args={[30, 15]} />
      <meshBasicMaterial
        color="#7c3aed"
        transparent
        opacity={0.1}
        side={THREE.DoubleSide}
        blending={THREE.AdditiveBlending}
      />
    </mesh>
  )
}

// Floating orbs representing wisdom/knowledge
function WisdomOrbs({ count = 8 }: { count?: number }) {
  const groupRef = useRef<THREE.Group>(null)
  
  const orbs = useMemo(() => {
    return Array.from({ length: count }, (_, i) => ({
      position: [
        (Math.random() - 0.5) * 15,
        (Math.random() - 0.5) * 8,
        -5 + Math.random() * -10
      ] as [number, number, number],
      scale: 0.2 + Math.random() * 0.3,
      speed: 0.2 + Math.random() * 0.3,
      offset: Math.random() * Math.PI * 2,
      color: ['#f43f5e', '#8b5cf6', '#06b6d4', '#22c55e', '#f59e0b'][i % 5]
    }))
  }, [count])

  useFrame((state) => {
    if (groupRef.current) {
      groupRef.current.children.forEach((child, i) => {
        const orb = orbs[i]
        child.position.y = orb.position[1] + Math.sin(state.clock.elapsedTime * orb.speed + orb.offset) * 0.5
        child.rotation.y = state.clock.elapsedTime * 0.5
      })
    }
  })

  return (
    <group ref={groupRef}>
      {orbs.map((orb, i) => (
        <mesh key={i} position={orb.position} scale={orb.scale}>
          <icosahedronGeometry args={[1, 1]} />
          <meshBasicMaterial
            color={orb.color}
            transparent
            opacity={0.3}
            wireframe
          />
        </mesh>
      ))}
    </group>
  )
}

// Gentle pulsing light at center
function CenterGlow() {
  const lightRef = useRef<THREE.PointLight>(null)
  
  useFrame((state) => {
    if (lightRef.current) {
      lightRef.current.intensity = 0.5 + Math.sin(state.clock.elapsedTime * 0.5) * 0.2
    }
  })

  return (
    <>
      <pointLight ref={lightRef} position={[0, 0, 0]} color="#fbbf24" intensity={0.5} distance={20} />
      <mesh position={[0, 0, -5]}>
        <sphereGeometry args={[0.5, 32, 32]} />
        <meshBasicMaterial color="#fbbf24" transparent opacity={0.1} />
      </mesh>
    </>
  )
}

// Main scene
function Scene() {
  return (
    <>
      <ambientLight intensity={0.1} />
      <StarField count={1500} />
      <Fireflies count={40} />
      <Aurora />
      <WisdomOrbs count={6} />
      <CenterGlow />
    </>
  )
}

// Exported component with error boundary fallback
export function InspirationScene() {
  return (
    <div className="absolute inset-0 -z-10">
      <Canvas
        camera={{ position: [0, 0, 5], fov: 60 }}
        gl={{ antialias: true, alpha: true }}
        style={{ background: 'transparent' }}
      >
        <Scene />
      </Canvas>
    </div>
  )
}

export default InspirationScene
