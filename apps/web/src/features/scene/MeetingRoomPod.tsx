"use client";

import { Text } from "@react-three/drei";
import type { ThreeEvent } from "@react-three/fiber";
import type { MeetingRoom } from "@raisehack/shared";
import { useSelection } from "@/features/selection/SelectionProvider";
import { BUILDING, getFloorBaseY } from "./buildingConfig";

interface MeetingRoomPodProps {
  room: MeetingRoom;
}

/** Minimal back-corner meeting nook — label only when selected */
export function MeetingRoomPod({ room }: MeetingRoomPodProps) {
  const { selectedMeetingRoomId, setSelectedMeetingRoom } = useSelection();
  const isSelected = selectedMeetingRoomId === room.id;
  const accent = room.accentColor ?? "#4ade80";

  const floorY = getFloorBaseY(room.floor);
  const [x, yOff, z] = room.position;
  const podY = floorY + BUILDING.slabThickness + yOff;
  const w = 0.62;
  const d = 0.48;
  const h = 0.48;

  const handleClick = (e: ThreeEvent<MouseEvent>) => {
    e.stopPropagation();
    setSelectedMeetingRoom(room.id);
  };

  return (
    <group position={[x, podY, z]}>
      {/* Floor tint */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.004, 0]}>
        <planeGeometry args={[w + 0.06, d + 0.06]} />
        <meshStandardMaterial
          color={accent}
          transparent
          opacity={isSelected ? 0.2 : 0.08}
          depthWrite={false}
        />
      </mesh>

      {/* Back + side walls — low, open front */}
      <mesh position={[0, h * 0.45, -d / 2 + 0.015]}>
        <boxGeometry args={[w, h * 0.85, 0.025]} />
        <meshStandardMaterial color={accent} transparent opacity={0.2} />
      </mesh>
      {([-1, 1] as const).map((side) => (
        <mesh key={side} position={[side * (w / 2 - 0.012), h * 0.4, -d * 0.15]}>
          <boxGeometry args={[0.025, h * 0.75, d * 0.65]} />
          <meshStandardMaterial color={accent} transparent opacity={0.15} />
        </mesh>
      ))}

      {/* Table */}
      <mesh position={[0, 0.18, -0.02]}>
        <boxGeometry args={[w * 0.45, 0.03, d * 0.28]} />
        <meshStandardMaterial color="#94a3b8" roughness={0.6} />
      </mesh>

      {/* Screen */}
      <mesh position={[0, h * 0.55, -d / 2 + 0.03]}>
        <boxGeometry args={[w * 0.35, h * 0.22, 0.015]} />
        <meshStandardMaterial
          color="#0f172a"
          emissive={accent}
          emissiveIntensity={isSelected ? 0.45 : 0.15}
        />
      </mesh>

      {/* Hit area */}
      <mesh
        position={[0, h / 2, 0]}
        onClick={handleClick}
        onPointerOver={(e) => {
          e.stopPropagation();
          document.body.style.cursor = "pointer";
        }}
        onPointerOut={() => {
          document.body.style.cursor = "default";
        }}
      >
        <boxGeometry args={[w, h, d]} />
        <meshBasicMaterial transparent opacity={0} depthWrite={false} />
      </mesh>

      {/* Label — only when selected to reduce clutter */}
      {isSelected && (
        <>
          <mesh position={[0, h + 0.06, 0]}>
            <boxGeometry args={[w + 0.2, 0.13, 0.01]} />
            <meshBasicMaterial color="#0f172a" transparent opacity={0.88} depthWrite={false} />
          </mesh>
          <Text
            position={[0, h + 0.06, 0.008]}
            fontSize={0.055}
            color="#f8fafc"
            anchorX="center"
            anchorY="middle"
            maxWidth={w + 0.15}
          >
            {room.name.toUpperCase()}
          </Text>
        </>
      )}
    </group>
  );
}
