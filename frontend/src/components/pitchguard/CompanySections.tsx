export function CompanySections() {
  const workflow = [
    {
      number: "01",
      title: "Understand",
      text:
        "Build client context from researched company intelligence, business exposures and advisor-supplied priorities.",
    },
    {
      number: "02",
      title: "Compare",
      text:
        "Evaluate the supplied insurance policies against identified client needs and workforce context.",
    },
    {
      number: "03",
      title: "Verify",
      text:
        "Retrieve source evidence and independently audit factual policy claims before advisor use.",
    },
    {
      number: "04",
      title: "Review",
      text:
        "Keep the advisor in control through approval, revision, re-audit and client-ready export.",
    },
  ];

  const principles = [
    ["Evidence", "Source-linked policy claims"],
    ["Control", "Human approval before client use"],
    ["Traceability", "Claim-level audit trail"],
    ["Output", "Professional client-ready pitch"],
  ];

  return (
    <>
      {/* ====================================================
          HOW IT WORKS
          ==================================================== */}

      <section
        id="how-it-works"
        className="scroll-mt-24 py-12 sm:py-16"
      >
        <div className="mb-8 max-w-2xl">
          <p className="font-mono text-[10px] font-semibold tracking-[0.16em] text-primary">
            THE INSUREAI WORKFLOW
          </p>

          <h2 className="mt-3 text-[28px] font-semibold tracking-[-0.03em] text-navy sm:text-[34px]">
            From company context to evidence-backed advice.
          </h2>

          <p className="mt-3 text-[14px] leading-6 text-muted-foreground">
            INSUREAI combines company intelligence, policy-document
            retrieval, AI-assisted comparison and independent claim
            verification in one advisor-led workflow.
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {workflow.map((item) => (
            <article
              key={item.number}
              className="surface-card group relative overflow-hidden p-6 transition duration-300 hover:-translate-y-1 hover:shadow-[var(--shadow-lift)]"
            >
              <div className="absolute right-0 top-0 h-20 w-20 rounded-bl-[48px] bg-accent/50" />

              <span className="relative font-mono text-[11px] font-semibold text-primary">
                {item.number}
              </span>

              <h3 className="relative mt-6 text-[18px] font-semibold text-navy">
                {item.title}
              </h3>

              <p className="relative mt-2 text-[13px] leading-6 text-muted-foreground">
                {item.text}
              </p>
            </article>
          ))}
        </div>
      </section>

      {/* ====================================================
          ABOUT
          ==================================================== */}

      <section
        id="about"
        className="scroll-mt-24 overflow-hidden rounded-[30px] border border-border bg-navy px-7 py-10 text-primary-foreground shadow-[var(--shadow-lift)] sm:px-10 sm:py-12"
      >
        <div className="grid gap-10 lg:grid-cols-[1fr_0.85fr] lg:items-center">
          <div>
            <p className="font-mono text-[10px] font-semibold tracking-[0.16em] text-cyan">
              ABOUT INSUREAI
            </p>

            <h2 className="mt-4 max-w-xl text-[30px] font-semibold leading-tight tracking-[-0.03em] sm:text-[36px]">
              AI assistance without removing human accountability.
            </h2>

            <p className="mt-4 max-w-2xl text-[14px] leading-7 text-primary-foreground/70">
              INSUREAI is an academic advisor-support prototype for
              evidence-grounded insurance pitch preparation. It brings
              company research, policy comparison, recommendation
              generation and claim verification into a structured
              workflow.
            </p>

            <p className="mt-4 max-w-2xl text-[14px] leading-7 text-primary-foreground/70">
              The system supports the advisor rather than replacing
              professional judgement. Recommendations remain subject to
              advisor review, and final policy selection remains with the
              client.
            </p>
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            {principles.map(([title, text]) => (
              <div
                key={title}
                className="rounded-2xl border border-white/10 bg-white/5 p-5 transition hover:bg-white/[0.08]"
              >
                <div className="mb-4 h-1 w-8 rounded-full bg-cyan" />

                <p className="text-[12px] font-semibold text-cyan">
                  {title}
                </p>

                <p className="mt-2 text-[13px] leading-5 text-primary-foreground/75">
                  {text}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ====================================================
          PROJECT / TEAM
          ==================================================== */}

      <section
        id="team"
        className="scroll-mt-24 py-12 sm:py-16"
        >
        <div className="mb-7 max-w-2xl">
            <p className="font-mono text-[10px] font-semibold tracking-[0.16em] text-primary">
            OUR TEAM
            </p>

            <h2 className="mt-3 text-[28px] font-semibold tracking-[-0.03em] text-navy sm:text-[34px]">
            Built around insurance intelligence.
            </h2>

            <p className="mt-3 text-[13px] leading-6 text-muted-foreground">
            A demonstration team structure representing the disciplines behind
            INSUREAI's research, AI, verification and advisor experience.
            </p>
        </div>

        <div className="grid gap-6">

            {/* TEAM */}

            <div className="surface-card p-7 sm:p-8">
            <div className="grid gap-4 sm:grid-cols-2">

                {[
                {
                    initials: "AR",
                    name: "Aarav Rao",
                    role: "AI & Product Lead",
                    area: "Generative AI • Product Strategy",
                },
                {
                    initials: "MK",
                    name: "Meera Kapoor",
                    role: "Insurance Intelligence",
                    area: "Policy Research • Risk Analysis",
                },
                {
                    initials: "RS",
                    name: "Rohan Shah",
                    role: "AI Engineer",
                    area: "RAG • Retrieval • Verification",
                },
                {
                    initials: "AN",
                    name: "Anaya Nair",
                    role: "Experience & Advisory",
                    area: "Advisor Workflow • Client Experience",
                },
                ].map((member) => (
                <article
                    key={member.name}
                    className="rounded-2xl border border-border bg-surface-muted/40 p-5 transition duration-300 hover:-translate-y-1 hover:bg-surface hover:shadow-[var(--shadow-soft)]"
                >
                    <div className="flex items-center gap-4">
                    <div className="brand-gradient grid size-11 shrink-0 place-items-center rounded-xl text-[11px] font-bold text-primary-foreground">
                        {member.initials}
                    </div>

                    <div className="min-w-0">
                        <p className="text-[14px] font-semibold text-navy">
                        {member.name}
                        </p>

                        <p className="mt-0.5 text-[11px] font-medium text-primary">
                        {member.role}
                        </p>
                    </div>
                    </div>

                    <p className="mt-4 text-[11px] leading-5 text-muted-foreground">
                    {member.area}
                    </p>
                </article>
                ))}
            </div>

            <p className="mt-5 text-[10px] text-muted-foreground">
                Demonstration team profiles for the INSUREAI prototype.
            </p>
            </div>


            {/* CONTACT */}

            <div
            id="contact"
            className="surface-card scroll-mt-24 p-7 sm:p-8"
            >
            <p className="font-mono text-[10px] font-semibold tracking-[0.16em] text-primary">
                CONTACT
            </p>

            <h2 className="mt-3 text-[26px] font-semibold tracking-[-0.02em] text-navy">
                Talk to INSUREAI.
            </h2>

            <p className="mt-3 text-[13px] leading-6 text-muted-foreground">
                Get in touch for product demonstrations, platform enquiries
                and partnership discussions.
            </p>

            <div className="mt-7 grid gap-3 md:grid-cols-3">

                <div className="rounded-2xl border border-border bg-surface-muted/50 p-4">
                <p className="font-mono text-[9px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                    Email
                </p>

                <p className="mt-2 text-[13px] font-semibold text-navy">
                    hello@insureai.example
                </p>
                </div>

                <div className="rounded-2xl border border-border bg-surface-muted/50 p-4">
                <p className="font-mono text-[9px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                    Phone
                </p>

                <p className="mt-2 text-[13px] font-semibold text-navy">
                    +91 00000 00000
                </p>
                </div>

                <div className="rounded-2xl border border-border bg-surface-muted/50 p-4">
                <p className="font-mono text-[9px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                    Office
                </p>

                <p className="mt-2 text-[13px] font-semibold text-navy">
                    Mumbai, Maharashtra, India
                </p>
                </div>

            </div>

            <p className="mt-5 text-[10px] leading-5 text-muted-foreground">
                Demonstration contact information for the INSUREAI prototype.
            </p>
            </div>
        </div>
        </section>
    </>
  );
}