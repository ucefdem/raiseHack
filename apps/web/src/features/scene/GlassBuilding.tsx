"use client";

import { Text } from "@react-three/drei";
import { getDepartmentsByFloor } from "@/data/departments";
import { BuildingFloor } from "./BuildingFloor";
import { MeetingRoomsLayer } from "./MeetingRoomsLayer";
import {
  BUILDING,
  FLOOR_COUNT,
  FOREST,
  STEEL_COLOR,
  TECH_ACCENT,
  HIGHLIGHT_COLOR,
  FACADE_COLOR,
  getFloorBaseY,
  getTowerHeight,
  getTotalBuildingHeight,
} from "./buildingConfig";

function ForestTree({ position, scale = 1 }: { position: [number, number, number]; scale?: number }) {
  return (
    <group position={position} scale={scale}>
      <mesh position={[0, 0.22, 0]} castShadow>
        <cylinderGeometry args={[0.035, 0.055, 0.44, 6]} />
        <meshStandardMaterial color={FOREST.trunk} roughness={0.95} />
      </mesh>
      <mesh position={[0, 0.58, 0]} castShadow>
        <coneGeometry args={[0.32, 0.72, 7]} />
        <meshStandardMaterial color={FOREST.foliage} roughness={0.9} />
      </mesh>
      <mesh position={[0, 0.78, 0]} castShadow>
        <coneGeometry args={[0.22, 0.45, 7]} />
        <meshStandardMaterial color={FOREST.foliageLight} roughness={0.9} />
      </mesh>
    </group>
  );
}

function generateTreePositions(clearingRadius: number): [number, number, number][] {
  const trees: [number, number, number][] = [];

  // Inner ring — just outside the clearing
  for (let i = 0; i < 12; i++) {
    const angle = (i / 12) * Math.PI * 2 + 0.15;
    const dist = clearingRadius + 0.8 + (i % 3) * 0.3;
    trees.push([
      Math.cos(angle) * dist,
      Math.sin(angle) * dist,
      0.8 + (i % 4) * 0.08,
    ]);
  }

  // Mid ring
  for (let i = 0; i < 14; i++) {
    const angle = (i / 14) * Math.PI * 2 + 0.4;
    const dist = clearingRadius + 2.5 + (i % 4) * 0.6;
    trees.push([
      Math.cos(angle) * dist,
      Math.sin(angle) * dist,
      0.85 + (i % 5) * 0.1,
    ]);
  }

  // Outer ring
  for (let i = 0; i < 12; i++) {
    const angle = (i / 12) * Math.PI * 2 + 0.8;
    const dist = clearingRadius + 4.8 + (i % 3) * 0.8;
    trees.push([
      Math.cos(angle) * dist,
      Math.sin(angle) * dist,
      0.9 + (i % 4) * 0.12,
    ]);
  }

  return trees;
}

function ForestFloor() {
  const p = BUILDING.pedestalSize;
  const clearingRadius = p * 0.48;
  const treePositions = generateTreePositions(clearingRadius);

  return (
    <group>
      {/* Forest ground */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.04, 0]} receiveShadow>
        <circleGeometry args={[18, 40]} />
        <meshStandardMaterial color={FOREST.floor} roughness={1} />
      </mesh>

      {/* Lighter grass patches */}
      {(
        [
          [-5, -4, 3.5],
          [4, 3, 3.0],
          [-3, 5, 2.8],
          [6, -3, 3.2],
        ] as [number, number, number][]
      ).map(([x, z, r], i) => (
        <mesh key={i} rotation={[-Math.PI / 2, 0, 0]} position={[x, -0.035, z]}>
          <circleGeometry args={[r, 24]} />
          <meshStandardMaterial color={FOREST.floorLight} roughness={0.98} transparent opacity={0.45} />
        </mesh>
      ))}

      {/* Natural clearing under the building */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.02, 0]} receiveShadow>
        <circleGeometry args={[clearingRadius, 32]} />
        <meshStandardMaterial color={FOREST.clearing} roughness={0.98} />
      </mesh>

      {/* Moss pad for building base */}
      <mesh position={[0, 0.02, 0]} receiveShadow>
        <boxGeometry args={[p * 0.85, 0.04, p * 0.85]} />
        <meshStandardMaterial color={FOREST.moss} roughness={0.95} />
      </mesh>

      {/* Dense tree scatter */}
      {treePositions.map(([x, z, s], i) => (
        <ForestTree key={i} position={[x, 0, z]} scale={s} />
      ))}
    </group>
  );
}

function CornerPost({
  x,
  z,
  baseY,
  height,
}: {
  x: number;
  z: number;
  baseY: number;
  height: number;
}) {
  return (
    <mesh position={[x, baseY + height / 2, z]} castShadow>
      <boxGeometry args={[0.06, height, 0.06]} />
      <meshStandardMaterial color={STEEL_COLOR} metalness={0.5} roughness={0.35} />
    </mesh>
  );
}

