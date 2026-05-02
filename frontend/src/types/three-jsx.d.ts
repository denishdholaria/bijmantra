import { Object3DNode, BufferGeometryNode, MaterialNode } from '@react-three/fiber'
import { Group, Mesh, Points, BufferGeometry, Material, MeshStandardMaterial, SphereGeometry, MeshBasicMaterial, PlaneGeometry, IcosahedronGeometry, PointsMaterial, GridHelper, AmbientLight, PointLight, Fog, Color } from 'three'

declare global {
  namespace JSX {
    interface IntrinsicElements {
      group: Object3DNode<Group, typeof Group>
      mesh: Object3DNode<Mesh, typeof Mesh>
      points: Object3DNode<Points, typeof Points>
      sphereGeometry: BufferGeometryNode<SphereGeometry, typeof SphereGeometry>
      meshStandardMaterial: MaterialNode<MeshStandardMaterial, typeof MeshStandardMaterial>
      pointsMaterial: MaterialNode<PointsMaterial, typeof PointsMaterial>
      meshBasicMaterial: MaterialNode<MeshBasicMaterial, typeof MeshBasicMaterial>
      planeGeometry: BufferGeometryNode<PlaneGeometry, typeof PlaneGeometry>
      icosahedronGeometry: BufferGeometryNode<IcosahedronGeometry, typeof IcosahedronGeometry>
      gridHelper: Object3DNode<GridHelper, typeof GridHelper>
      ambientLight: Object3DNode<AmbientLight, typeof AmbientLight>
      pointLight: Object3DNode<PointLight, typeof PointLight>
      fog: Object3DNode<Fog, typeof Fog>
      color: Object3DNode<Color, typeof Color>
    }
  }
}
