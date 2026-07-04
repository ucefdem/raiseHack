"use client";

interface ModulePlaceholderProps {
  title: string;
  owner: string;
  description: string;
  active?: boolean;
}

export function ModulePlaceholder({
  title,
  owner,
  description,
  active = false,
}: ModulePlaceholderProps) {
  return (
    <div
      className={`rounded-lg border p-3 ${
        active
          ? "border-blue-500/50 bg-blue-500/5"
          : "border-slate-700/60 bg-slate-900/40"
      }`}
    >
      <div className="flex items-center justify-between gap-2">
        <h3 className="text-sm font-medium text-slate-200">{title}</h3>
        <span className="rounded-full bg-slate-800 px-2 py-0.5 text-[10px] uppercase tracking-wide text-slate-400">
          {owner}
        </span>
      </div>
      <p className="mt-1 text-xs text-slate-400">{description}</p>
    </div>
  );
}