function FloorWalls({ floor }: { floor: number }) {
  const floorY = getFloorBaseY(floor);
  const centerY = floorY + BUILDING.floorHeight / 2;
  const halfW = BUILDING.width / 2;
  const halfD = BUILDING.depth / 2;
  const wallH = BUILDING.floorHeight - 0.1;
  const deptsOnFloor = getDepartmentsByFloor(floor);
  const accent = deptsOnFloor[0]?.zone.color ?? HIGHLIGHT_COLOR;

  const frontWallZ = -halfD + 0.025;
  const leftWallX = -halfW + 0.025;

  return (
    <group>
      {/* Full front wall behind the label */}
      <mesh position={[0, centerY, frontWallZ]} castShadow receiveShadow>
        <boxGeometry args={[BUILDING.width, wallH, 0.05]} />
        <meshStandardMaterial
          color={FACADE_COLOR}
          transparent
          opacity={0.72}
          roughness={0.45}
          metalness={0.05}
        />
      </mesh>
      <mesh position={[0, floorY + BUILDING.floorHeight - 0.06, frontWallZ - 0.01]}>
        <boxGeometry args={[BUILDING.width, 0.04, 0.03]} />
        <meshStandardMaterial
          color={accent}
          emissive={accent}
          emissiveIntensity={0.2}
          metalness={0.2}
          roughness={0.4}
        />
      </mesh>

      {/* Left side wall */}
      <mesh position={[leftWallX, centerY, 0]} castShadow receiveShadow>
        <boxGeometry args={[0.05, wallH, BUILDING.depth]} />
        <meshStandardMaterial
          color={FACADE_COLOR}
          transparent
          opacity={0.72}
          roughness={0.45}
          metalness={0.05}
        />
      </mesh>
      <mesh position={[leftWallX - 0.01, floorY + BUILDING.floorHeight - 0.06, 0]}>
        <boxGeometry args={[0.03, 0.04, BUILDING.depth]} />
        <meshStandardMaterial
          color={accent}
          emissive={accent}
          emissiveIntensity={0.2}
          metalness={0.2}
          roughness={0.4}
        />
      </mesh>
    </group>
  );
}

function OpenFrame() {
  const towerH = getTowerHeight();
  const baseY = BUILDING.towerBaseY + BUILDING.lobbyHeight;
  const halfW = BUILDING.width / 2;
  const halfD = BUILDING.depth / 2;
  const corners: [number, number][] = [
    [-halfW, -halfD],
    [halfW, -halfD],
    [-halfW, halfD],
    [halfW, halfD],
  ];

  return (
    <group>
      {corners.map(([x, z], i) => (
        <CornerPost key={i} x={x} z={z} baseY={baseY} height={towerH} />
      ))}

      {Array.from({ length: FLOOR_COUNT - 1 }, (_, i) => {
        const y = getFloorBaseY(i + 2);
        return (
          <group key={i}>
            {(
              [
                [0, -halfD, [BUILDING.width, 0.03, 0.03]],
                [-halfW, 0, [0.03, 0.03, BUILDING.depth]],
                [halfW, 0, [0.03, 0.03, BUILDING.depth]],
              ] as [number, number, [number, number, number]][]
            ).map(([x, z, size], j) => (
              <mesh key={j} position={[x, y, z]}>
                <boxGeometry args={size} />
                <meshStandardMaterial color="#7a9a82" metalness={0.35} roughness={0.45} />
              </mesh>
            ))}
          </group>
        );
      })}
    </group>
  );
}

function GroundLobby() {
  const y = BUILDING.towerBaseY + BUILDING.lobbyHeight / 2;
  const halfD = BUILDING.depth / 2;

  return (
    <group>
      <mesh position={[0, y, 0]} receiveShadow>
        <boxGeometry args={[BUILDING.width + 0.4, BUILDING.lobbyHeight, BUILDING.depth + 0.4]} />
        <meshStandardMaterial color="#f0f4f1" roughness={0.6} />
      </mesh>
      <Text
        position={[0, y + 0.15, -halfD - 0.06]}
        fontSize={0.14}
        color={TECH_ACCENT}
        anchorX="center"
        letterSpacing={0.06}
      >
        raiseHack HQ
      </Text>
    </group>
  );
}

function Rooftop() {
  const roofY = BUILDING.towerBaseY + getTotalBuildingHeight();
  return (
    <group position={[0, roofY, 0]}>
      <mesh position={[0, 0.04, 0]}>
        <boxGeometry args={[BUILDING.width + 0.15, 0.06, BUILDING.depth + 0.15]} />
        <meshStandardMaterial color="#b8c9bc" metalness={0.2} roughness={0.65} />
      </mesh>
      <mesh position={[0, 0.12, 0]}>
        <cylinderGeometry args={[0.03, 0.04, 0.35, 6]} />
        <meshStandardMaterial color={STEEL_COLOR} metalness={0.6} />
      </mesh>
      <mesh position={[0, 0.32, 0]}>
        <sphereGeometry args={[0.04, 8, 8]} />
        <meshStandardMaterial color={TECH_ACCENT} emissive={TECH_ACCENT} emissiveIntensity={0.55} />
      </mesh>
    </group>
  );
}

export function GlassBuilding() {
  return (
    <group>
      <ForestFloor />
      <GroundLobby />
      <OpenFrame />

      {Array.from({ length: FLOOR_COUNT }, (_, i) => (
        <FloorWalls key={`walls-${i}`} floor={i + 1} />
      ))}

      {Array.from({ length: FLOOR_COUNT }, (_, i) => (
        <BuildingFloor key={`floor-${i}`} floor={i + 1} />
      ))}

      <MeetingRoomsLayer />

      <Rooftop />
    </group>
  );
}
