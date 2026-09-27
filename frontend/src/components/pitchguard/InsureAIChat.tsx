import {
  useEffect,
  useRef,
  useState,
} from "react";

import {
  askInsureAI,
  type ChatResponse,
} from "@/lib/pitchguard-api";


interface ChatMessage {
  id: number;
  role: "user" | "assistant";
  text: string;
  result?: ChatResponse;
}


export function InsureAIChat() {
  const [isOpen, setIsOpen] =
    useState(false);

  const [question, setQuestion] =
    useState("");

  const [isLoading, setIsLoading] =
    useState(false);

  const [error, setError] =
    useState<string | null>(null);

  const [messages, setMessages] =
    useState<ChatMessage[]>([
      {
        id: 1,
        role: "assistant",
        text:
          "Ask me about coverage, benefits, exclusions, waiting periods, ambulance cover, hospitalisation, or other facts contained in the available policy documents.",
      },
    ]);

  const messageIdRef =
    useRef(2);

  const bottomRef =
    useRef<HTMLDivElement | null>(
      null,
    );


  useEffect(() => {
    if (isOpen) {
      bottomRef.current?.scrollIntoView({
        behavior: "smooth",
      });
    }
  }, [
    messages,
    isLoading,
    isOpen,
  ]);


  async function handleSend() {
    const cleaned =
      question.trim();

    if (!cleaned || isLoading) {
      return;
    }

    const userMessage: ChatMessage = {
      id: messageIdRef.current++,
      role: "user",
      text: cleaned,
    };

    setMessages((current) => [
      ...current,
      userMessage,
    ]);

    setQuestion("");
    setError(null);
    setIsLoading(true);

    try {
      const result =
        await askInsureAI(
          cleaned,
        );

      const assistantMessage:
        ChatMessage = {
          id: messageIdRef.current++,
          role: "assistant",
          text: result.answer,
          result,
        };

      setMessages((current) => [
        ...current,
        assistantMessage,
      ]);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Something went wrong while contacting INSUREAI.",
      );
    } finally {
      setIsLoading(false);
    }
  }


  function handleKeyDown(
    event:
      React.KeyboardEvent<HTMLTextAreaElement>,
  ) {
    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {
      event.preventDefault();
      void handleSend();
    }
  }


  return (
    <>
      {/* ====================================================
          FLOATING LAUNCH BUTTON
          ==================================================== */}

      {!isOpen && (
        <button
          type="button"
          onClick={() =>
            setIsOpen(true)
          }
          className="fixed bottom-6 right-6 z-50 flex items-center gap-3 rounded-2xl border border-white/20 bg-navy px-5 py-3.5 text-left text-white shadow-[0_20px_60px_-20px_rgba(20,45,100,0.65)] transition hover:-translate-y-0.5 hover:shadow-[0_24px_70px_-20px_rgba(20,45,100,0.75)]"
          aria-label="Open INSUREAI assistant"
        >
          <span className="brand-gradient grid size-9 place-items-center rounded-xl border border-white/15 font-mono text-[11px] font-semibold text-white">
            AI
          </span>

          <span>
            <span className="block text-[13px] font-semibold">
              Ask INSUREAI
            </span>

            <span className="block text-[10px] text-white/65">
              Evidence-grounded assistant
            </span>
          </span>
        </button>
      )}


      {/* ====================================================
          CHAT PANEL
          ==================================================== */}

      {isOpen && (
        <aside className="fixed bottom-5 right-5 z-50 flex h-[min(680px,calc(100vh-40px))] w-[min(420px,calc(100vw-40px))] flex-col overflow-hidden rounded-3xl border border-border bg-surface shadow-[0_30px_90px_-28px_rgba(20,45,100,0.55)]">

          {/* Header */}

          <div className="relative overflow-hidden border-b border-border bg-navy px-5 py-4 text-white">
            <div className="glow-orb pointer-events-none absolute -right-16 -top-20 size-52 opacity-40" />

            <div className="relative flex items-start justify-between gap-4">
              <div className="flex items-center gap-3">
                <span className="brand-gradient grid size-10 shrink-0 place-items-center rounded-xl border border-white/15 font-mono text-[11px] font-semibold">
                  AI
                </span>

                <div>
                  <p className="text-[15px] font-semibold">
                    INSUREAI Assistant
                  </p>

                  <p className="mt-0.5 text-[11px] text-white/65">
                    Grounded in supplied policy evidence
                  </p>
                </div>
              </div>

              <button
                type="button"
                onClick={() =>
                  setIsOpen(false)
                }
                className="grid size-8 shrink-0 place-items-center rounded-lg border border-white/10 bg-white/5 text-lg text-white/70 transition hover:bg-white/10 hover:text-white"
                aria-label="Close assistant"
              >
                ×
              </button>
            </div>
          </div>


          {/* Guardrail notice */}

          <div className="border-b border-border bg-accent/40 px-5 py-3">
            <div className="flex gap-2.5">
              <span className="mt-1 size-1.5 shrink-0 rounded-full bg-primary" />

              <p className="text-[11px] leading-relaxed text-muted-foreground">
                Answers are restricted to the available
                insurance-policy documents. When sufficient
                evidence is unavailable, INSUREAI will abstain
                rather than invent policy facts.
              </p>
            </div>
          </div>


          {/* Messages */}

          <div className="flex-1 space-y-4 overflow-y-auto bg-surface-muted/35 px-4 py-5">
            {messages.map(
              (message) => (
                <div
                  key={message.id}
                  className={
                    message.role ===
                    "user"
                      ? "flex justify-end"
                      : "flex justify-start"
                  }
                >
                  <div
                    className={
                      message.role ===
                      "user"
                        ? "max-w-[85%] rounded-2xl rounded-br-md bg-navy px-4 py-3 text-[13px] leading-relaxed text-white shadow-[var(--shadow-soft)]"
                        : "max-w-[92%] rounded-2xl rounded-bl-md border border-border bg-surface px-4 py-3 text-[13px] leading-relaxed text-foreground shadow-[var(--shadow-soft)]"
                    }
                  >
                    <p>
                      {message.text}
                    </p>

                    {message.role ===
                      "assistant" &&
                      message.result && (
                        <AssistantEvidence
                          result={
                            message.result
                          }
                        />
                      )}
                  </div>
                </div>
              ),
            )}


            {isLoading && (
              <div className="flex justify-start">
                <div className="rounded-2xl rounded-bl-md border border-border bg-surface px-4 py-3 shadow-[var(--shadow-soft)]">
                  <div className="flex items-center gap-2">
                    <span className="size-1.5 animate-pulse rounded-full bg-primary" />
                    <span className="size-1.5 animate-pulse rounded-full bg-primary [animation-delay:150ms]" />
                    <span className="size-1.5 animate-pulse rounded-full bg-primary [animation-delay:300ms]" />

                    <span className="ml-1 text-[11px] text-muted-foreground">
                      Retrieving evidence...
                    </span>
                  </div>
                </div>
              </div>
            )}

            <div
              ref={bottomRef}
            />
          </div>


          {/* Error */}

          {error && (
            <div className="border-t border-contradicted/20 bg-contradicted-soft px-4 py-3 text-[11px] text-contradicted">
              {error}
            </div>
          )}


          {/* Input */}

          <div className="border-t border-border bg-surface p-4">
            <div className="rounded-2xl border border-border bg-surface shadow-[var(--shadow-soft)] transition focus-within:border-primary/50 focus-within:ring-4 focus-within:ring-primary/10">
              <textarea
                value={question}
                onChange={(event) =>
                  setQuestion(
                    event.target.value,
                  )
                }
                onKeyDown={
                  handleKeyDown
                }
                rows={2}
                maxLength={1000}
                placeholder="Ask about policy coverage..."
                className="block w-full resize-none bg-transparent px-4 pt-3 text-[13px] text-foreground outline-none placeholder:text-muted-foreground/70"
              />

              <div className="flex items-center justify-between px-3 pb-3">
                <span className="font-mono text-[9px] uppercase tracking-wide text-muted-foreground">
                  Evidence only
                </span>

                <button
                  type="button"
                  onClick={() =>
                    void handleSend()
                  }
                  disabled={
                    isLoading ||
                    !question.trim()
                  }
                  className="brand-gradient rounded-lg px-3.5 py-2 text-[12px] font-semibold text-primary-foreground transition-opacity hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {isLoading
                    ? "Checking..."
                    : "Ask →"}
                </button>
              </div>
            </div>

            <p className="mt-2 text-center text-[9px] leading-relaxed text-muted-foreground">
              AI-generated responses require advisor review.
            </p>
          </div>
        </aside>
      )}
    </>
  );
}


