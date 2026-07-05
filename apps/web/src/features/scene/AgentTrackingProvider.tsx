"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  type ReactNode,
  type RefObject,
} from "react";
import type { Group } from "three";

export interface ScreenAnchor {
  x: number;
  y: number;
}

interface AgentTrackingContextValue {
  registerAgentRef: (agentId: string, ref: RefObject<Group | null>) => void;
  unregisterAgentRef: (agentId: string) => void;
  getAgentRef: (agentId: string) => RefObject<Group | null> | undefined;
  screenAnchorRef: RefObject<ScreenAnchor | null>;
}

const AgentTrackingContext = createContext<AgentTrackingContextValue | null>(null);

export function AgentTrackingProvider({ children }: { children: ReactNode }) {
  const refsMap = useRef(new Map<string, RefObject<Group | null>>());
  const screenAnchorRef = useRef<ScreenAnchor | null>(null);

  const registerAgentRef = useCallback(
    (agentId: string, ref: RefObject<Group | null>) => {
      refsMap.current.set(agentId, ref);
    },
    [],
  );

  const unregisterAgentRef = useCallback((agentId: string) => {
    refsMap.current.delete(agentId);
  }, []);

  const getAgentRef = useCallback((agentId: string) => {
    return refsMap.current.get(agentId);
  }, []);

  const value = useMemo(
    () => ({
      registerAgentRef,
      unregisterAgentRef,
      getAgentRef,
      screenAnchorRef,
    }),
    [registerAgentRef, unregisterAgentRef, getAgentRef, screenAnchorRef],
  );

  return (
    <AgentTrackingContext.Provider value={value}>
      {children}
    </AgentTrackingContext.Provider>
  );
}

export function useAgentTracking(): AgentTrackingContextValue {
  const context = useContext(AgentTrackingContext);
  if (!context) {
    throw new Error("useAgentTracking must be used within AgentTrackingProvider");
  }
  return context;
}

/** World-space point used for camera focus and screen projection */
export const AGENT_FOCUS_HEIGHT = 0.38;
