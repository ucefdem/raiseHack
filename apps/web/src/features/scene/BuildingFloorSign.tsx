"use client";

import { Text } from "@react-three/drei";
import type { ThreeEvent } from "@react-three/fiber";
import type { Department } from "@raisehack/shared";
import { useSelection } from "@/features/selection/SelectionProvider";
import { BUILDING, getFloorBaseY } from "./buildingConfig";

/** One compact sign per physical floor — avoids duplicate plaques on shared floors */
export function BuildingFloorSign({
  floor,
  departments,
}: {
  floor: number;
  departments: Department[];
}) {
  const { selectedDepartmentId, setSelectedDepartment } = useSelection();
  const floorY = getFloorBaseY(floor);
  const halfD = BUILDING.depth / 2;
  const signY = floorY + BUILDING.floorHeight * 0.62;
  const signZ = -halfD + 0.07;
  const signW = departments.length > 1 ? 2.6 : 1.9;
  const signH = 0.34;
  const primary = departments[0];
  const accent = primary?.zone.color ?? "#94a3b8";
  const anySelected = departments.some((d) => d.id === selectedDepartmentId);
  const names = departments.map((d) => d.name).join("  ·  ");

  const handleClick = (e: ThreeEvent<MouseEvent>) => {
    e.stopPropagation();
    const hit = departments[0];
    if (hit) setSelectedDepartment(hit.id);
  };

  return (
    <group position={[0, signY, signZ]} onClick={handleClick}>
      <mesh
        onPointerOver={(e) => {
          e.stopPropagation();
          document.body.style.cursor = "pointer";
        }}
        onPointerOut={() => {
          document.body.style.cursor = "default";
        }}
      >
        <boxGeometry args={[signW, signH, 0.03]} />
        <meshStandardMaterial
          color={anySelected ? "#0f172a" : "#1a2332"}
          emissive={accent}
          emissiveIntensity={anySelected ? 0.12 : 0.04}
          roughness={0.5}
        />
      </mesh>

      {/* Split accent for multi-dept floors */}
      {departments.length > 1 ? (
        departments.map((dept, i) => (
          <mesh
            key={dept.id}
            position={[(i - 0.5) * (signW / departments.length), signH / 2 - 0.04, 0.016]}
          >
            <boxGeometry
              args={[signW / departments.length - 0.06, 0.04, 0.01]}
            />
            <meshStandardMaterial
              color={dept.zone.color ?? accent}
              emissive={dept.zone.color ?? accent}
              emissiveIntensity={selectedDepartmentId === dept.id ? 0.7 : 0.35}
            />
          </mesh>
        ))
      ) : (
        <mesh position={[0, signH / 2 - 0.04, 0.016]}>
          <boxGeometry args={[signW - 0.1, 0.04, 0.01]} />
          <meshStandardMaterial
            color={accent}
            emissive={accent}
            emissiveIntensity={anySelected ? 0.7 : 0.35}
          />
        </mesh>
      )}

      <Text
        position={[0, 0.04, 0.018]}
        fontSize={0.08}
        color={accent}
        anchorX="center"
        anchorY="middle"
        letterSpacing={0.06}
      >
        {`FLOOR ${floor}`}
      </Text>

      <Text
        position={[0, -0.08, 0.018]}
        fontSize={departments.length > 1 ? 0.075 : 0.085}
        color="#e2e8f0"
        anchorX="center"
        anchorY="middle"
        maxWidth={signW - 0.2}
      >
        {names.toUpperCase()}
      </Text>
    </group>
  );
}
