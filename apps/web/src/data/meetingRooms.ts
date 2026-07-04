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
