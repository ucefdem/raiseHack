/** Shared meeting space — agents and humans from multiple departments */
export interface MeetingRoom {
  id: string;
  name: string;
  floor: number;
  meetUrl: string;
  /** Departments that can join this room */
  departmentIds: string[];
  capacity?: number;
  /** Position on the floor [x, y-offset from slab, z] */
  position: [number, number, number];
  /** Accent color for the room pod */
  accentColor?: string;
}
