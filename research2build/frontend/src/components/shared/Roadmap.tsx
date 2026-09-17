import type { RoadmapPlan } from "../../types";

export default function Roadmap({ roadmap }: { roadmap: RoadmapPlan }) {
  return (
    <div className="bg-white rounded-2xl border border-border p-6">
      <div className="flex items-center justify-between mb-5">
        <p className="font-display font-bold text-lg text-ink">Roadmap</p>
        <p className="text-muted text-sm">{roadmap.total_weeks} weeks total</p>
      </div>
      <ol className="space-y-0">
        {roadmap.milestones.map((m, i) => (
          <li key={m.phase} className="flex gap-4">
            <div className="flex flex-col items-center">
              <span className="w-3 h-3 rounded-full bg-mint-deep shrink-0 mt-1" aria-hidden="true" />
              {i < roadmap.milestones.length - 1 && (
                <span className="w-px flex-1 bg-border" aria-hidden="true" />
              )}
            </div>
            <div className="pb-6">
              <div className="flex items-baseline gap-2 flex-wrap">
                <p className="font-semibold text-ink">{m.phase}</p>
                <p className="text-xs text-muted">
                  weeks {m.start_week}–{m.end_week} ({m.duration_weeks}w)
                </p>
              </div>
              {m.deliverables.length > 0 && (
                <ul className="mt-1.5 space-y-1">
                  {m.deliverables.map((d, di) => (
                    <li key={di} className="text-sm text-muted">
                      {d}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </li>
        ))}
      </ol>
    </div>
  );
}
