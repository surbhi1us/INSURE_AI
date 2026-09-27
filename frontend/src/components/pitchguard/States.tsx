export function GeneratingState() {
  return (
    <section className="surface-card p-7">
      <p className="font-mono text-[11px] tracking-wide text-primary">
        GENERATING
      </p>
      <h2 className="mt-2 text-[22px] font-semibold tracking-tight text-navy">
        Reading client context and policy documents…
      </h2>
      <div className="mt-7 grid gap-4 lg:grid-cols-3">
        {[0, 1, 2].map((index) => (
          <div
            key={index}
            className="space-y-3 rounded-2xl border border-border bg-surface p-5"
          >
            <div className="shimmer-line h-2.5 w-2/3" />
            <div className="shimmer-line h-2.5 w-full" />
            <div className="shimmer-line h-2.5 w-4/5" />
          </div>
        ))}
      </div>
      <div className="mt-4 space-y-3 rounded-2xl border border-border bg-surface p-5">
        <div className="shimmer-line h-2.5 w-1/3" />
        <div className="shimmer-line h-2.5 w-full" />
        <div className="shimmer-line h-2.5 w-5/6" />
        <div className="shimmer-line h-2.5 w-2/3" />
      </div>
    </section>
  );
}

export function EmptyState() {
  return (
    <section className="surface-card p-10 text-center">
      <div className="mx-auto grid size-12 place-items-center rounded-2xl bg-accent">
        <span className="font-mono text-[15px] text-accent-foreground">◇</span>
      </div>
      <h2 className="mx-auto mt-5 max-w-lg text-[22px] font-semibold tracking-tight text-navy">
        No pitch generated yet
      </h2>
      <p className="mx-auto mt-2 max-w-md text-[14px] leading-relaxed text-muted-foreground">
        Enter the client company, select the policies to compare, then generate a
        pitch. Client intelligence, the recommendation and the claim audit will
        appear here.
      </p>
    </section>
  );
}

export function ErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry: () => void;
}) {
  return (
    <section className="rounded-3xl border border-contradicted/30 bg-contradicted-soft/50 p-7">
      <p className="font-mono text-[11px] tracking-wide text-contradicted">
        GENERATION FAILED
      </p>
      <h2 className="mt-2 text-[20px] font-semibold tracking-tight text-navy">
        {message}
      </h2>
      <button
        type="button"
        onClick={onRetry}
        className="mt-5 rounded-xl border border-border bg-surface px-5 py-2.5 text-[14px] font-semibold text-navy transition-colors hover:border-border-strong"
      >
        Try again
      </button>
    </section>
  );
}

export function PlaceholderNotice() {
  return (
    <div className="flex items-start gap-3 rounded-2xl border border-primary/25 bg-accent/50 p-5">
      <span className="mt-0.5 shrink-0 font-mono text-[12px] text-primary">
        ℹ
      </span>
      <p className="min-w-0 text-[14px] text-secondary-foreground">
        <span className="font-semibold text-navy">Demo state.</span> No backend
        is connected, so company profile, policy benefits, claims, confidence
        values and evidence are labelled placeholders — not real insurer facts.
      </p>
    </div>
  );
}
