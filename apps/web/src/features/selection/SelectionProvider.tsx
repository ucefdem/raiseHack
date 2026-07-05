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
import { getMeetingRoomById } from "@/data/meetingRooms";

const SelectionContext = createContext<OfficeSelectionContext | null>(null);

export function SelectionProvider({ children }: { children: ReactNode }) {
  const [selectedDepartmentId, setSelectedDepartmentId] = useState<string | null>(
    null,
  );
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);
  const [selectedMeetingRoomId, setSelectedMeetingRoomId] = useState<string | null>(
    null,
  );

  const setSelectedDepartment = useCallback((departmentId: string | null) => {
    setSelectedDepartmentId(departmentId);
    setSelectedAgentId(null);
    setSelectedMeetingRoomId(null);
  }, []);

  const setSelectedAgent = useCallback((agentId: string | null) => {
    setSelectedAgentId(agentId);
    setSelectedMeetingRoomId(null);
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
    if (roomId) {
      setSelectedDepartmentId(null);
    }
  }, []);

  const clearSelection = useCallback(() => {
    setSelectedDepartmentId(null);
    setSelectedAgentId(null);
    setSelectedMeetingRoomId(null);
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
      setSelectedDepartment,
      setSelectedAgent,
      setSelectedMeetingRoom,
      clearSelection,
    }),
    [
      selectedDepartmentId,
      selectedAgentId,
      selectedMeetingRoomId,
      setSelectedDepartment,
      setSelectedAgent,
      setSelectedMeetingRoom,
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
