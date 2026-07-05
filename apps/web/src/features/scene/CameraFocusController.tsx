"use client";

import { useEffect, useRef } from "react";
import { useFrame, useThree } from "@react-three/fiber";
import type { OrbitControls as OrbitControlsImpl } from "three-stdlib";
import { Vector3 } from "three";
import { useSelection } from "@/features/selection/SelectionProvider";
import {
  AGENT_FOCUS_HEIGHT,
  useAgentTracking,
} from "./AgentTrackingProvider";
import { FIXED_CAMERA } from "./buildingConfig";

const REST_TARGET = new Vector3(...FIXED_CAMERA.target);
const REST_OFFSET = new Vector3(...FIXED_CAMERA.position).sub(REST_TARGET);
const FOCUS_DISTANCE_SCALE = 0.36;
const SNAP_THRESHOLD = 0.06;

const agentFocusPoint = new Vector3();
const cameraOffset = new Vector3();
const desiredOffset = new Vector3();
const restCamera = new Vector3();

interface CameraFocusControllerProps {
  controlsRef: React.RefObject<OrbitControlsImpl | null>;
}

export function CameraFocusController({ controlsRef }: CameraFocusControllerProps) {
  const { selectedAgent } = useSelection();
  const { getAgentRef } = useAgentTracking();
  const { camera } = useThree();

  const goalTarget = useRef(new Vector3().copy(REST_TARGET));
  const goalOffset = useRef(new Vector3().copy(REST_OFFSET));
  const isAnimating = useRef(false);
  const trackingAgent = useRef(false);
  const zoomingIn = useRef(false);

  useEffect(() => {
    const controls = controlsRef.current;
    if (!controls) return;

    if (selectedAgent) {
      trackingAgent.current = true;
      zoomingIn.current = true;
      cameraOffset.subVectors(camera.position, controls.target);
      desiredOffset.copy(REST_OFFSET).multiplyScalar(FOCUS_DISTANCE_SCALE);
      return;
    }

    trackingAgent.current = false;
    zoomingIn.current = false;
    goalTarget.current.copy(REST_TARGET);
    goalOffset.current.copy(REST_OFFSET);
    isAnimating.current = true;
  }, [selectedAgent?.id, selectedAgent, controlsRef, camera]);

  useFrame((_, delta) => {
    const controls = controlsRef.current;
    if (!controls) return;

    if (trackingAgent.current && selectedAgent) {
      const group = getAgentRef(selectedAgent.id)?.current;
      if (!group) return;

      group.getWorldPosition(agentFocusPoint);
      agentFocusPoint.y += AGENT_FOCUS_HEIGHT;

      cameraOffset.subVectors(camera.position, controls.target);

      if (zoomingIn.current) {
        cameraOffset.lerp(desiredOffset, 1 - Math.exp(-delta * 4));
        if (cameraOffset.distanceTo(desiredOffset) < 0.08) {
          zoomingIn.current = false;
        }
      }

      const t = 1 - Math.exp(-delta * 10);
      controls.target.lerp(agentFocusPoint, t);
      camera.position.copy(controls.target).add(cameraOffset);
      controls.update();
      return;
    }

    if (!isAnimating.current) return;

    const t = 1 - Math.exp(-delta * 4.5);
    controls.target.lerp(goalTarget.current, t);
    cameraOffset.lerp(goalOffset.current, t);
    camera.position.copy(controls.target).add(cameraOffset);
    controls.update();

    restCamera.copy(controls.target).add(cameraOffset);
    const posClose = camera.position.distanceTo(restCamera) < SNAP_THRESHOLD;
    const targetClose = controls.target.distanceTo(goalTarget.current) < SNAP_THRESHOLD;

    if (posClose && targetClose) {
      controls.target.copy(goalTarget.current);
      cameraOffset.copy(goalOffset.current);
      camera.position.copy(restCamera);
      controls.update();
      isAnimating.current = false;
    }
  });

  return null;
}
