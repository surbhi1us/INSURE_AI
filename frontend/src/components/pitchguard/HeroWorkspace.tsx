interface HeroWorkspaceProps {
  companyName: string;
  priorities: string;
  onCompanyNameChange: (value: string) => void;
  onPrioritiesChange: (value: string) => void;
  onGenerate: () => void;
  isGenerating: boolean;
}

function IntelligenceVisual() {
  return (
    <div className="relative mx-auto h-[370px] w-full max-w-[500px]">
      <div className="glow-orb absolute left-1/2 top-1/2 size-[360px] -translate-x-1/2 -translate-y-1/2 opacity-50" />

      <svg
        className="absolute inset-0 h-full w-full"
        viewBox="0 0 500 370"
        fill="none"
        aria-hidden="true"
      >
        <path
          d="M132 98 C205 98, 205 174, 286 174"
          stroke="var(--color-primary)"
          strokeOpacity="0.28"
          strokeWidth="1.5"
          strokeDasharray="5 6"
        />

        <path
          d="M135 278 C210 278, 210 195, 286 195"
          stroke="var(--color-cyan)"
          strokeOpacity="0.4"
          strokeWidth="1.5"
          strokeDasharray="5 6"
        />
      </svg>

      <div className="absolute left-0 top-10 w-[210px] rotate-[-3deg] rounded-2xl border border-border bg-surface p-5 shadow-[var(--shadow-soft)]">
        <div className="flex items-center gap-2">
          <div className="grid size-8 place-items-center rounded-lg bg-accent text-[13px]">
            01
          </div>

          <div>
            <p className="font-mono text-[9px] tracking-[0.12em] text-muted-foreground">
              SOURCE
            </p>
            <p className="text-[12px] font-semibold text-navy">
              Policy evidence
            </p>
          </div>
        </div>

        <div className="mt-4 space-y-2">
          <div className="h-1.5 w-full rounded-full bg-surface-muted" />
          <div className="h-1.5 w-[88%] rounded-full bg-surface-muted" />
          <div className="h-1.5 w-[65%] rounded-full bg-accent" />
        </div>

        <p className="mt-4 text-[10px] text-muted-foreground">
          Supplied policy documents
        </p>
      </div>

      <div className="absolute bottom-6 left-7 w-[200px] rotate-[2deg] rounded-2xl border border-border bg-surface p-5 shadow-[var(--shadow-soft)]">
        <div className="flex items-center gap-2">
          <div className="grid size-8 place-items-center rounded-lg bg-surface-muted text-[13px]">
            02
          </div>

          <div>
            <p className="font-mono text-[9px] tracking-[0.12em] text-muted-foreground">
              CONTEXT
            </p>
            <p className="text-[12px] font-semibold text-navy">
              Client intelligence
            </p>
          </div>
        </div>

        <div className="mt-4 space-y-2">
          <div className="h-1.5 w-[76%] rounded-full bg-surface-muted" />
          <div className="h-1.5 w-full rounded-full bg-surface-muted" />
          <div className="h-1.5 w-[70%] rounded-full bg-surface-muted" />
        </div>
      </div>

      <div className="absolute right-0 top-[105px] w-[245px] rounded-2xl border border-primary/15 bg-surface p-5 shadow-[var(--shadow-lift)]">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="font-mono text-[9px] tracking-[0.12em] text-muted-foreground">
              VERIFICATION
            </p>
            <p className="mt-1 text-[13px] font-semibold text-navy">
              Evidence-linked claim
            </p>
          </div>

          <span className="rounded-full bg-verified-soft px-2.5 py-1 text-[9px] font-bold text-verified">
            VERIFIED
          </span>
        </div>

        <div className="mt-5 space-y-2">
          <div className="h-1.5 w-full rounded-full bg-surface-muted" />
          <div className="h-1.5 w-[84%] rounded-full bg-surface-muted" />
          <div className="h-1.5 w-[62%] rounded-full bg-surface-muted" />
        </div>

        <div className="mt-5 flex items-center justify-between">
          <span className="text-[10px] text-muted-foreground">
            Evidence match
          </span>

          <span className="font-mono text-[10px] font-semibold text-primary">
            SOURCE LINKED
          </span>
        </div>

        <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-surface-muted">
          <div className="brand-gradient h-full w-[82%] rounded-full" />
        </div>
      </div>

      <div className="absolute right-8 top-2 rounded-full border border-border bg-surface px-3 py-2 shadow-[var(--shadow-soft)]">
        <span className="font-mono text-[9px] font-medium tracking-wide text-primary">
          HUMAN-IN-THE-LOOP
        </span>
      </div>
    </div>
  );
}

