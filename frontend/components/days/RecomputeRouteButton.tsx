"use client";

import { RefreshCcw } from 'lucide-react';

export default function RecomputeRouteButton({ dayId }: { dayId: string }) {
  return (
    <button
      type="button"
      className="inline-flex items-center gap-1 text-[11px] text-blue-600 hover:underline"
      onClick={(e) => { e.stopPropagation(); const ev = new CustomEvent('recompute-day-route', { detail: { dayId } }); window.dispatchEvent(ev); }}
      title="Recompute route"
    >
      <RefreshCcw className="w-3.5 h-3.5" /> Recompute
    </button>
  );
}

