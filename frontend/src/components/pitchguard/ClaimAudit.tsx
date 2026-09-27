import { formatPercent, statusLabel, type AuditedClaim, type PitchResult } from "@/lib/pitchguard";

function statusClasses(status: AuditedClaim["status"]) {
  if (status === "VERIFIED") return "bg-verified-soft text-verified";
  if (status === "REVIEW") return "bg-review-soft text-review";
  return "bg-contradicted-soft text-contradicted";
}

function MetricCard({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone: "navy" | "verified" | "review" | "contradicted";
}) {
  const valueClass =
    tone === "verified"
      ? "text-verified"
      : tone === "review"
        ? "text-review"
        : tone === "contradicted"
          ? "text-contradicted"
          : "text-navy";
  return (
    <div className="rounded-2xl border border-border bg-surface p-5 shadow-[var(--shadow-soft)]">
      <p className="text-[13px] text-muted-foreground">{label}</p>
      <p className={`tnum mt-2 text-[30px] font-semibold leading-none ${valueClass}`}>
        {value}
      </p>
    </div>
  );
}

function EvidenceInspector({ claim }: { claim: AuditedClaim }) {
  return (
    <div className="mt-4 rounded-2xl border border-border bg-surface-muted/50 p-5 rise">
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-2xl border border-border bg-surface p-5">
          <p className="font-mono text-[11px] tracking-wide text-primary">
            AI GENERATED CLAIM
          </p>
          <p className="mt-3 text-[14px] leading-relaxed text-secondary-foreground">
            {claim.claim}
          </p>
        </div>
        <div className="rounded-2xl border border-border bg-surface p-5">
          <p className="font-mono text-[11px] tracking-wide text-cyan">
            SOURCE EVIDENCE
          </p>
          <p className="mt-3 text-[14px] leading-relaxed text-secondary-foreground">
            {claim.evidence.retrievedPassage}
          </p>
        </div>
      </div>

      <div className="mt-4 grid gap-4 sm:grid-cols-3">
        <div className="rounded-xl border border-border bg-surface p-4">
          <p className="text-[12px] text-muted-foreground">Policy</p>
          <p className="mt-1 truncate text-[14px] font-medium text-navy">
            {claim.evidence.policyLabel}
          </p>
        </div>
        <div className="rounded-xl border border-border bg-surface p-4">
          <p className="text-[12px] text-muted-foreground">Page</p>
          <p className="tnum mt-1 font-mono text-[14px] text-navy">
            {claim.evidence.page}
          </p>
        </div>
        <div className="rounded-xl border border-border bg-surface p-4">
          <p className="text-[12px] text-muted-foreground">Retrieval similarity</p>
          <div className="mt-2 flex items-center gap-2.5">
            <div className="h-1.5 min-w-0 flex-1 overflow-hidden rounded-full bg-surface-muted">
              <div
                className="brand-gradient h-full rounded-full"
                style={{ width: formatPercent(claim.evidence.semanticMatch) }}
              />
            </div>
            <span className="tnum shrink-0 font-mono text-[13px] text-navy">
              {formatPercent(claim.evidence.semanticMatch)}
            </span>
          </div>
        </div>
      </div>

      <div className="mt-4">
        <p className="text-[13px] font-semibold text-navy">
          Numeric validation
        </p>
        <div className="mt-2.5 space-y-2.5">
          {claim.evidence.numericValidation.map((item) => (
            <div
              key={item.label}
              className={
                item.matches
                  ? "grid gap-3 rounded-xl border border-border bg-surface p-4 sm:grid-cols-[minmax(0,1fr)_auto_auto] sm:items-center"
                  : "grid gap-3 rounded-xl border border-contradicted/40 bg-contradicted-soft/70 p-4 sm:grid-cols-[minmax(0,1fr)_auto_auto] sm:items-center"
              }
            >
              <p className="min-w-0 text-[13px] text-secondary-foreground">
                {item.label}
              </p>
              <span
                className={
                  item.matches
                    ? "tnum shrink-0 font-mono text-[14px] text-navy"
                    : "tnum shrink-0 rounded-md bg-contradicted/15 px-2 py-0.5 font-mono text-[14px] font-semibold text-contradicted line-through"
                }
              >
                {item.claimedValue}
              </span>
              <span className="tnum shrink-0 font-mono text-[14px] text-verified">
                {item.sourceValue}
              </span>
            </div>
          ))}
        </div>
        <p className="mt-2.5 text-[12px] text-muted-foreground">
          Left value is the generated claim, right value is the source document.
          Mismatches are highlighted.
        </p>
      </div>
    </div>
  );
}

