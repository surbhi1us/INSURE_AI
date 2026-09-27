import { useEffect, useState } from "react";

const NAV_ITEMS = [
  { label: "Workspace", href: "#workspace", id: "workspace" },
  { label: "How It Works", href: "#how-it-works", id: "how-it-works" },
  { label: "About", href: "#about", id: "about" },
  { label: "Team", href: "#team", id: "team" },
  { label: "Contact", href: "#contact", id: "contact" },
];

export function TopNav() {
  const [activeSection, setActiveSection] = useState("workspace");

  useEffect(() => {
    const updateActiveSection = () => {
      const marker = window.scrollY + 140;
      let current = "workspace";

      for (const item of NAV_ITEMS) {
        const section = document.getElementById(item.id);
        if (section && section.offsetTop <= marker) current = item.id;
      }

      setActiveSection(current);
    };

    updateActiveSection();
    window.addEventListener("scroll", updateActiveSection, { passive: true });
    window.addEventListener("resize", updateActiveSection);

    return () => {
      window.removeEventListener("scroll", updateActiveSection);
      window.removeEventListener("resize", updateActiveSection);
    };
  }, []);

  return (
    <header className="sticky top-0 z-40 border-b border-border/80 bg-surface/90 backdrop-blur-xl">
      <div className="mx-auto flex max-w-[1400px] items-center justify-between gap-5 px-6 py-3.5">
        <a href="#workspace" className="flex min-w-0 items-center gap-3" aria-label="INSUREAI home">
          <div className="brand-gradient grid size-10 shrink-0 place-items-center rounded-xl shadow-[var(--shadow-soft)]">
            <span className="font-mono text-sm font-semibold text-primary-foreground">I</span>
          </div>
          <div className="min-w-0">
            <p className="truncate text-[16px] font-semibold tracking-tight text-navy">INSUREAI</p>
            <p className="hidden truncate text-[11px] text-muted-foreground sm:block">Evidence-backed insurance intelligence</p>
          </div>
        </a>

        <nav className="hidden items-center gap-1 lg:flex" aria-label="Primary navigation">
          {NAV_ITEMS.map((item) => {
            const active = activeSection === item.id;
            return (
              <a
                key={item.label}
                href={item.href}
                aria-current={active ? "page" : undefined}
                className={`rounded-lg px-3 py-2 text-[12px] font-medium transition-colors ${
                  active
                    ? "bg-surface-muted text-navy shadow-sm"
                    : "text-muted-foreground hover:bg-surface-muted hover:text-navy"
                }`}
              >
                {item.label}
              </a>
            );
          })}
        </nav>

        <div className="flex items-center gap-2.5 rounded-full border border-border bg-surface px-2 py-1.5 pr-3.5 shadow-[var(--shadow-soft)]">
          <span className="relative flex size-7 shrink-0 items-center justify-center">
            <span className="absolute size-2 rounded-full bg-verified" />
            <span className="absolute size-2 animate-ping rounded-full bg-verified opacity-30" />
          </span>
          <span className="hidden text-[12px] font-medium text-secondary-foreground sm:inline">Advisor workspace</span>
        </div>
      </div>
    </header>
  );
}
