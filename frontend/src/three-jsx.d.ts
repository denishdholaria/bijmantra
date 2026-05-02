import { Object3DNode, BufferGeometryNode, MaterialNode, LightNode, Node } from '@react-three/fiber'
import {
  Group,
  Mesh,
  Points,
  BufferGeometry,
  Material,
  MeshStandardMaterial,
  SphereGeometry,
  PointsMaterial,
  GridHelper,
  AmbientLight,
  PointLight,
  Color,
  Fog,
  PlaneGeometry,
  MeshBasicMaterial,
  IcosahedronGeometry,
  Line
} from 'three'

declare module 'react' {
  namespace JSX {
    interface IntrinsicElements {
      group: Object3DNode<Group, typeof Group>
      mesh: Object3DNode<Mesh, typeof Mesh>
      points: Object3DNode<Points, typeof Points>
      lineSegments: Object3DNode<any, any>
      bufferGeometry: BufferGeometryNode<BufferGeometry, typeof BufferGeometry>
      sphereGeometry: BufferGeometryNode<SphereGeometry, typeof SphereGeometry>
      planeGeometry: BufferGeometryNode<PlaneGeometry, typeof PlaneGeometry>
      icosahedronGeometry: BufferGeometryNode<IcosahedronGeometry, typeof IcosahedronGeometry>
      meshStandardMaterial: MaterialNode<MeshStandardMaterial, typeof MeshStandardMaterial>
      meshBasicMaterial: MaterialNode<MeshBasicMaterial, typeof MeshBasicMaterial>
      pointsMaterial: MaterialNode<PointsMaterial, typeof PointsMaterial>
      gridHelper: Object3DNode<GridHelper, typeof GridHelper>
      ambientLight: LightNode<AmbientLight, typeof AmbientLight>
      pointLight: LightNode<PointLight, typeof PointLight>
      // Use Node or any for non-Object3D elements to allow args/props
      color: any
      fog: any
    }
  }
}
