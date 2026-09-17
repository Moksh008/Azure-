export default function ErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div
      role="alert"
      className="flex flex-col items-center gap-3 text-center py-12 px-6 rounded-2xl bg-white border border-border"
    >
      <span
        className="w-10 h-10 rounded-full bg-coral/10 text-coral flex items-center justify-center font-bold text-lg"
        aria-hidden="true"
      >
        !
      </span>
      <p className="text-ink font-semibold">Something went wrong</p>
      <p className="text-muted text-sm max-w-sm">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-2 rounded-[10px] bg-ink text-white text-sm font-semibold px-5 py-2.5 cursor-pointer hover:opacity-90"
        >
          Try again
        </button>
      )}
    </div>
  );
}
