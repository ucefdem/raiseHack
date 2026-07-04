"use client";

import { useRef, useState, useEffect } from "react";
import { Text } from "@react-three/drei";
import { useFrame } from "@react-three/fiber";
import type { ThreeEvent } from "@react-three/fiber";
import type { Group } from "three";
import type { Agent } from "@raisehack/shared";
import { getDepartmentById } from "@/data/departments";
import { useSelection } from "@/features/selection/SelectionProvider";
import { useAgentTracking } from "./AgentTrackingProvider";
import { AgentErrorSignal, AgentWorkSurfaceProp } from "./AgentWorkSurfaceProp";
import { BUILDING, getFloorBaseY } from "./buildingConfig";

const HEAD_COLOR = "#f4f4f5";
const FLOOR_MARGIN = 0.38;

function hashSeed(id: string): number {
  let h = 0;
  for (let i = 0; i < id.length; i++) h = (h << 5) - h + id.charCodeAt(i);
  return Math.abs(h);
}

function getFloorWalkBounds() {
  const maxX = BUILDING.width / 2 - FLOOR_MARGIN;
  const maxZ = BUILDING.depth / 2 - FLOOR_MARGIN;
  return { maxX, maxZ };
}

/** Matte chibi material — soft toy-like finish */
function chibiMat(color: string, emissive = "#000000", emissiveIntensity = 0) {
  return (
    <meshStandardMaterial
      color={color}
      emissive={emissive}
      emissiveIntensity={emissiveIntensity}
      roughness={0.92}
      metalness={0.02}
    />
  );
}

function ChibiFigure({
  bodyColor,
  highlighted,
  leftArmRef,
  rightArmRef,
  leftLegRef,
  rightLegRef,
}: {
  bodyColor: string;
  highlighted: boolean;
  leftArmRef: React.RefObject<Group | null>;
  rightArmRef: React.RefObject<Group | null>;
  leftLegRef: React.RefObject<Group | null>;
  rightLegRef: React.RefObject<Group | null>;
}) {
  const glow = highlighted ? 0.16 : 0.03;

  return (
    <group scale={1.15}>
      {/* Head — large soft rounded sphere */}
      <mesh position={[0, 0.4, 0]} castShadow>
        <sphereGeometry args={[0.125, 24, 24]} />
        {chibiMat(HEAD_COLOR)}
      </mesh>

      {/* Rounded-box torso (capsule gives soft edges) */}
      <mesh position={[0, 0.2, 0]} scale={[1, 1, 0.82]} castShadow>
        <capsuleGeometry args={[0.085, 0.11, 6, 16]} />
        {chibiMat(bodyColor, bodyColor, glow)}
      </mesh>

      {/* Arms — cylinders hanging at the sides with rounded ends */}
      <group ref={leftArmRef} position={[-0.11, 0.27, 0]} rotation={[0, 0, 0.05]}>
        <mesh position={[0, -0.07, 0]} castShadow>
          <capsuleGeometry args={[0.03, 0.11, 6, 12]} />
          {chibiMat(bodyColor, bodyColor, glow)}
        </mesh>
      </group>

      <group ref={rightArmRef} position={[0.11, 0.27, 0]} rotation={[0, 0, -0.05]}>
        <mesh position={[0, -0.07, 0]} castShadow>
          <capsuleGeometry args={[0.03, 0.11, 6, 12]} />
          {chibiMat(bodyColor, bodyColor, glow)}
        </mesh>
      </group>

      {/* Legs — short stubby cylinders with a gap */}
      <group ref={leftLegRef} position={[-0.05, 0.09, 0]}>
        <mesh position={[0, -0.05, 0]} castShadow>
          <capsuleGeometry args={[0.036, 0.06, 6, 12]} />
          {chibiMat(bodyColor, bodyColor, glow)}
        </mesh>
      </group>

      <group ref={rightLegRef} position={[0.05, 0.09, 0]}>
        <mesh position={[0, -0.05, 0]} castShadow>
          <capsuleGeometry args={[0.036, 0.06, 6, 12]} />
          {chibiMat(bodyColor, bodyColor, glow)}
        </mesh>
      </group>
    </group>
  );
}

interface AgentAvatarProps {
  agent: Agent;
  floor: number;
  index: number;
  totalOnFloor: number;
  zoneCenter?: [number, number];
  zoneHalfSize?: number;
}

function clampToZone(
  x: number,
  z: number,
  cx: number,
  cz: number,
  half: number,
) {
  return {
    x: Math.max(cx - half, Math.min(cx + half, x)),
    z: Math.max(cz - half, Math.min(cz + half, z)),
  };
}

