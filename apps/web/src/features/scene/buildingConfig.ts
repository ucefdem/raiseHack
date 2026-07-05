import type { DepartmentZone } from "@raisehack/shared";

export const BUILDING = {
  width: 4.6,
  depth: 3.6,
  floorHeight: 2.5,
  lobbyHeight: 1.35,
  slabThickness: 0.08,
  pedestalSize: 9.5,
  balconyDepth: 0.38,
  towerBaseY: 0.12,
} as const;

export const FLOOR_COUNT = 3;

/** Light forest palette */
export const FOREST = {
  floor: "#4a7a52",
  floorLight: "#5c9464",
  clearing: "#6fa876",
  moss: "#82b88a",
  canopy: "#5a9470",
  foliage: "#52a062",
  foliageLight: "#72c082",
  trunk: "#7a6048",
  trunkDark: "#6a5038",
} as const;

export const HIGHLIGHT_COLOR = "#86efac";
export const TECH_ACCENT = "#4ade80";
export const FACADE_COLOR = "#e8eaed";
export const STEEL_COLOR = "#5a7a62";
export const GLASS_COLOR = "#cbd5e1";

export function getTowerHeight(): number {
  return FLOOR_COUNT * BUILDING.floorHeight;
}

export function getTotalBuildingHeight(): number {
  return BUILDING.lobbyHeight + getTowerHeight();
}

export function getFloorBaseY(floor: number): number {
  return (
    BUILDING.towerBaseY +
    BUILDING.lobbyHeight +
    (floor - 1) * BUILDING.floorHeight
  );
}

export function getFloorCenterY(floor: number): number {
  return getFloorBaseY(floor) + BUILDING.floorHeight / 2;
}

export function getBuildingCenterY(): number {
  return BUILDING.towerBaseY + BUILDING.lobbyHeight + getTowerHeight() / 2;
}

export function makeDepartmentZone(floor: number, color: string): DepartmentZone {
  return {
    position: [0, getFloorBaseY(floor) + BUILDING.slabThickness / 2, 0],
    size: [BUILDING.width - 0.15, BUILDING.slabThickness, BUILDING.depth - 0.15],
    color,
  };
}

const centerY = getBuildingCenterY();

/** Fixed angle camera — zoom enabled via OrbitControls */
export const FIXED_CAMERA = {
  position: [8.2, centerY + 1.6, 8.2] as [number, number, number],
  fov: 32,
  target: [0, centerY, 0] as [number, number, number],
};
