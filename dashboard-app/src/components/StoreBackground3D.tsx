"use client";

import { useRef, useEffect, useState, useMemo } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Environment, Points, PointMaterial } from "@react-three/drei";
import * as THREE from "three";
import { useTheme } from "next-themes";

function StoreModel({ theme }: { theme: string | undefined }) {
  const groupRef = useRef<THREE.Group>(null);
  
  useFrame((state, delta) => {
    if (!groupRef.current) return;
    // Slow cinematic rotation
    groupRef.current.rotation.y += delta * 0.05;
    
    // Add a slight bobbing motion
    groupRef.current.position.y = Math.sin(state.clock.elapsedTime * 0.5) * 0.1;
  });

  return (
    <group ref={groupRef} rotation={[Math.PI / 6, 0, 0]} scale={1.2}>
      <mesh>
        <boxGeometry args={[6, 2, 6, 12, 4, 12]} />
        <meshBasicMaterial 
          color={theme === "light" ? "#0071e3" : "#bf5af2"} 
          wireframe 
          transparent 
          opacity={0.15} 
        />
      </mesh>
      {/* Inner core */}
      <mesh>
        <boxGeometry args={[5.8, 1.8, 5.8]} />
        <meshStandardMaterial 
          color={theme === "light" ? "#f8fafc" : "#000000"} 
          roughness={theme === "light" ? 0.3 : 0.1} 
          metalness={theme === "light" ? 0.2 : 0.9} 
          transparent 
          opacity={theme === "light" ? 0.4 : 0.7} 
        />
      </mesh>
    </group>
  );
}

function FloatingParticles({ theme }: { theme: string | undefined }) {
  const particlesCount = 1500;
  const positions = useMemo(() => {
    const pos = new Float32Array(particlesCount * 3);
    for(let i = 0; i < particlesCount * 3; i++) {
      pos[i] = (Math.random() - 0.5) * 25;
    }
    return pos;
  }, [particlesCount]);
  
  const ref = useRef<THREE.Points>(null);
  useFrame((state) => {
    if (ref.current) {
      ref.current.rotation.y = state.clock.elapsedTime * 0.01;
    }
  });

  return (
    <Points ref={ref} positions={positions} stride={3} frustumCulled={false}>
      <PointMaterial 
        transparent 
        color={theme === "light" ? "#0071e3" : "#bf5af2"} 
        size={0.04} 
        sizeAttenuation={true} 
        depthWrite={false} 
        opacity={theme === "light" ? 0.4 : 0.8}
      />
    </Points>
  );
}

export default function StoreBackground3D() {
  const { theme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  return (
    <div className="fixed inset-0 w-full h-full pointer-events-none z-0">
      <Canvas camera={{ position: [0, 3, 10], fov: 50 }}>
        <ambientLight intensity={theme === "light" ? 1.5 : 0.5} />
        <directionalLight position={[10, 10, 10]} intensity={theme === "light" ? 2 : 1} />
        <Environment preset="city" />
        
        <StoreModel theme={theme} />
        <FloatingParticles theme={theme} />
      </Canvas>
    </div>
  );
}
