"use client";

import { Component, Suspense, useRef, useState, type ReactNode } from "react";
import { Canvas } from "@react-three/fiber";
import type { OrbitControls as OrbitControlsImpl } from "three-stdlib";
import { GlassBuilding } from "./GlassBuilding";
import { CameraFocusController } from "./CameraFocusController";
import { SelectedAgentTracker } from "./SelectedAgentTracker";
import { FIXED_CAMERA } from "./buildingConfig";
import { SceneToolbar } from "./SceneToolbar";
import { FloorSlider } from "./FloorSlider";
import { ZoomControls } from "./ZoomControls";

class SceneErrorBoundary extends Component<
  { children: ReactNode },
  { error: Error | null }
> {
  state = { error: null as Error | null };

  static getDerivedStateFromError(error: Error) {
    return { error };
  }

  render() {
    if (this.state.error) {
      return (
        <div className="flex h-full w-full flex-col items-center justify-center gap-2 p-6 text-center">
          <p className="text-sm font-medium text-white/80">3D scene failed to load</p>
          <p className="max-w-sm text-xs text-white/45">{this.state.error.message}</p>
        </div>
      );
    }
    return this.props.children;
  }
}

function SceneContent({
  controlsRef,
  onZoomChange,
}: {
  controlsRef: React.RefObject<OrbitControlsImpl | null>;
  onZoomChange: (percent: number) => void;
}) {
  return (
    <>
      <fog attach="fog" args={["#6a9a72", 26, 58]} />

      <ambientLight intensity={0.78} color="#e8f5e9" />
      <directionalLight
        position={[6, 14, 5]}
        intensity={1.25}
        color="#f5faf5"
        castShadow
      />
      <directionalLight position={[-4, 8, -3]} intensity={0.35} color="#a8d4b0" />
      <hemisphereLight args={["#9fd4a8", "#4a7a52", 0.55]} />

      <GlassBuilding />
      <CameraFocusController controlsRef={controlsRef} />
      <SelectedAgentTracker />
      <ZoomControls controlsRef={controlsRef} onZoomChange={onZoomChange} />
    </>
  );
}

export function BuildingScene() {
  const controlsRef = useRef<OrbitControlsImpl | null>(null);
  const [zoom, setZoom] = useState(40);

  return (
    <div className="relative h-full w-full bg-[#5a9470]">
      <SceneErrorBoundary>
        <Canvas
          shadows
          className="h-full w-full"
          camera={{
            position: FIXED_CAMERA.position,
            fov: FIXED_CAMERA.fov,
          }}
          onCreated={({ camera, gl }) => {
            camera.lookAt(...FIXED_CAMERA.target);
            gl.setClearColor(0x000000, 0);
          }}
          gl={{ antialias: true, alpha: true }}
        >
          <Suspense fallback={null}>
            <SceneContent controlsRef={controlsRef} onZoomChange={setZoom} />
          </Suspense>
        </Canvas>
      </SceneErrorBoundary>

      <SceneToolbar zoom={zoom} controlsRef={controlsRef} />

      <div className="pointer-events-auto absolute left-4 top-1/2 z-10 -translate-y-1/2">
        <FloorSlider />
      </div>

      <div className="pointer-events-none absolute bottom-4 left-4 rounded-md bg-black/35 px-3 py-1.5 text-xs text-slate-300 backdrop-blur">
        Drag to rotate · Scroll to zoom · Click agent or meeting room
      </div>
    </div>
  );
}
