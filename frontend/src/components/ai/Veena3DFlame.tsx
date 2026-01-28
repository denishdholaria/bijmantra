import { useRef } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { Sphere, MeshDistortMaterial } from '@react-three/drei'
import * as THREE from 'three'

function FlameMesh({ scale = 1 }: { scale?: number }) {
  const ref = useRef<THREE.Mesh>(null)
  const materialRef = useRef<any>(null)

  useFrame((state) => {
    const time = state.clock.getElapsedTime()
    if (ref.current) {
      // Rotation
      ref.current.rotation.y = time * 0.1
      ref.current.rotation.z = time * 0.05
    }
    if (materialRef.current) {
      // Organic movement via distort
      materialRef.current.distort = 0.4 + Math.sin(time) * 0.1
    }
  })

  return (
    <Sphere args={[1, 64, 64]} ref={ref} scale={scale}>
      <MeshDistortMaterial
        ref={materialRef}
        speed={2}
        distort={0.4}
        color="#10b981" // Emerald base
        emissive="#059669"
        emissiveIntensity={0.5}
        roughness={0.2}
        metalness={0.8}
      />
    </Sphere>
  )
}

// GradientTexture removed due to potential stability issues


export function Veena3DFlame({ className, scale = 1 }: { className?: string, scale?: number }) {
  return (
    <div className={className}>
      <Canvas camera={{ position: [0, 0, 3], fov: 45 }}>
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} intensity={1} color="#fcd34d" />
        <pointLight position={[-10, -10, -5]} intensity={0.5} color="#10b981" />
        <FlameMesh scale={scale} />
      </Canvas>
    </div>
  )
}
