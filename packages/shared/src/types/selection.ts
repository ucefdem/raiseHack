import type { Agent } from "./agent";
import type { Department } from "./department";
import type { MeetingRoom } from "./meetingRoom";
import type { DepartmentOccupancy } from "./presence";

/** Selection state exposed by 3D frontend for other modules */
export interface OfficeSelection {
  selectedDepartmentId: string | null;
  selectedAgentId: string | null;
  selectedMeetingRoomId: string | null;
}

export interface OfficeSelectionContext extends OfficeSelection {
  selectedDepartment: Department | null;
  selectedAgent: Agent | null;
  selectedMeetingRoom: MeetingRoom | null;
  setSelectedDepartment: (departmentId: string | null) => void;
  setSelectedAgent: (agentId: string | null) => void;
  setSelectedMeetingRoom: (roomId: string | null) => void;
  clearSelection: () => void;
}

/** Realtime channel event names — align early across team */
export const REALTIME_CHANNELS = {
  PRESENCE: "presence",
  PRESENCE_SYNC: "presence:sync",
  CHAT: "chat",
} as const;

export type RealtimeChannel = (typeof REALTIME_CHANNELS)[keyof typeof REALTIME_CHANNELS];

export interface AppDataSnapshot {
  departments: Department[];
  agents: Agent[];
  occupancy: DepartmentOccupancy[];
}
