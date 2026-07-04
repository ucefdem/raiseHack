export type PresenceState = "online" | "idle" | "away";

export interface PresenceEvent {
  userId: string;
  departmentId: string | null;
  state: PresenceState;
  timestamp: string;
  displayName?: string;
  /** Optional avatar position in 3D scene */
  position?: [number, number, number];
}

export interface DepartmentOccupancy {
  departmentId: string;
  userIds: string[];
  count: number;
}
