"use client";

import { departments, getDepartmentsByFloor } from "@/data/departments";
import { useSelection } from "@/features/selection/SelectionProvider";
import { FLOOR_COUNT } from "./buildingConfig";

function getSelectedFloor(): number {
  const dept = departments.find((d) => d.id === undefined);
  void dept;
  return 1;
}

export function FloorSlider() {
  const { selectedDepartmentId, setSelectedDepartment } = useSelection();

  const selectedFloor = selectedDepartmentId
    ? (departments.find((d) => d.id === selectedDepartmentId)?.floor ?? 1)
    : null;

  return (
    <div className="pointer-events-auto flex flex-col items-center gap-2 rounded-xl border border-white/10 bg-black/35 px-2 py-3 backdrop-blur-xl">
      <span className="text-[10px] font-medium uppercase tracking-widest text-white/40">
        Floors
      </span>
      <div className="flex flex-col gap-1.5">
        {Array.from({ length: FLOOR_COUNT }, (_, i) => FLOOR_COUNT - i).map(
          (floor) => {
            const floorDepts = getDepartmentsByFloor(floor);
            const isActive = floorDepts.some((d) => d.id === selectedDepartmentId);
            const title = floorDepts.map((d) => d.name).join(" · ");

            return (
              <button
                key={floor}
                type="button"
                title={title || `Floor ${floor}`}
                onClick={() => {
                  const primary = floorDepts[0];
                  if (primary) setSelectedDepartment(primary.id);
                }}
                className={`relative flex h-9 w-9 items-center justify-center rounded-lg text-xs font-semibold transition ${
                  isActive
                    ? "bg-emerald-400 text-slate-900 shadow-lg shadow-emerald-400/30"
                    : "bg-white/8 text-white/60 hover:bg-white/15 hover:text-white"
                }`}
              >
                F{floor}
                {floorDepts.length > 1 && (
                  <span className="absolute -right-0.5 -top-0.5 flex h-3.5 w-3.5 items-center justify-center rounded-full bg-white/20 text-[8px] font-bold text-white">
                    {floorDepts.length}
                  </span>
                )}
              </button>
            );
          },
        )}
      </div>
      <div className="mt-1 h-16 w-1 rounded-full bg-white/10">
        <div
          className="w-full rounded-full bg-emerald-400/80 transition-all"
          style={{
            height: selectedFloor
              ? `${(selectedFloor / FLOOR_COUNT) * 100}%`
              : "33%",
          }}
        />
      </div>
    </div>
  );
}
