import { useRef, Suspense } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Environment } from '@react-three/drei';
import type { Mesh } from 'three';

// 3D Metallic Object Component - Optimized
const MetallicObject = () => {
  const meshRef = useRef<Mesh>(null);

  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.3) * 0.1;
      meshRef.current.rotation.y += 0.003;
      meshRef.current.position.y = Math.sin(state.clock.elapsedTime * 0.5) * 0.3;
    }
  });

  return (
    <mesh ref={meshRef} position={[2, 0, 0]} castShadow>
      <torusKnotGeometry args={[1.5, 0.4, 100, 24]} />
      <meshStandardMaterial
        color="#ff6e00"
        metalness={1}
        roughness={0.15}
        envMapIntensity={1.5}
      />
    </mesh>
  );
};

const TorusKnot3D = () => {
  return (
    <div 
      className="absolute right-0 top-1/2 -translate-y-1/2 w-[60%] h-[80%] z-[1] hidden lg:block"
      style={{ contain: 'layout paint' }}
    >
      <Suspense fallback={null}>
        <Canvas
          camera={{ position: [0, 0, 8], fov: 50 }}
          dpr={[1, 1.5]}
          gl={{ antialias: false, alpha: true, powerPreference: 'low-power' }}
          frameloop="always"
        >
          <ambientLight intensity={0.3} />
          <spotLight
            position={[10, 10, 10]}
            angle={0.3}
            penumbra={1}
            intensity={2}
          />
          <pointLight position={[-10, -10, -10]} intensity={0.5} color="#ff6e00" />
          <MetallicObject />
          <Environment preset="city" />
        </Canvas>
      </Suspense>
    </div>
  );
};

export default TorusKnot3D;
