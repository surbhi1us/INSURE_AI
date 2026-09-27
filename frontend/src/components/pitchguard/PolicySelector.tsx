import { POLICY_OPTIONS } from "@/lib/pitchguard";

interface PolicySelectorProps {
  selected: string[];
  onToggle: (id: string) => void;
}

export function PolicySelector({ selected, onToggle }: PolicySelectorProps) {
  return (
    <section className="surface-card p-7">
      <div className="grid grid-cols-[minmax(0,1fr)_auto] items-start gap-4">
        <div className="min-w-0">
          <h2 className="text-[22px] font-semibold tracking-tight text-navy">
            Policy intelligence
          </h2>
          <p className="mt-1.5 text-[14px] text-muted-foreground">
            Choose the policies to compare and audit against their source
            documents.
          </p>
        </div>
        <span className="shrink-0 rounded-full border border-border bg-surface-muted px-3 py-1.5 font-mono text-[11px] text-muted-foreground">
          {selected.length} / {POLICY_OPTIONS.length} selected
        </span>
      </div>

      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        {POLICY_OPTIONS.map((option) => {
          const isSelected = selected.includes(option.id);
          return (
            <button
              key={option.id}
              type="button"
              aria-pressed={isSelected}
              onClick={() => onToggle(option.id)}
              className={
                isSelected
                  ? "rounded-2xl border border-primary/50 bg-accent/60 p-5 text-left shadow-[var(--shadow-soft)] ring-4 ring-primary/10 transition-all"
                  : "rounded-2xl border border-border bg-surface p-5 text-left transition-all hover:border-border-strong hover:shadow-[var(--shadow-soft)]"
              }
            >
              <div className="grid grid-cols-[minmax(0,1fr)_auto] items-start gap-3">
                <div className="min-w-0">
                  <p className="text-[13px] text-muted-foreground">
                    {option.insurer}
                  </p>
                  <p className="mt-0.5 truncate text-[16px] font-semibold text-navy">
                    {option.product}
                  </p>
                </div>
                <span
                  className={
                    isSelected
                      ? "brand-gradient grid size-6 shrink-0 place-items-center rounded-full text-[12px] font-semibold text-primary-foreground"
                      : "size-6 shrink-0 rounded-full border border-border-strong"
                  }
                >
                  {isSelected ? "✓" : ""}
                </span>
              </div>

              <div className="mt-5 flex items-center gap-2">
                <span
                  className={
                    option.sourceDocumentAvailable
                      ? "size-1.5 rounded-full bg-verified"
                      : "size-1.5 rounded-full bg-review"
                  }
                />
                <span className="text-[12px] text-muted-foreground">
                  {option.sourceDocumentAvailable
                    ? "Source document available"
                    : "Source document not indexed"}
                </span>
              </div>
            </button>
          );
        })}
      </div>
    </section>
  );
}
