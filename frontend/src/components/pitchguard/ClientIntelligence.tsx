import type { PitchResult } from "@/lib/pitchguard";

export function ClientIntelligenceSection({ result }: { result: PitchResult }) {
  const { intelligence, recommendation } = result;

  return (
    <div className="space-y-6">
      <section className="surface-card p-7 rise">
        <h2 className="text-[22px] font-semibold tracking-tight text-navy">
          Client intelligence
        </h2>
        <p className="mt-1.5 text-[14px] text-muted-foreground">
          Context used to shape the pitch. Everything here is supplied by the
          backend and reviewable by the advisor.
        </p>

        <div className="mt-7 grid gap-6 lg:grid-cols-3">
          <div className="rounded-2xl border border-border bg-surface-muted/60 p-5">
            <p className="text-[13px] text-muted-foreground">Industry</p>
            <p className="mt-1.5 text-[16px] font-medium text-navy">
              {intelligence.industry}
            </p>
          </div>
          <div className="rounded-2xl border border-border bg-surface-muted/60 p-5">
            <p className="text-[13px] text-muted-foreground">Company size</p>
            <p className="mt-1.5 text-[16px] font-medium text-navy">
              {intelligence.companySize}
            </p>
          </div>
          <div className="rounded-2xl border border-border bg-surface-muted/60 p-5">
            <p className="text-[13px] text-muted-foreground">Client</p>
            <p className="mt-1.5 truncate text-[16px] font-medium text-navy">
              {intelligence.company}
            </p>
          </div>
        </div>

        <div className="mt-6 grid gap-6 lg:grid-cols-2">
          <div>
            <h3 className="text-[15px] font-semibold text-navy">
              Key business &amp; workforce exposures
            </h3>
            <ul className="mt-3 space-y-2.5">
              {intelligence.exposures.map((exposure) => (
                <li
                  key={exposure}
                  className="flex items-start gap-3 rounded-xl border border-border bg-surface p-4 text-[14px] text-secondary-foreground"
                >
                  <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-primary" />
                  <span className="min-w-0">{exposure}</span>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className="text-[15px] font-semibold text-review">
              Assumptions — advisor to confirm
            </h3>
            <ul className="mt-3 space-y-2.5">
              {intelligence.assumptions.map((assumption) => (
                <li
                  key={assumption}
                  className="flex items-start gap-3 rounded-xl border border-review/25 bg-review-soft/60 p-4 text-[14px] text-secondary-foreground"
                >
                  <span className="mt-0.5 shrink-0 font-mono text-[12px] text-review">
                    ⚠
                  </span>
                  <span className="min-w-0">{assumption}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      <section className="relative overflow-hidden rounded-3xl border border-border bg-surface p-7 shadow-[var(--shadow-lift)] rise">
        <div className="glow-orb pointer-events-none absolute -right-20 -top-24 size-72 opacity-45" />
        <div className="relative">
          <div className="grid grid-cols-[minmax(0,1fr)_auto] items-start gap-4">
            <div className="min-w-0">
              <p className="font-mono text-[11px] tracking-wide text-primary">
                RECOMMENDED SOLUTION
              </p>
              <h2 className="mt-2 text-[26px] font-semibold leading-tight tracking-tight text-navy">
                {recommendation.policyLabel}
              </h2>
            </div>
            <span className="brand-gradient shrink-0 rounded-full px-3.5 py-1.5 text-[12px] font-semibold text-primary-foreground">
              Primary
            </span>
          </div>

          <p className="mt-4 max-w-3xl text-[15px] leading-relaxed text-secondary-foreground">
            {recommendation.reasoning}
          </p>

          <h3 className="mt-8 text-[15px] font-semibold text-navy">
            Client need → verified policy benefit
          </h3>
          <div className="mt-3 space-y-3">
            {recommendation.mapping.map((item, index) => (
              <div
                key={`${item.policyId}-${index}`}
                className="grid gap-3 rounded-2xl border border-border bg-surface-muted/50 p-5 lg:grid-cols-[minmax(0,1fr)_auto_minmax(0,1.2fr)] lg:items-center"
              >
                <p className="min-w-0 text-[14px] font-medium text-navy">
                  {item.need}
                </p>
                <span className="hidden font-mono text-[13px] text-primary lg:block">
                  →
                </span>
                <div className="min-w-0">
                  <p className="text-[14px] text-secondary-foreground">
                    {item.benefit}
                  </p>
                  <span
                    className={
                      item.verified
                        ? "mt-2 inline-block rounded-full bg-verified-soft px-2.5 py-0.5 font-mono text-[10px] font-semibold text-verified"
                        : "mt-2 inline-block rounded-full bg-review-soft px-2.5 py-0.5 font-mono text-[10px] font-semibold text-review"
                    }
                  >
                    {item.verified ? "✓ VERIFIED BENEFIT" : "⚠ UNVERIFIED"}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
