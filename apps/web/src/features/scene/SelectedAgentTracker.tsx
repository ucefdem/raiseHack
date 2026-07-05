"use client";

import { useFrame, useThree } from "@react-three/fiber";
import { Vector3 } from "three";
import { useSelection } from "@/features/selection/SelectionProvider";
import {
  AGENT_FOCUS_HEIGHT,
  useAgentTracking,
} from "./AgentTrackingProvider";

const focusPoint = new Vector3();
const projected = new Vector3();

export function SelectedAgentTracker() {
  const { selectedAgent } = useSelection();
  const { getAgentRef, screenAnchorRef } = useAgentTracking();
  const { camera, size } = useThree();

  useFrame(() => {
    if (!selectedAgent) {
      screenAnchorRef.current = null;
      return;
    }

    const group = getAgentRef(selectedAgent.id)?.current;
    if (!group) return;

    group.getWorldPosition(focusPoint);
    focusPoint.y += AGENT_FOCUS_HEIGHT;

    projected.copy(focusPoint).project(camera);

    if (projected.z > 1) {
      screenAnchorRef.current = null;
      return;
    }

    screenAnchorRef.current = {
      x: (projected.x * 0.5 + 0.5) * size.width,
      y: (-projected.y * 0.5 + 0.5) * size.height,
    };
  });

  return null;
}
