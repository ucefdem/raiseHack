"use client";

import { Text } from "@react-three/drei";
import type { ThreeEvent } from "@react-three/fiber";
import type { Department } from "@raisehack/shared";
import { useSelection } from "@/features/selection/SelectionProvider";
import { BUILDING, getFloorBaseY } from "./buildingConfig";
import type { SignSide } from "./floorLayout";

interface DepartmentFloorLabelProps {
  department: Department;
  signSide?: SignSide;
}

function nameFontSize(name: string): number {
  if (name.length > 16) return 0.11;
  if (name.length > 12) return 0.13;
  return 0.15;
}

/** Sign on the inside of the front wall — text faces into the floor */
export function DepartmentFloorLabel({
  department,
  signSide = "left",
}: DepartmentFloorLabelProps) {
  const { selectedDepartmentId, setSelectedDepartment } = useSelection();
  const isSelected = selectedDepartmentId === department.id;
  const accent = department.zone.color ?? "#94a3b8";

  const floorY = getFloorBaseY(department.floor);
  const halfW = BUILDING.width / 2;
  const halfD = BUILDING.depth / 2;
  const signY = floorY + BUILDING.floorHeight * 0.55;
  const signW = 2.4;
  const signH = 0.52;

  // Inner face of front wall (wall center at -halfD + 0.025, depth 0.05)
  const signZ = -halfD + 0.07;
  const signX =
    signSide === "right"
      ? halfW - signW / 2 - 0.18
      : -halfW + signW / 2 + 0.18;

  const handleClick = (e: ThreeEvent<MouseEvent>) => {
    e.stopPropagation();
    setSelectedDepartment(department.id);
  };

  return (
    <group
      position={[signX, signY, signZ]}
      onClick={handleClick}
      onPointerOver={(e) => {
        e.stopPropagation();
        document.body.style.cursor = "pointer";
      }}
      onPointerOut={() => {
        document.body.style.cursor = "default";
      }}
    >
      {/* Sign backing */}
      <mesh position={[0, 0, 0]} renderOrder={2}>
        <boxGeometry args={[signW, signH, 0.04]} />
        <meshStandardMaterial
          color={isSelected ? "#0f172a" : "#1e293b"}
          emissive={accent}
          emissiveIntensity={isSelected ? 0.18 : 0.06}
          metalness={0.35}
          roughness={0.45}
        />
      </mesh>

      {/* Accent stripe */}
      <mesh position={[0, signH / 2 - 0.05, 0.022]} renderOrder={3}>
        <boxGeometry args={[signW - 0.08, 0.07, 0.02]} />
        <meshStandardMaterial
          color={accent}
          emissive={accent}
          emissiveIntensity={isSelected ? 0.9 : 0.55}
        />
      </mesh>

      <Text
        position={[-signW / 2 + 0.32, 0.06, 0.022]}
        fontSize={0.11}
        color={accent}
        anchorX="left"
        anchorY="middle"
        letterSpacing={0.04}
        renderOrder={4}
      >
        {`FLOOR ${department.floor}`}
      </Text>

      <Text
        position={[0, -0.1, 0.022]}
        fontSize={nameFontSize(department.name)}
        color="#f8fafc"
        anchorX="center"
        anchorY="middle"
        maxWidth={signW - 0.35}
        letterSpacing={0.02}
        renderOrder={4}
      >
        {department.name.toUpperCase()}
      </Text>

      {isSelected && (
        <mesh position={[0, 0, 0.024]}>
          <boxGeometry args={[signW + 0.1, signH + 0.1, 0.01]} />
          <meshBasicMaterial color={accent} transparent opacity={0.3} depthWrite={false} />
        </mesh>
      )}
    </group>
  );
}
