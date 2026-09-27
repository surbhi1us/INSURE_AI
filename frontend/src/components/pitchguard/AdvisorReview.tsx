import { useState } from "react";

import type {
  AdvisorDecision,
  PitchResult,
} from "@/lib/pitchguard";

interface AdvisorReviewProps {
  decision: AdvisorDecision | null;
  onDecision: (decision: AdvisorDecision) => void;

  onRevise: (
    instructions: string,
  ) => Promise<PitchResult>;

  onRevisionComplete: (
    result: PitchResult,
  ) => void;

  onDownloadPitch: () => void;
  onDownloadAudit: () => void;

  downloadError: string | null;
  isDownloading: boolean;
}

export function AdvisorReviewSection({
  decision,
  onDecision,
  onRevise,
  onRevisionComplete,
  onDownloadPitch,
  onDownloadAudit,
  downloadError,
  isDownloading,
}: AdvisorReviewProps) {
  const [instructions, setInstructions] =
    useState("");

  const [isRevising, setIsRevising] =
    useState(false);

  const [revisionError, setRevisionError] =
    useState<string | null>(null);

  async function handleRevision() {
    const cleaned =
      instructions.trim();

    if (!cleaned) {
      setRevisionError(
        "Enter revision instructions first.",
      );
      return;
    }

    setRevisionError(null);
    setIsRevising(true);

    try {
      const revised =
        await onRevise(cleaned);

      /*
       * Replace the current UI result with the newly
       * revised AND re-audited result.
       */
      onRevisionComplete(revised);

      /*
       * Clear the edit box because the revised pitch
       * now requires a fresh advisor decision.
       */
      setInstructions("");
    } catch (error) {
      setRevisionError(
        error instanceof Error
          ? error.message
          : "Pitch revision failed.",
      );
    } finally {
      setIsRevising(false);
    }
  }

  return (
    <section className="surface-card p-7 rise">
      <p className="font-mono text-[11px] tracking-wide text-primary">
        ADVISOR REVIEW
      </p>

      <h2 className="mt-2 text-[24px] font-semibold tracking-tight text-navy">
        AI verification is complete. Final client communication
        requires advisor approval.
      </h2>

      <p className="mt-2 max-w-3xl text-[14px] leading-relaxed text-muted-foreground">
        Approve the audited pitch, request an AI-assisted revision,
        or reject it and regenerate. Revised policy claims are
        independently audited again before approval.
      </p>

      <div className="mt-6 grid gap-3 sm:grid-cols-3">
        <button
          type="button"
          onClick={() =>
            onDecision("approved")
          }
          disabled={isRevising}
          className={
            decision === "approved"
              ? "rounded-xl border border-verified/50 bg-verified-soft px-4 py-3 text-[15px] font-semibold text-verified"
              : "rounded-xl border border-border bg-surface px-4 py-3 text-[15px] font-semibold text-navy transition-colors hover:border-verified/50 hover:bg-verified-soft/50 disabled:opacity-60"
          }
        >
          Approve Pitch
        </button>

        <button
          type="button"
          onClick={() =>
            onDecision("editing")
          }
          disabled={isRevising}
          className={
            decision === "editing"
              ? "rounded-xl border border-primary/50 bg-accent px-4 py-3 text-[15px] font-semibold text-accent-foreground"
              : "rounded-xl border border-border bg-surface px-4 py-3 text-[15px] font-semibold text-navy transition-colors hover:border-primary/40 hover:bg-accent/50 disabled:opacity-60"
          }
        >
          Edit Pitch
        </button>

        <button
          type="button"
          onClick={() =>
            onDecision("rejected")
          }
          disabled={isRevising}
          className={
            decision === "rejected"
              ? "rounded-xl border border-contradicted/50 bg-contradicted-soft px-4 py-3 text-[15px] font-semibold text-contradicted"
              : "rounded-xl border border-border bg-surface px-4 py-3 text-[15px] font-semibold text-navy transition-colors hover:border-contradicted/40 hover:bg-contradicted-soft/50 disabled:opacity-60"
          }
        >
          Reject / Regenerate
        </button>
      </div>

      {decision === "editing" && (
        <div className="mt-5 rounded-2xl border border-primary/20 bg-surface-muted/60 p-5">
          <label
            htmlFor="pitch-edits"
            className="block text-[14px] font-semibold text-navy"
          >
            Advisor revision instructions
          </label>

          <p className="mt-1 text-[12px] leading-relaxed text-muted-foreground">
            Describe what should change in the pitch. Any revised
            policy-specific factual claims will be checked again
            against the supplied policy documents.
          </p>

          <textarea
            id="pitch-edits"
            value={instructions}
            rows={5}
            maxLength={3000}
            disabled={isRevising}
            onChange={(event) => {
              setInstructions(
                event.target.value,
              );

              if (revisionError) {
                setRevisionError(null);
              }
            }}
            placeholder="Example: Make the executive summary shorter and make the recommendation explanation more client-friendly. Do not change unsupported policy facts."
            className="mt-4 w-full resize-y rounded-xl border border-border bg-surface px-4 py-3 text-[14px] text-foreground outline-none placeholder:text-muted-foreground/70 focus:border-primary/60 focus:ring-4 focus:ring-primary/10 disabled:opacity-60"
          />

          <div className="mt-2 flex items-center justify-between gap-4">
            <p className="text-[11px] text-muted-foreground">
              {instructions.length}/3000
            </p>

            <button
              type="button"
              onClick={handleRevision}
              disabled={
                isRevising ||
                !instructions.trim()
              }
              className="brand-gradient rounded-xl px-5 py-3 text-[14px] font-semibold text-primary-foreground shadow-[var(--shadow-soft)] transition-opacity hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isRevising
                ? "Revising & Re-auditing..."
                : "Save Changes & Re-audit"}
            </button>
          </div>

          {isRevising && (
            <p className="mt-4 rounded-xl border border-primary/20 bg-accent/50 px-4 py-3 text-[13px] text-secondary-foreground">
              Revising the pitch and independently checking the
              revised factual claims against the original policy
              documents...
            </p>
          )}

          {revisionError && (
            <p className="mt-4 rounded-xl border border-contradicted/30 bg-contradicted-soft/70 px-4 py-3 text-[13px] text-contradicted">
              {revisionError}
            </p>
          )}
        </div>
      )}

      {decision === "rejected" && (
        <p className="mt-5 rounded-2xl border border-contradicted/25 bg-contradicted-soft/60 p-5 text-[14px] text-secondary-foreground">
          Pitch rejected. Adjust the client information, priorities
          or policy selection and generate a new pitch.
        </p>
      )}

      {decision === "approved" && (
        <div className="mt-6 rounded-2xl border border-verified/30 bg-verified-soft/60 p-6">
          <div className="flex items-start gap-3">
            <span className="grid size-8 shrink-0 place-items-center rounded-full bg-verified/15 font-mono text-[14px] text-verified">
              ✓
            </span>

            <div className="min-w-0">
              <p className="text-[17px] font-semibold text-navy">
                Pitch approved for advisor use
              </p>

              <p className="mt-1 text-[14px] text-muted-foreground">
                Export the reviewed client presentation and its
                supporting audit trail.
              </p>
            </div>
          </div>

          <div className="mt-5 flex flex-col gap-3 sm:flex-row">
            <button
              type="button"
              onClick={onDownloadPitch}
              disabled={isDownloading}
              className="brand-gradient rounded-xl px-5 py-3 text-[15px] font-semibold text-primary-foreground shadow-[var(--shadow-soft)] transition-opacity hover:opacity-95 disabled:opacity-60"
            >
              {isDownloading
                ? "Preparing..."
                : "Download Client Pitch (.pptx)"}
            </button>

            <button
              type="button"
              onClick={onDownloadAudit}
              disabled={isDownloading}
              className="rounded-xl border border-border bg-surface px-5 py-3 text-[15px] font-semibold text-navy transition-colors hover:border-border-strong disabled:opacity-60"
            >
              Download Audit Report
            </button>
          </div>

          {downloadError && (
            <p className="mt-4 rounded-xl border border-contradicted/30 bg-contradicted-soft/70 px-4 py-3 text-[13px] text-contradicted">
              {downloadError}
            </p>
          )}
        </div>
      )}
    </section>
  );
}