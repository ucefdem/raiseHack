export interface MeetLink {
  departmentId: string;
  agentId?: string;
  url: string;
  label: string;
}

export interface MeetJoinEvent {
  userId: string;
  departmentId: string;
  agentId?: string;
  timestamp: string;
}
