import type { MeetingRoom } from "@raisehack/shared";
import { BUILDING, getFloorBaseY } from "./buildingConfig";

/** Camera zoom when entering a meeting room nook */
export const ROOM_FOCUS_DISTANCE_SCALE = 0.3;

/** Eye-level focus inside the pod (table / screen height) */
const ROOM_FOCUS_HEIGHT = 0.35;

export function getMeetingRoomFocusPoint(room: MeetingRoom): [number, number, number] {
  const floorY = getFloorBaseY(room.floor);
  const [x, yOff, z] = room.position;
  const podY = floorY + BUILDING.slabThickness + yOff;
  return [x, podY + ROOM_FOCUS_HEIGHT, z];
}
