"use client";

import { useRef, useEffect, useState, useMemo } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { Environment, Points, PointMaterial } from "@react-three/drei";
import * as THREE from "three";
import { useScroll, motion } from "framer-motion";
import { useTheme } from "next-themes";

function StoreModel({ scrollYProgress, theme }: { scrollYProgress: any, theme: string | undefined }) {
  const groupRef = useRef<THREE.Group>(null);
  const pointsRef = useRef<THREE.Points>(null);

  // Generate a procedural wireframe "store" layout
  const storeGeometry = new THREE.BoxGeometry(4, 2, 4, 10, 5, 10);
  
  useFrame((state, delta) => {
    if (!groupRef.current) return;
    
    // Map scroll 0 -> 1 to specific rotations and positions
    const scroll = scrollYProgress.get();
    
    // Smoothly interpolate target values based on scroll
    const targetRotationY = scroll * Math.PI * 2;
    const targetRotationX = (Math.PI / 8) + (scroll * Math.PI / 4);
    const targetScale = 1 + (scroll * 1.5);
    const targetZ = scroll * 3;

    groupRef.current.rotation.y = THREE.MathUtils.lerp(groupRef.current.rotation.y, targetRotationY, 0.1);
    groupRef.current.rotation.x = THREE.MathUtils.lerp(groupRef.current.rotation.x, targetRotationX, 0.1);
    groupRef.current.scale.setScalar(THREE.MathUtils.lerp(groupRef.current.scale.x, targetScale, 0.1));
    groupRef.current.position.z = THREE.MathUtils.lerp(groupRef.current.position.z, targetZ, 0.1);

    if (pointsRef.current) {
      pointsRef.current.rotation.y -= delta * 0.05;
    }
  });

  return (
    <group ref={groupRef}>
      <mesh>
        <boxGeometry args={[4, 2, 4, 10, 5, 10]} />
        <meshBasicMaterial color="#0071e3" wireframe transparent opacity={0.3} />
      </mesh>
      {/* Inner core */}
      <mesh>
        <boxGeometry args={[3.8, 1.8, 3.8]} />
        <meshStandardMaterial 
          color={theme === "light" ? "#f8fafc" : "#000000"} 
          roughness={theme === "light" ? 0.3 : 0.1} 
          metalness={theme === "light" ? 0.2 : 0.9} 
          transparent 
          opacity={theme === "light" ? 0.5 : 0.8} 
        />
      </mesh>
    </group>
  );
}

function FloatingParticles({ theme }: { theme: string | undefined }) {
  const particlesCount = 1000;
  const positions = useMemo(() => {
    const pos = new Float32Array(particlesCount * 3);
    for(let i = 0; i < particlesCount * 3; i++) {
      pos[i] = (Math.random() - 0.5) * 20;
    }
    return pos;
  }, [particlesCount]);
  
  const ref = useRef<THREE.Points>(null);
  useFrame((state) => {
    if (ref.current) {
      ref.current.rotation.y = state.clock.elapsedTime * 0.02;
    }
  });

  return (
    <Points ref={ref} positions={positions} stride={3} frustumCulled={false}>
      <PointMaterial 
        transparent 
        color={theme === "light" ? "#0071e3" : "#bf5af2"} 
        size={0.05} 
        sizeAttenuation={true} 
        depthWrite={false} 
        opacity={theme === "light" ? 0.5 : 1}
      />
    </Points>
  );
}

export default function AppleScrollScene() {
  const { scrollYProgress } = useScroll();
  const { theme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  return (
    <div className="fixed inset-0 w-full h-full pointer-events-none z-0">
      <Canvas camera={{ position: [0, 2, 8], fov: 45 }}>
        <ambientLight intensity={theme === "light" ? 1.5 : 0.5} />
        <directionalLight position={[10, 10, 10]} intensity={theme === "light" ? 2 : 1} />
        <Environment preset="city" />
        
        <StoreModel scrollYProgress={scrollYProgress} theme={theme} />
        <FloatingParticles theme={theme} />
      </Canvas>
    </div>
  );
}
