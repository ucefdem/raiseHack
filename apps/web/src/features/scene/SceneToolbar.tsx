"use client";

import {
  Grid3x3,
  History,
  Image as ImageIcon,
  Layers,
  Minus,
  Plus,
  RotateCcw,
  RotateCw,
  Search,
  Settings,
  SlidersHorizontal,
  Trash2,
} from "lucide-react";
import type { OrbitControls as OrbitControlsImpl } from "three-stdlib";
import { stepZoom } from "./ZoomControls";

function ToolButton({
  children,
  label,
  onClick,
}: {
  children: React.ReactNode;
  label: string;
  onClick?: () => void;
}) {
  return (
    <button
      type="button"
      title={label}
      onClick={onClick}
      className="flex h-8 w-8 items-center justify-center rounded-lg text-white/70 transition hover:bg-white/10 hover:text-white"
    >
      {children}
    </button>
  );
}

interface SceneToolbarProps {
  zoom: number;
  controlsRef: React.RefObject<OrbitControlsImpl | null>;
}

export function SceneToolbar({ zoom, controlsRef }: SceneToolbarProps) {
  return (
    <>
      <div className="pointer-events-auto absolute left-1/2 top-4 z-10 flex -translate-x-1/2 items-center gap-1 rounded-xl border border-white/10 bg-black/35 px-3 py-1.5 backdrop-blur-xl">
        <ToolButton label="Undo">
          <RotateCcw className="h-4 w-4" />
        </ToolButton>
        <ToolButton label="Redo">
          <RotateCw className="h-4 w-4" />
        </ToolButton>
        <div className="mx-1 h-5 w-px bg-white/15" />
        <ToolButton label="Zoom out" onClick={() => stepZoom(controlsRef, "out")}>
          <Minus className="h-4 w-4" />
        </ToolButton>
        <span className="min-w-[3rem] px-2 text-center text-xs font-medium tabular-nums text-emerald-300">
          {zoom}%
        </span>
        <ToolButton label="Zoom in" onClick={() => stepZoom(controlsRef, "in")}>
          <Plus className="h-4 w-4" />
        </ToolButton>
        <div className="mx-1 h-5 w-px bg-white/15" />
        <ToolButton label="Grid">
          <Grid3x3 className="h-4 w-4" />
        </ToolButton>
        <ToolButton label="History">
          <History className="h-4 w-4" />
        </ToolButton>
        <ToolButton label="Layers">
          <Layers className="h-4 w-4" />
        </ToolButton>
        <ToolButton label="Gallery">
          <ImageIcon className="h-4 w-4" />
        </ToolButton>
      </div>

      <div className="pointer-events-none absolute bottom-4 left-1/2 z-10 flex -translate-x-1/2 items-center gap-1 rounded-xl border border-white/10 bg-black/35 px-3 py-1.5 backdrop-blur-xl">
        <ToolButton label="Adjust">
          <SlidersHorizontal className="h-4 w-4" />
        </ToolButton>
        <ToolButton label="Settings">
          <Settings className="h-4 w-4" />
        </ToolButton>
        <div className="mx-1 h-5 w-px bg-white/15" />
        <ToolButton label="Delete">
          <Trash2 className="h-4 w-4" />
        </ToolButton>
        <ToolButton label="Search">
          <Search className="h-4 w-4" />
        </ToolButton>
      </div>
    </>
  );
}
