"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import type { OfficeSelectionContext } from "@raisehack/shared";
import { getAgentById } from "@/data/agents";
import { getDepartmentById } from "@/data/departments";
import {
  getMeetingRoomById,
  getMeetingRoomsByFloor,
  getPrimaryMeetingRoomForDepartment,
} from "@/data/meetingRooms";

const SelectionContext = createContext<OfficeSelectionContext | null>(null);

export function SelectionProvider({ children }: { children: ReactNode }) {
  const [selectedDepartmentId, setSelectedDepartmentId] = useState<string | null>(
    null,
  );
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);
  const [selectedMeetingRoomId, setSelectedMeetingRoomId] = useState<string | null>(
    null,
  );
  const [meetDeployAgentId, setMeetDeployAgentId] = useState<string | null>(null);

  const setSelectedDepartment = useCallback((departmentId: string | null) => {
    setSelectedDepartmentId(departmentId);
    setSelectedAgentId(null);
    setSelectedMeetingRoomId(null);
    setMeetDeployAgentId(null);
  }, []);

  const setSelectedAgent = useCallback((agentId: string | null) => {
    setSelectedAgentId(agentId);
    setSelectedMeetingRoomId(null);
    setMeetDeployAgentId(null);
    if (agentId) {
      const agent = getAgentById(agentId);
      if (agent) {
        setSelectedDepartmentId(agent.departmentId);
      }
    }
  }, []);

  const setSelectedMeetingRoom = useCallback((roomId: string | null) => {
    setSelectedMeetingRoomId(roomId);
    setSelectedAgentId(null);
    setMeetDeployAgentId(null);
    if (roomId) {
      setSelectedDepartmentId(null);
    }
  }, []);

  const openMeetForAgent = useCallback((agentId: string) => {
    const agent = getAgentById(agentId);
    if (!agent) return;

    let room =
      getPrimaryMeetingRoomForDepartment(agent.departmentId) ??
      getMeetingRoomsByFloor(getDepartmentById(agent.departmentId)?.floor ?? 1)[0];

    if (!room) return;

    setSelectedAgentId(null);
    setSelectedDepartmentId(null);
    setMeetDeployAgentId(agentId);
    setSelectedMeetingRoomId(room.id);
  }, []);

  const clearSelection = useCallback(() => {
    setSelectedDepartmentId(null);
    setSelectedAgentId(null);
    setSelectedMeetingRoomId(null);
    setMeetDeployAgentId(null);
  }, []);

  const value = useMemo<OfficeSelectionContext>(
    () => ({
      selectedDepartmentId,
      selectedAgentId,
      selectedMeetingRoomId,
      selectedDepartment: selectedDepartmentId
        ? (getDepartmentById(selectedDepartmentId) ?? null)
        : null,
      selectedAgent: selectedAgentId
        ? (getAgentById(selectedAgentId) ?? null)
        : null,
      selectedMeetingRoom: selectedMeetingRoomId
        ? (getMeetingRoomById(selectedMeetingRoomId) ?? null)
        : null,
      meetDeployAgent: meetDeployAgentId
        ? (getAgentById(meetDeployAgentId) ?? null)
        : null,
      setSelectedDepartment,
      setSelectedAgent,
      setSelectedMeetingRoom,
      openMeetForAgent,
      clearSelection,
    }),
    [
      selectedDepartmentId,
      selectedAgentId,
      selectedMeetingRoomId,
      meetDeployAgentId,
      setSelectedDepartment,
      setSelectedAgent,
      setSelectedMeetingRoom,
      openMeetForAgent,
      clearSelection,
    ],
  );

  return (
    <SelectionContext.Provider value={value}>
      {children}
    </SelectionContext.Provider>
  );
}

export function useSelection(): OfficeSelectionContext {
  const context = useContext(SelectionContext);
  if (!context) {
    throw new Error("useSelection must be used within SelectionProvider");
  }
  return context;
}
