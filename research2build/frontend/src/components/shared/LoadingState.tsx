export default function LoadingState({ label = "Loading…" }: { label?: string }) {
  return (
    <div
      role="status"
      aria-live="polite"
      className="flex flex-col items-center justify-center gap-3 py-16 text-muted"
    >
      <span className="w-8 h-8 rounded-full border-[3px] border-border border-t-ink animate-spin" />
      <span className="text-sm font-medium">{label}</span>
    </div>
  );
}
