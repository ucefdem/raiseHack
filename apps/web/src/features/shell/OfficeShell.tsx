"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { AgentDetailModal } from "@/features/agents/AgentDetailModal";
import { DepartmentMissionModal } from "@/features/departments/DepartmentMissionModal";
import { MeetingRoomModal } from "@/features/meeting/MeetingRoomModal";
import { AgentTrackingProvider } from "@/features/scene/AgentTrackingProvider";
import {
  SelectionProvider,
  useSelection,
} from "@/features/selection/SelectionProvider";
import {
  CompanyOpsBar,
  CompanyOpsPanel,
  type OpsPanel,
} from "@/features/shell/CompanyOpsBar";

const BuildingScene = dynamic(
  () =>
    import("@/features/scene/BuildingScene").then((mod) => mod.BuildingScene),
  {
    ssr: false,
    loading: () => (
      <div className="flex h-full w-full items-center justify-center bg-[#5a9470]">
        <p className="text-sm text-white/60">Loading 3D office…</p>
      </div>
    ),
  },
);

function OfficeShellContent() {
  const [opsPanel, setOpsPanel] = useState<OpsPanel>(null);
  const { selectedMeetingRoom } = useSelection();
  const roomFocusActive = Boolean(selectedMeetingRoom);

  return (
    <div className="relative h-screen w-screen overflow-hidden">
      {/* Light forest backdrop */}
      <div className="absolute inset-0 bg-[#5a9470]" />
      <div className="absolute inset-0 bg-gradient-to-b from-[#8ec49a]/75 via-[#6aaa78]/50 to-[#4a8260]/70" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_50%_15%,rgba(200,240,210,0.5),transparent_55%)]" />

      <div className="pointer-events-none absolute inset-0 shadow-[inset_0_0_80px_rgba(40,80,50,0.2)]" />

      <main className="absolute inset-0">
        <BuildingScene />
        <div
          className={`pointer-events-none absolute inset-0 z-[1] bg-black/35 transition-opacity duration-500 ease-out ${
            roomFocusActive ? "opacity-100" : "opacity-0"
          }`}
          aria-hidden
        />
      </main>

      <header className="pointer-events-none absolute left-0 right-0 top-0 z-10 flex items-start justify-between px-6 py-5">
        <div>
          <p className="text-[10px] font-medium uppercase tracking-[0.28em] text-white/35">
            raiseHack
          </p>
          <h1 className="text-sm font-light tracking-wide text-white/75">
            Horizon AI Office
          </h1>
        </div>
        <p className="hidden text-[10px] uppercase tracking-widest text-white/25 sm:block">
          Forest campus
        </p>
      </header>

      <CompanyOpsBar activePanel={opsPanel} onPanelChange={setOpsPanel} />
      <CompanyOpsPanel panel={opsPanel} onClose={() => setOpsPanel(null)} />

      <AgentDetailModal />
      <DepartmentMissionModal />
      <MeetingRoomModal />
    </div>
  );
}

export function OfficeShell() {
  return (
    <SelectionProvider>
      <AgentTrackingProvider>
        <OfficeShellContent />
      </AgentTrackingProvider>
    </SelectionProvider>
  );
}
