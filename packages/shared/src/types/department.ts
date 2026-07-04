export interface DepartmentZone {
  /** Position in 3D scene [x, y, z] */
  position: [number, number, number];
  /** Size of clickable zone [width, height, depth] */
  size: [number, number, number];
  /** Optional accent color (hex) */
  color?: string;
}

export interface DepartmentPlanItem {
  id: string;
  title: string;
  date?: string;
  status?: "planned" | "in-progress" | "done";
}

export interface DepartmentMission {
  mission: string;
  goals: string[];
  calendar: DepartmentPlanItem[];
}

export interface Department {
  id: string;
  name: string;
  description: string;
  floor: number;
  zone: DepartmentZone;
  meetUrl?: string;
  agentIds: string[];
  /** Mission, OKRs, and calendar shown in floor popup */
  missionPlan?: DepartmentMission;
}
