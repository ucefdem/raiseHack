"use client";

import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import type { OrbitControls as OrbitControlsImpl } from "three-stdlib";
import { Vector3 } from "three";
import { useSelection } from "@/features/selection/SelectionProvider";
import { FIXED_CAMERA } from "./buildingConfig";

/** Default camera distance maps to this label (reference-style HUD) */
export const ZOOM_DEFAULT_PERCENT = 40;

interface ZoomControlsProps {
  controlsRef: React.RefObject<OrbitControlsImpl | null>;
  onZoomChange: (percent: number) => void;
}

export function ZoomControls({ controlsRef, onZoomChange }: ZoomControlsProps) {
  const initialDistance = useRef<number | null>(null);
  const lastPercent = useRef<number | null>(null);
  const { selectedAgent } = useSelection();

  useFrame(({ camera }) => {
    const controls = controlsRef.current;
    if (!controls) return;

    const dist = camera.position.distanceTo(controls.target);
    if (initialDistance.current === null) {
      initialDistance.current = dist;
    }
    const base = initialDistance.current ?? dist;

    const percent = Math.max(1, Math.round((base / dist) * ZOOM_DEFAULT_PERCENT));
    if (percent === lastPercent.current) return;
    lastPercent.current = percent;
    onZoomChange(percent);
  });

  return (
    <OrbitControls
      ref={controlsRef}
      target={FIXED_CAMERA.target}
      enableRotate
      enablePan={!selectedAgent}
      enableZoom
      minDistance={0.5}
      maxDistance={Infinity}
      zoomSpeed={0.9}
      panSpeed={0.8}
      rotateSpeed={0.7}
      maxPolarAngle={Math.PI / 2}
    />
  );
}

export function stepZoom(
  controlsRef: React.RefObject<OrbitControlsImpl | null>,
  direction: "in" | "out",
) {
  const controls = controlsRef.current;
  if (!controls) return;

  const camera = controls.object;
  const offset = new Vector3().subVectors(camera.position, controls.target);
  const factor = direction === "in" ? 0.85 : 1.18;
  offset.multiplyScalar(factor);

  if (offset.length() < 0.5) return;

  camera.position.copy(controls.target).add(offset);
  controls.update();
}