function AssistantEvidence({
  result,
}: {
  result: ChatResponse;
}) {
  const uniqueSources =
    result.sources.filter(
      (
        source,
        index,
        all,
      ) =>
        all.findIndex(
          (candidate) =>
            candidate.file ===
              source.file &&
            candidate.page ===
              source.page,
        ) === index,
    );


  return (
    <div className="mt-3 border-t border-border pt-3">
      <div className="flex items-center gap-2">
        <span
          className={
            result.supported
              ? "rounded-full bg-verified-soft px-2 py-1 font-mono text-[9px] font-semibold uppercase tracking-wide text-verified"
              : "rounded-full bg-review-soft px-2 py-1 font-mono text-[9px] font-semibold uppercase tracking-wide text-review"
          }
        >
          {result.supported
            ? "Evidence grounded"
            : "Insufficient evidence"}
        </span>
      </div>


      {result.claims.length >
        0 && (
        <div className="mt-3 space-y-2">
          {result.claims.map(
            (claim, index) => (
              <div
                key={`${claim.file}-${claim.page}-${index}`}
                className="rounded-xl bg-surface-muted px-3 py-2.5"
              >
                <p className="text-[11px] leading-relaxed text-secondary-foreground">
                  {claim.claim}
                </p>

                <p className="mt-1.5 font-mono text-[9px] text-muted-foreground">
                  {claim.file} ·
                  Page {claim.page}
                </p>
              </div>
            ),
          )}
        </div>
      )}


      {uniqueSources.length >
        0 && (
        <details className="mt-3">
          <summary className="cursor-pointer text-[10px] font-medium text-primary">
            View retrieved sources (
            {uniqueSources.length})
          </summary>

          <div className="mt-2 space-y-1.5">
            {uniqueSources.map(
              (source) => (
                <div
                  key={`${source.file}-${source.page}`}
                  className="rounded-lg border border-border bg-surface-muted/60 px-2.5 py-2"
                >
                  <p className="text-[10px] text-secondary-foreground">
                    {source.file}
                  </p>

                  <p className="mt-0.5 font-mono text-[9px] text-muted-foreground">
                    Page {source.page}
                  </p>
                </div>
              ),
            )}
          </div>
        </details>
      )}
    </div>
  );
}