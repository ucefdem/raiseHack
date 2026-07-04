import { BUILDING } from "@/features/scene/buildingConfig";

export type SignSide = "left" | "right";

export interface DepartmentFloorLayout {
  signSide: SignSide;
  zoneCenter: [number, number];
  zoneHalfSize: number;
  colorZone: {
    offset: [number, number];
    size: [number, number];
  };
}

/** Layout for a department within a shared or solo floor */
export function getDepartmentFloorLayout(
  indexOnFloor: number,
  totalOnFloor: number,
): DepartmentFloorLayout {
  const halfW = BUILDING.width / 2 - 0.15;
  const depth = BUILDING.depth - 0.2;
  // Keep agents in the front half — meeting nooks live in the back
  const frontZ = -0.35;

  if (totalOnFloor <= 1) {
    return {
      signSide: "left",
      zoneCenter: [0, frontZ],
      zoneHalfSize: halfW - 0.3,
      colorZone: { offset: [0, frontZ * 0.3], size: [BUILDING.width - 0.2, depth * 0.65] },
    };
  }

  const isLeft = indexOnFloor === 0;
  const xOffset = isLeft ? -halfW * 0.45 : halfW * 0.45;

  return {
    signSide: isLeft ? "left" : "right",
    zoneCenter: [xOffset, frontZ],
    zoneHalfSize: halfW * 0.38,
    colorZone: { offset: [xOffset, frontZ * 0.2], size: [halfW * 0.92, depth * 0.55] },
  };
}