export function HeroWorkspace({
  companyName,
  priorities,
  onCompanyNameChange,
  onPrioritiesChange,
  onGenerate,
  isGenerating,
}: HeroWorkspaceProps) {
  return (
    <section
      id="workspace"
      className="hero-shell relative overflow-hidden rounded-[28px] border border-border bg-surface px-6 py-9 shadow-[var(--shadow-lift)] sm:px-9 sm:py-11 lg:px-12"
    >
      <div className="pointer-events-none absolute -left-40 -top-48 size-[600px] rounded-full bg-primary/5 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-48 right-0 size-[500px] rounded-full bg-cyan/5 blur-3xl" />

      <div className="relative grid gap-12 lg:grid-cols-[minmax(0,1.05fr)_minmax(420px,0.95fr)] lg:items-center">
        <div>
          <div className="inline-flex items-center gap-2 rounded-full border border-primary/15 bg-accent/70 px-3 py-1.5">
            <span className="relative flex size-2">
              <span className="absolute inline-flex size-full animate-ping rounded-full bg-verified opacity-30" />
              <span className="relative inline-flex size-2 rounded-full bg-verified" />
            </span>

            <span className="text-[11px] font-semibold tracking-wide text-accent-foreground">
              EVIDENCE-BACKED ADVISOR INTELLIGENCE
            </span>
          </div>

          <h1 className="mt-6 max-w-[680px] text-[38px] font-semibold leading-[1.06] tracking-[-0.04em] text-navy sm:text-[48px] lg:text-[52px]">
            From policy documents to a{" "}
            <span className="brand-text">
              client-ready recommendation.
            </span>
          </h1>

          <p className="mt-5 max-w-[620px] text-[15px] leading-7 text-muted-foreground sm:text-[16px]">
            INSUREAI combines client context with supplied policy evidence to
            build recommendations, audit factual claims, and keep the advisor
            in control of the final client communication.
          </p>

          <div className="mt-7 flex flex-wrap gap-x-6 gap-y-3">
            {[
              "Policy-grounded",
              "Claim-level audit",
              "Advisor approval",
            ].map((item) => (
              <div
                key={item}
                className="flex items-center gap-2 text-[12px] font-medium text-secondary-foreground"
              >
                <span className="grid size-5 place-items-center rounded-full bg-verified-soft text-[10px] font-bold text-verified">
                  ✓
                </span>
                {item}
              </div>
            ))}
          </div>

          <div className="mt-9 max-w-[650px] rounded-2xl border border-border bg-background/70 p-5 shadow-[var(--shadow-soft)] backdrop-blur">
            <div className="grid gap-5 sm:grid-cols-2">
              <div>
                <label
                  htmlFor="company-name"
                  className="mb-2 block text-[12px] font-semibold text-secondary-foreground"
                >
                  Client company
                  <span className="ml-1 text-primary">*</span>
                </label>

                <input
                  id="company-name"
                  type="text"
                  value={companyName}
                  maxLength={120}
                  onChange={(event) =>
                    onCompanyNameChange(event.target.value)
                  }
                  placeholder="Enter company name"
                  className="w-full rounded-xl border border-border bg-surface px-4 py-3 text-[14px] text-foreground shadow-sm outline-none transition focus:border-primary/60 focus:ring-4 focus:ring-primary/10"
                />
              </div>

              <div>
                <label
                  htmlFor="client-priorities"
                  className="mb-2 block text-[12px] font-semibold text-secondary-foreground"
                >
                  Client priorities
                  <span className="ml-1 font-normal text-muted-foreground">
                    optional
                  </span>
                </label>

                <input
                  id="client-priorities"
                  type="text"
                  value={priorities}
                  maxLength={400}
                  onChange={(event) =>
                    onPrioritiesChange(event.target.value)
                  }
                  placeholder="Hospitalisation, employee cover..."
                  className="w-full rounded-xl border border-border bg-surface px-4 py-3 text-[14px] text-foreground shadow-sm outline-none transition focus:border-primary/60 focus:ring-4 focus:ring-primary/10"
                />
              </div>
            </div>

            <div className="mt-5 flex flex-col gap-4 border-t border-border pt-5 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-[12px] font-medium text-secondary-foreground">
                  Ready to analyse
                </p>

                <p className="mt-1 max-w-md text-[11px] leading-relaxed text-muted-foreground">
                  Policy facts remain grounded in the supplied source
                  documents. Final recommendations require advisor review.
                </p>
              </div>

              <button
                type="button"
                onClick={onGenerate}
                disabled={isGenerating || !companyName.trim()}
                className="brand-gradient group shrink-0 rounded-xl px-6 py-3 text-[13px] font-semibold text-primary-foreground shadow-[var(--shadow-lift)] transition hover:-translate-y-0.5 hover:shadow-lg disabled:cursor-not-allowed disabled:translate-y-0 disabled:opacity-50"
              >
                {isGenerating ? (
                  "Analysing..."
                ) : (
                  <span className="flex items-center gap-2">
                    Generate pitch
                    <span className="transition-transform group-hover:translate-x-0.5">
                      →
                    </span>
                  </span>
                )}
              </button>
            </div>
          </div>
        </div>

        <div className="hidden lg:block">
          <IntelligenceVisual />
        </div>
      </div>
    </section>
  );
}