import type { MeetingRoom } from "@raisehack/shared";

export const meetingRooms: MeetingRoom[] = [
  {
    id: "room-engineering-huddle",
    name: "Eng huddle",
    floor: 1,
    meetUrl: "https://meet.google.com/lookup/eng-huddle",
    departmentIds: ["dept-engineering"],
    capacity: 6,
    position: [1.45, 0.02, 1.15],
    accentColor: "#059669",
  },
  {
    id: "room-cross-functional",
    name: "Cross-functional",
    floor: 2,
    meetUrl: "https://meet.google.com/lookup/cross-functional-room",
    departmentIds: ["dept-engineering", "dept-platform", "dept-product"],
    capacity: 12,
    position: [1.45, 0.02, 1.2],
    accentColor: "#2563eb",
  },
  {
    id: "room-incident",
    name: "Incident bridge",
    floor: 2,
    meetUrl: "https://meet.google.com/lookup/incident-bridge",
    departmentIds: ["dept-platform", "dept-engineering"],
    capacity: 10,
    position: [-1.45, 0.02, 1.2],
    accentColor: "#ef4444",
  },
  {
    id: "room-gtm",
    name: "GTM war room",
    floor: 3,
    meetUrl: "https://meet.google.com/lookup/gtm-war-room",
    departmentIds: ["dept-sales", "dept-executive", "dept-product"],
    capacity: 8,
    position: [1.45, 0.02, 1.2],
    accentColor: "#f59e0b",
  },
];

export function getMeetingRoomById(id: string): MeetingRoom | undefined {
  return meetingRooms.find((room) => room.id === id);
}

export function getMeetingRoomsByFloor(floor: number): MeetingRoom[] {
  return meetingRooms.filter((room) => room.floor === floor);
}

export function getMeetingRoomsForDepartment(departmentId: string): MeetingRoom[] {
  return meetingRooms.filter((room) => room.departmentIds.includes(departmentId));
}

/** Best room for an agent — dedicated dept room first, then floor fallback */
export function getPrimaryMeetingRoomForDepartment(departmentId: string): MeetingRoom | undefined {
  const deptRooms = getMeetingRoomsForDepartment(departmentId);
  if (deptRooms.length > 0) {
    const dedicated = deptRooms.find((room) => room.departmentIds.length === 1);
    if (dedicated) return dedicated;
    return [...deptRooms].sort(
      (a, b) => a.departmentIds.length - b.departmentIds.length,
    )[0];
  }
  return meetingRooms.find((room) => room.id === "room-cross-functional");
}
