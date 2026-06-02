"use client";

import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls, Environment, Grid, Html } from "@react-three/drei";
import { useMemo, useRef, useState } from "react";
import * as THREE from "three";

function ZoneMesh({ 
  position, 
  size, 
  color, 
  label, 
  dwellTime 
}: { 
  position: [number, number, number], 
  size: [number, number, number],
  color: string,
  label: string,
  dwellTime: number
}) {
  const meshRef = useRef<THREE.Mesh>(null);
  const [hovered, setHovered] = useState(false);

  // Subtle breathing animation
  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.position.y = position[1] + Math.sin(state.clock.elapsedTime * 2 + position[0]) * 0.05;
    }
  });

  return (
    <mesh
      ref={meshRef}
      position={position}
      onPointerOver={(e) => { e.stopPropagation(); setHovered(true); }}
      onPointerOut={() => setHovered(false)}
    >
      <boxGeometry args={size} />
      <meshPhysicalMaterial 
        color={color} 
        transparent 
        opacity={hovered ? 0.8 : 0.5} 
        roughness={0.1}
        metalness={0.8}
        clearcoat={1}
      />
      {hovered && (
        <Html position={[0, size[1]/2 + 0.5, 0]} center>
          <div className="bg-black/80 backdrop-blur-md text-white px-4 py-2 rounded-xl text-sm whitespace-nowrap border border-white/10 shadow-2xl">
            <div className="font-bold mb-1">{label}</div>
            <div className="text-gray-300">Avg Dwell: {(dwellTime/60).toFixed(1)}m</div>
          </div>
        </Html>
      )}
    </mesh>
  );
}

function WanderingAgents({ zones, count = 10 }: { zones: any[], count?: number }) {
  const agents = useMemo(() => {
    return Array.from({ length: count }).map(() => ({
      position: new THREE.Vector3(
        (Math.random() - 0.5) * 8,
        0.5,
        (Math.random() - 0.5) * 8
      ),
      target: new THREE.Vector3(),
      speed: Math.random() * 0.02 + 0.01,
    }));
  }, [count]);

  const groupRef = useRef<THREE.Group>(null);

  useFrame(() => {
    const group = groupRef.current;
    if (!group) return;
    
    agents.forEach((agent, i) => {
      // If agent reached target or has no target, pick a new random zone target
      if (agent.position.distanceTo(agent.target) < 0.5 || agent.target.lengthSq() === 0) {
        const randomZone = zones[Math.floor(Math.random() * zones.length)];
        // Pick a point inside the zone bounds
        const [x, y, z] = randomZone.pos;
        const [w, h, d] = randomZone.size;
        agent.target.set(
          x + (Math.random() - 0.5) * w,
          0.5,
          z + (Math.random() - 0.5) * d
        );
      }
      // Move towards target
      agent.position.lerp(agent.target, agent.speed);
      
      const mesh = group.children[i] as THREE.Mesh;
      if (mesh) {
        mesh.position.copy(agent.position);
      }
    });
  });

  return (
    <group ref={groupRef}>
      {agents.map((_, i) => (
        <mesh key={i}>
          <sphereGeometry args={[0.15, 16, 16]} />
          <meshStandardMaterial color="#4ade80" emissive="#4ade80" emissiveIntensity={0.5} />
        </mesh>
      ))}
    </group>
  );
}

export default function StoreHeatmap3D({ heatmap }: { heatmap: any }) {
  // Map API heatmap data to glowing colors
  const zones = useMemo(() => {
    const layout = [
      { id: "ENTRY", pos: [0, 0.5, 4], size: [3, 1, 2] },
      { id: "BILLING", pos: [0, 0.5, -4], size: [4, 1, 2] },
      { id: "MENS", pos: [-3, 0.5, 0], size: [2, 1, 4] },
      { id: "WOMENS", pos: [3, 0.5, 0], size: [2, 1, 4] },
    ];

    return layout.map(z => {
      const heat = Array.isArray(heatmap) ? heatmap.find((hz: any) => hz.zone_id === z.id) : null;
      const dwell_ms = heat?.avg_dwell_ms || 0;
      const dwell_time_sec = dwell_ms / 1000;
      // Interpolate color from blue (cool) to red (hot) based on dwell time (e.g. max 300s)
      const intensity = Math.min(dwell_time_sec / 300, 1);
      const color = new THREE.Color().lerpColors(new THREE.Color("#0071e3"), new THREE.Color("#ff3b30"), intensity);
      
      return { ...z, color: color.getStyle(), dwellTime: dwell_time_sec };
    });
  }, [heatmap]);

  return (
    <div className="w-full h-full min-h-[400px] glass-panel relative overflow-hidden">
      <div className="absolute top-4 left-4 z-10">
        <h3 className="font-semibold tracking-wide">3D Store Heatmap</h3>
        <p className="text-xs text-gray-400">Interactive live layout</p>
      </div>
      <Canvas camera={{ position: [8, 8, 8], fov: 45 }}>
        <ambientLight intensity={0.5} />
        <directionalLight position={[10, 10, 5]} intensity={1} />
        <Environment preset="city" />
        
        {/* Futuristic glowing grid floor */}
        <Grid 
          infiniteGrid 
          fadeDistance={30} 
          sectionColor="#ffffff" 
          cellColor="#ffffff" 
          cellThickness={0.5} 
          sectionThickness={1} 
          sectionSize={2} 
          cellSize={1} 
          position={[0, 0, 0]} 
        />

        {zones.map((z, i) => (
          <ZoneMesh key={i} position={z.pos as any} size={z.size as any} color={z.color} label={z.id} dwellTime={z.dwellTime} />
        ))}
        
        <WanderingAgents zones={zones} count={12} />

        <OrbitControls 
          enablePan={false} 
          maxPolarAngle={Math.PI / 2.2} 
          minDistance={5} 
          maxDistance={20}
          autoRotate
          autoRotateSpeed={0.5}
        />
      </Canvas>
    </div>
  );
}