interface ClaimAuditProps {
  result: PitchResult;
  expandedClaimId: string | null;
  onToggleClaim: (id: string) => void;
}

export function ClaimAuditSection({
  result,
  expandedClaimId,
  onToggleClaim,
}: ClaimAuditProps) {
  const { audit, claims } = result;
  const unsupported = audit.contradicted + audit.needsReview;

  return (
    <section className="rounded-3xl border border-border bg-surface p-7 shadow-[var(--shadow-lift)] rise">
      <div className="grid grid-cols-[minmax(0,1fr)_auto] items-start gap-4">
        <div className="min-w-0">
          <p className="font-mono text-[11px] tracking-wide text-primary">
            AI CLAIM AUDIT
          </p>
          <h2 className="mt-2 text-[26px] font-semibold tracking-tight text-navy">
            Every claim traced to its source
          </h2>
        </div>
        <span className="tnum shrink-0 rounded-full border border-border bg-surface-muted px-3 py-1.5 font-mono text-[11px] text-muted-foreground">
          {audit.totalClaims} claims audited
        </span>
      </div>

      <div className="mt-7 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          label="Verified claims"
          value={String(audit.verified)}
          tone="verified"
        />
        <MetricCard
          label="Needs review"
          value={String(audit.needsReview)}
          tone="review"
        />
        <MetricCard
          label="Contradicted"
          value={String(audit.contradicted)}
          tone="contradicted"
        />
        <MetricCard
          label="Verification rate"
          value={formatPercent(audit.confidenceScore)}
          tone="navy"
        />
      </div>

      {unsupported > 0 && (
        <div className="mt-6 flex items-start gap-3 rounded-2xl border border-review/30 bg-review-soft/60 p-5">
          <span className="mt-0.5 shrink-0 font-mono text-[13px] text-review">
            ⚠
          </span>
          <p className="min-w-0 text-[14px] text-secondary-foreground">
            <span className="font-semibold text-navy">
              Advisor review required before client release.
            </span>{" "}
            {unsupported} claim{unsupported === 1 ? "" : "s"} are not fully
            supported by source evidence.
          </p>
        </div>
      )}

      <div className="mt-6 space-y-3">
        {claims.map((claim) => {
          const isOpen = expandedClaimId === claim.id;
          return (
            <div
              key={claim.id}
              className={
                isOpen
                  ? "rounded-2xl border border-primary/40 bg-surface p-5 shadow-[var(--shadow-soft)] ring-4 ring-primary/10"
                  : "rounded-2xl border border-border bg-surface p-5 transition-colors hover:border-border-strong"
              }
            >
              <button
                type="button"
                onClick={() => onToggleClaim(claim.id)}
                aria-expanded={isOpen}
                className="grid w-full grid-cols-[minmax(0,1fr)_auto] items-center gap-4 text-left"
              >
                <div className="min-w-0">
                  <p className="text-[15px] font-medium text-navy">
                    {claim.claim}
                  </p>
                  <p className="mt-1.5 truncate text-[13px] text-muted-foreground">
                    {claim.policyLabel} · page {claim.evidence.page} ·
                    retrieval match{" "}
                    <span className="tnum font-mono">
                      {formatPercent(claim.confidence)}
                    </span>
                  </p>
                </div>
                <div className="flex shrink-0 items-center gap-3">
                  <span
                    className={`rounded-full px-3 py-1 font-mono text-[10px] font-semibold ${statusClasses(claim.status)}`}
                  >
                    {statusLabel(claim.status)}
                  </span>
                  <span className="font-mono text-[12px] text-muted-foreground">
                    {isOpen ? "−" : "+"}
                  </span>
                </div>
              </button>

              {isOpen && <EvidenceInspector claim={claim} />}
            </div>
          );
        })}
      </div>
    </section>
  );
}
