// webapp/src/theme.ts
export function applyThemeFromTelegram(tg: any) {
  const p = tg?.themeParams || {};
  const isDark = (tg?.colorScheme || "dark") === "dark";
  const cssVars: Record<string, string> = {
    "--bg":     p.bg_color || (isDark ? "#0b0d0f" : "#fafafa"),
    "--card":   p.secondary_bg_color || (isDark ? "#111418" : "#ffffff"),
    "--text":   p.text_color || (isDark ? "#e6edf3" : "#111827"),
    "--muted":  p.hint_color || (isDark ? "#9aa4b2" : "#6b7280"),
    "--border": p.section_separator_color || (isDark ? "#1f242b" : "#e5e7eb")
  };
  for (const k in cssVars) document.documentElement.style.setProperty(k, cssVars[k]);
}