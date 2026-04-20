export {};

declare global {
  namespace JSX {
    interface IntrinsicElements {
      group: any;
      mesh: any;
      pointLight: any;
      ambientLight: any;
      sphereGeometry: any;
      meshStandardMaterial: any;
      points: any;
      pointsMaterial: any;
      gridHelper: any;
      color: any;
      fog: any;
      planeGeometry: any;
      meshBasicMaterial: any;
      icosahedronGeometry: any;
    }
  }
}
