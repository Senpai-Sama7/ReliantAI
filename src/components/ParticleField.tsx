import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

function createParticleData(count: number) {
  const positions = new Float32Array(count * 3);
  const velocities = new Float32Array(count * 3);

  for (let i = 0; i < count; i++) {
    const i3 = i * 3;
    positions[i3] = (Math.random() - 0.5) * 100;
    positions[i3 + 1] = (Math.random() - 0.5) * 100;
    positions[i3 + 2] = (Math.random() - 0.5) * 50;

    velocities[i3] = (Math.random() - 0.5) * 0.02;
    velocities[i3 + 1] = (Math.random() - 0.5) * 0.02;
    velocities[i3 + 2] = (Math.random() - 0.5) * 0.01;
  }

  return { positions, velocities };
}

const PARTICLE_COUNT = 150;
const initialData = createParticleData(PARTICLE_COUNT);

const ParticleField = () => {
  const pointsRef = useRef<THREE.Points>(null);
  const velocitiesRef = useRef(initialData.velocities);

  useFrame((state) => {
    if (!pointsRef.current) return;

    const positions = pointsRef.current.geometry.attributes.position.array as Float32Array;
    const velocities = velocitiesRef.current;
    const time = state.clock.elapsedTime;

    for (let i = 0; i < PARTICLE_COUNT; i++) {
      const i3 = i * 3;

      // Update positions with velocity
      positions[i3] += velocities[i3] + Math.sin(time * 0.5 + i * 0.1) * 0.01;
      positions[i3 + 1] += velocities[i3 + 1] + Math.cos(time * 0.3 + i * 0.1) * 0.01;
      positions[i3 + 2] += velocities[i3 + 2];

      // Wrap around boundaries
      if (positions[i3] > 50) positions[i3] = -50;
      if (positions[i3] < -50) positions[i3] = 50;
      if (positions[i3 + 1] > 50) positions[i3 + 1] = -50;
      if (positions[i3 + 1] < -50) positions[i3 + 1] = 50;
      if (positions[i3 + 2] > 25) positions[i3 + 2] = -25;
      if (positions[i3 + 2] < -25) positions[i3 + 2] = 25;
    }

    pointsRef.current.geometry.attributes.position.needsUpdate = true;
    pointsRef.current.rotation.y = time * 0.02;
  });

  const positionAttribute = useMemo(() => {
    return new THREE.BufferAttribute(initialData.positions, 3);
  }, []);

  return (
    <points ref={pointsRef}>
      <bufferGeometry>
        <primitive object={positionAttribute} attach="attributes-position" />
      </bufferGeometry>
      <pointsMaterial
        size={0.5}
        color="#ff6e00"
        transparent
        opacity={0.6}
        sizeAttenuation
        blending={THREE.AdditiveBlending}
      />
    </points>
  );
};

export default ParticleField;
