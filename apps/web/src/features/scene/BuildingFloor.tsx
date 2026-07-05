"use client";

import type { ThreeEvent } from "@react-three/fiber";
import { getAgentsByDepartment } from "@/data/agents";
import { getDepartmentsByFloor } from "@/data/departments";
import { useSelection } from "@/features/selection/SelectionProvider";
import { AgentAvatar } from "./AgentAvatar";
import { BuildingFloorSign } from "./BuildingFloorSign";
import { getDepartmentFloorLayout } from "./floorLayout";
import { BUILDING, getFloorBaseY } from "./buildingConfig";

interface BuildingFloorProps {
  floor: number;
}

/** One physical floor — may host multiple departments side by side */
export function BuildingFloor({ floor }: BuildingFloorProps) {
  const { selectedDepartmentId, setSelectedDepartment } = useSelection();
  const departments = getDepartmentsByFloor(floor);
  const floorY = getFloorBaseY(floor);
  const slabY = floorY + BUILDING.slabThickness / 2;
  const zoneY = floorY + BUILDING.slabThickness + 0.002;

  return (
    <group>
      <mesh position={[0, slabY, 0]} receiveShadow>
        <boxGeometry args={[BUILDING.width, BUILDING.slabThickness, BUILDING.depth]} />
        <meshStandardMaterial color="#e8edf2" roughness={0.88} metalness={0.03} />
      </mesh>

      {/* Single compact floor sign */}
      <BuildingFloorSign floor={floor} departments={departments} />

      {departments.map((department, deptIndex) => {
        const layout = getDepartmentFloorLayout(deptIndex, departments.length);
        const accent = department.zone.color ?? "#94a3b8";
        const isSelected = selectedDepartmentId === department.id;
        const agents = getAgentsByDepartment(department.id);
        const [zoneX, zoneZ] = layout.colorZone.offset;
        const [zoneW, zoneD] = layout.colorZone.size;

        return (
          <group key={department.id}>
            <mesh
              position={[zoneX, zoneY, zoneZ]}
              rotation={[-Math.PI / 2, 0, 0]}
              onClick={(e: ThreeEvent<MouseEvent>) => {
                e.stopPropagation();
                setSelectedDepartment(department.id);
              }}
              onPointerOver={(e) => {
                e.stopPropagation();
                document.body.style.cursor = "pointer";
              }}
              onPointerOut={() => {
                document.body.style.cursor = "default";
              }}
            >
              <planeGeometry args={[zoneW, zoneD]} />
              <meshStandardMaterial
                color={accent}
                transparent
                opacity={isSelected ? 0.14 : 0.05}
                depthWrite={false}
              />
            </mesh>

            {agents.map((agent, index) => (
              <AgentAvatar
                key={agent.id}
                agent={agent}
                floor={floor}
                index={index}
                totalOnFloor={agents.length}
                zoneCenter={layout.zoneCenter}
                zoneHalfSize={layout.zoneHalfSize}
              />
            ))}
          </group>
        );
      })}
    </group>
  );
}