export function AgentAvatar({
  agent,
  floor,
  index,
  totalOnFloor,
  zoneCenter = [0, 0],
  zoneHalfSize,
}: AgentAvatarProps) {
  const groupRef = useRef<Group>(null);
  const leftArmRef = useRef<Group>(null);
  const rightArmRef = useRef<Group>(null);
  const leftLegRef = useRef<Group>(null);
  const rightLegRef = useRef<Group>(null);
  const walkPhase = useRef(0);

  const [hovered, setHovered] = useState(false);
  const { selectedAgentId, setSelectedAgent } = useSelection();
  const { registerAgentRef, unregisterAgentRef } = useAgentTracking();

  useEffect(() => {
    registerAgentRef(agent.id, groupRef);
    return () => unregisterAgentRef(agent.id);
  }, [agent.id, registerAgentRef, unregisterAgentRef]);

  const isSelected = selectedAgentId === agent.id;
  const isHighlighted = isSelected || hovered;
  const department = getDepartmentById(agent.departmentId);
  const floorColor = department?.zone.color ?? "#64748b";

  const seed = hashSeed(agent.id);
  const { maxX, maxZ } = getFloorWalkBounds();
  const [zoneCx, zoneCz] = zoneCenter;
  const half = zoneHalfSize ?? Math.min(maxX, maxZ) - 0.1;
  const phase = (seed % 628) / 100;
  const startAngle = (index / Math.max(totalOnFloor, 1)) * Math.PI * 2;
  const pathSpeed = 0.35 + (seed % 20) / 100;

  const spawnX = zoneCx + ((seed % 100) / 100 - 0.5) * half * 1.2;
  const spawnZ = zoneCz + (((seed >> 3) % 100) / 100 - 0.5) * half * 1.0;
  const pathRadius = Math.min(0.38, half * 0.55);

  const floorY = getFloorBaseY(floor) + BUILDING.slabThickness;

  useFrame(({ clock }) => {
    const g = groupRef.current;
    if (!g) return;

    let moving = false;
    let t = 0;

    if (agent.status === "offline") {
      const { x, z } = clampToZone(spawnX, spawnZ, zoneCx, zoneCz, half);
      g.position.set(x, floorY, z);
      g.rotation.y = 0;
    } else {
      moving = true;
      const speed = agent.status === "busy" ? pathSpeed * 1.3 : pathSpeed;
      t = clock.elapsedTime * speed + phase + startAngle;
      const rawX = spawnX + Math.cos(t) * pathRadius;
      const rawZ = spawnZ + Math.sin(t) * pathRadius * 0.7;
      const { x, z } = clampToZone(rawX, rawZ, zoneCx, zoneCz, half);
      g.position.set(x, floorY + Math.abs(Math.sin(t * 5)) * 0.012, z);
      g.rotation.y = -t + Math.PI / 2;
      walkPhase.current = t * 5;
    }

    const swing = moving ? Math.sin(walkPhase.current) * 0.4 : 0;
    leftArmRef.current?.rotation.set(swing, 0, 0.05);
    rightArmRef.current?.rotation.set(-swing, 0, -0.05);
    leftLegRef.current?.rotation.set(-swing * 0.6, 0, 0);
    rightLegRef.current?.rotation.set(swing * 0.6, 0, 0);
  });

  const handleClick = (e: ThreeEvent<MouseEvent>) => {
    e.stopPropagation();
    setSelectedAgent(agent.id);
  };

  return (
    <group ref={groupRef}>
      {agent.error?.needsReview && (
        <AgentErrorSignal severity={agent.error.severity} />
      )}

      {isHighlighted && !agent.error?.needsReview && (
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.01, 0]}>
          <ringGeometry args={[0.24, 0.3, 24]} />
          <meshBasicMaterial color={floorColor} transparent opacity={0.65} />
        </mesh>
      )}

      <group
        onClick={handleClick}
        onPointerOver={(e) => {
          e.stopPropagation();
          setHovered(true);
          document.body.style.cursor = "pointer";
        }}
        onPointerOut={() => {
          setHovered(false);
          document.body.style.cursor = "default";
        }}
      >
        <ChibiFigure
          bodyColor={floorColor}
          highlighted={isHighlighted}
          leftArmRef={leftArmRef}
          rightArmRef={rightArmRef}
          leftLegRef={leftLegRef}
          rightLegRef={rightLegRef}
        />

        {agent.status !== "offline" &&
          agent.workSurface &&
          agent.workSurface !== "none" &&
          isHighlighted && (
          <AgentWorkSurfaceProp surface={agent.workSurface} accent={floorColor} />
        )}

        {isHighlighted && (
          <Text
            position={[0, 0.58, 0]}
            fontSize={0.09}
            color="#f8fafc"
            anchorX="center"
            anchorY="bottom"
            outlineWidth={0.012}
            outlineColor="#0f172a"
          >
            {agent.name}
          </Text>
        )}
      </group>
    </group>
  );
}
