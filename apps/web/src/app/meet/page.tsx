import { Suspense } from "react";
import { MeetDeployPanel } from "@/features/meet/MeetDeployPanel";

export default function MeetPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-slate-950 text-slate-400">
          Loading…
        </div>
      }
    >
      <MeetDeployPanel />
    </Suspense>
  );
}
