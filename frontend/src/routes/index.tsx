import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";

import { AdvisorReviewSection } from "@/components/pitchguard/AdvisorReview";
import { ClaimAuditSection } from "@/components/pitchguard/ClaimAudit";
import { ClientIntelligenceSection } from "@/components/pitchguard/ClientIntelligence";
import { HeroWorkspace } from "@/components/pitchguard/HeroWorkspace";
import { InsureAIChat } from "@/components/pitchguard/InsureAIChat";
import { PolicySelector } from "@/components/pitchguard/PolicySelector";
import { StageRail } from "@/components/pitchguard/StageRail";
import {
  EmptyState,
  ErrorState,
  GeneratingState,
  PlaceholderNotice,
} from "@/components/pitchguard/States";
import { TopNav } from "@/components/pitchguard/TopNav";

import {
  downloadAuditReport,
  downloadPitchPptx,
  generatePitch,
  revisePitch,
  submitAdvisorDecision,
} from "@/lib/pitchguard-api";

import type {
  AdvisorDecision,
  PitchResult,
} from "@/lib/pitchguard";

import { CompanySections } from "@/components/pitchguard/CompanySections";

export const Route = createFileRoute("/")({
  component: Index,
});


function Index() {
  // =========================================================
  // CLIENT INPUT
  // =========================================================

  const [companyName, setCompanyName] = useState("");
  const [priorities, setPriorities] = useState("");

  // =========================================================
  // POLICY SELECTION
  // =========================================================

  const [selectedPolicies, setSelectedPolicies] = useState<string[]>([]);

  // =========================================================
  // WORKFLOW STATE
  // =========================================================

  const [result, setResult] = useState<PitchResult | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationError, setGenerationError] = useState<string | null>(null);

  // =========================================================
  // AUDIT UI STATE
  // =========================================================

  const [expandedClaimId, setExpandedClaimId] = useState<string | null>(null);

  // =========================================================
  // ADVISOR REVIEW
  // =========================================================

  const [decision, setDecision] = useState<AdvisorDecision | null>(null);

  // =========================================================
  // EXPORT STATE
  // =========================================================

  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);


  // =========================================================
  // WORKFLOW STAGE
  // =========================================================

  const activeStage = useMemo(() => {
    if (result) return 4;
    if (isGenerating) return 3;
    if (selectedPolicies.length > 0) return 2;

    return 1;
  }, [
    isGenerating,
    result,
    selectedPolicies.length,
  ]);


  // =========================================================
  // POLICY SELECTION
  // =========================================================

  function togglePolicy(id: string) {
    setSelectedPolicies((current) =>
      current.includes(id)
        ? current.filter(
            (policyId) => policyId !== id,
          )
        : [...current, id],
    );
  }


  // =========================================================
  // GENERATE PITCH
  // =========================================================

  async function handleGenerate() {
    setGenerationError(null);
    setDownloadError(null);

    if (!companyName.trim()) {
      setGenerationError(
        "Enter a client company name before generating the pitch.",
      );
      return;
    }

    if (selectedPolicies.length === 0) {
      setGenerationError(
        "Select at least one of the four supplied medical policies to compare.",
      );
      return;
    }

    setDecision(null);
    setResult(null);
    setExpandedClaimId(null);
    setIsGenerating(true);

    try {
      const priorityList = priorities
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean);

      const next = await generatePitch({
        companyName: companyName.trim(),
        priorities: priorityList,
        policyIds: selectedPolicies,
      });

      setResult(next);

      setExpandedClaimId(
        next.claims[0]?.id ?? null,
      );
    } catch (error) {
      setGenerationError(
        error instanceof Error
          ? error.message
          : "Pitch generation failed.",
      );
    } finally {
      setIsGenerating(false);
    }
  }


  // =========================================================
  // ADVISOR DECISION
  // =========================================================

  async function handleDecision(
    nextDecision: AdvisorDecision,
  ) {
    setDecision(nextDecision);
    setDownloadError(null);

    try {
      await submitAdvisorDecision(
        nextDecision,
      );
    } catch (error) {
      setDownloadError(
        error instanceof Error
          ? error.message
          : "Could not save advisor decision.",
      );
    }
  }


  // =========================================================
  // EXPORT
  // =========================================================

  async function runDownload(
    action: () => Promise<unknown>,
  ) {
    setIsDownloading(true);
    setDownloadError(null);

    try {
      await action();
    } catch (error) {
      setDownloadError(
        error instanceof Error
          ? error.message
          : "Download is not available yet.",
      );
    } finally {
      setIsDownloading(false);
    }
  }


  // =========================================================
  // UI
  // =========================================================

  return (
    <div className="min-h-screen bg-background text-foreground">
      <TopNav />

      <main
        id="workspace"
        className="mx-auto max-w-[1400px] space-y-6 px-5 py-7 sm:px-6 lg:py-9"
      >

        {/* -------------------------------------------------- */}
        {/* CLIENT INPUT */}
        {/* -------------------------------------------------- */}

        <HeroWorkspace
          companyName={companyName}
          priorities={priorities}
          onCompanyNameChange={setCompanyName}
          onPrioritiesChange={setPriorities}
          onGenerate={handleGenerate}
          isGenerating={isGenerating}
        />


        {/* -------------------------------------------------- */}
        {/* WORKFLOW PROGRESS */}
        {/* -------------------------------------------------- */}

        <StageRail
          activeStage={activeStage}
        />


        {/* -------------------------------------------------- */}
        {/* FOUR CASE-STUDY POLICIES */}
        {/* -------------------------------------------------- */}

        <PolicySelector
          selected={selectedPolicies}
          onToggle={togglePolicy}
        />


        {/* -------------------------------------------------- */}
        {/* GENERATION STATE */}
        {/* -------------------------------------------------- */}

        {isGenerating && (
          <GeneratingState />
        )}


        {/* -------------------------------------------------- */}
        {/* ERROR STATE */}
        {/* -------------------------------------------------- */}

        {!isGenerating &&
          generationError && (
            <ErrorState
              message={generationError}
              onRetry={handleGenerate}
            />
          )}


        {/* -------------------------------------------------- */}
        {/* EMPTY STATE */}
        {/* -------------------------------------------------- */}

        {!isGenerating &&
          !generationError &&
          !result && (
            <EmptyState />
          )}


        {/* -------------------------------------------------- */}
        {/* GENERATED RESULT */}
        {/* -------------------------------------------------- */}

        {!isGenerating &&
          result && (
            <>
              {result.isPlaceholderData && (
                <PlaceholderNotice />
              )}

              {/* Researched company intelligence */}
              <ClientIntelligenceSection
                result={result}
              />

              {/* Independent claim audit */}
              <ClaimAuditSection
                result={result}
                expandedClaimId={
                  expandedClaimId
                }
                onToggleClaim={(id) =>
                  setExpandedClaimId(
                    (current) =>
                      current === id
                        ? null
                        : id,
                  )
                }
              />

              {/* Human-in-the-loop approval */}
              <AdvisorReviewSection
                decision={decision}
                onDecision={handleDecision}
                onRevise={revisePitch}
                onRevisionComplete={(revisedResult) => {
                  setResult(revisedResult);

                  setDecision(null);

                  setExpandedClaimId(
                    revisedResult.claims[0]?.id ??
                      null,
                  );

                  setDownloadError(null);
                }}
                onDownloadPitch={() =>
                  runDownload(downloadPitchPptx)
                }
                onDownloadAudit={() =>
                  runDownload(downloadAuditReport)
                }
                downloadError={downloadError}
                isDownloading={isDownloading}
              />
            </>
          )}
        <CompanySections />
      </main>
<InsureAIChat />

      {/* ---------------------------------------------------- */}
      {/* FOOTER */}
      {/* ---------------------------------------------------- */}

      <footer className="border-t border-border bg-surface">
        <div className="mx-auto flex max-w-[1400px] flex-col gap-5 px-6 py-7 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-[14px] font-bold tracking-tight text-navy">
              INSUREAI
            </p>

            <p className="mt-1 text-[11px] text-muted-foreground">
              Evidence-backed insurance pitch intelligence
            </p>
          </div>

          <p className="max-w-2xl text-[10px] leading-5 text-muted-foreground sm:text-right">
            INSUREAI is a demonstration prototype. AI-generated recommendations
            and policy claims require source verification and professional advisor
            review before client use. Final policy selection remains with the client.
          </p>
        </div>
      </footer>
    </div>
  );
}