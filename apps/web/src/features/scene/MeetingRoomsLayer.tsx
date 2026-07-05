"use client";

import { meetingRooms } from "@/data/meetingRooms";
import { MeetingRoomPod } from "./MeetingRoomPod";

export function MeetingRoomsLayer() {
  return (
    <group>
      {meetingRooms.map((room) => (
        <MeetingRoomPod key={room.id} room={room} />
      ))}
    </group>
  );
}
