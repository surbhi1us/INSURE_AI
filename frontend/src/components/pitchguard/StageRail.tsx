import { STAGES } from "@/lib/pitchguard";

export function StageRail({ activeStage }: { activeStage: number }) {
  return (
    <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      {STAGES.map((stage) => {
        const isActive = stage.id === activeStage;
        const isDone = stage.id < activeStage;
        return (
          <div
            key={stage.id}
            className={
              isActive
                ? "brand-gradient rounded-2xl p-[1.5px] shadow-[var(--shadow-lift)]"
                : "rounded-2xl border border-border bg-surface shadow-[var(--shadow-soft)]"
            }
          >
            <div
              className={
                isActive
                  ? "flex items-center gap-3 rounded-[calc(var(--radius)-2px)] bg-surface px-4 py-4"
                  : "flex items-center gap-3 px-4 py-4"
              }
            >
              <span
                className={
                  isActive
                    ? "brand-gradient grid size-9 shrink-0 place-items-center rounded-xl font-mono text-[13px] font-semibold text-primary-foreground"
                    : isDone
                      ? "grid size-9 shrink-0 place-items-center rounded-xl bg-verified-soft font-mono text-[13px] font-semibold text-verified"
                      : "grid size-9 shrink-0 place-items-center rounded-xl bg-surface-muted font-mono text-[13px] font-semibold text-muted-foreground"
                }
              >
                {isDone ? "✓" : `0${stage.id}`}
              </span>
              <p
                className={
                  isActive
                    ? "min-w-0 truncate text-[15px] font-semibold text-navy"
                    : "min-w-0 truncate text-[15px] font-medium text-muted-foreground"
                }
              >
                {stage.label}
              </p>
            </div>
          </div>
        );
      })}
    </section>
  );
}
