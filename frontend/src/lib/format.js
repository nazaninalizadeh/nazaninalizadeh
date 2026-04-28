// Italian-style date formatting helpers (DD/MM/YYYY everywhere user-facing).
// All inputs in <input type="date"> still use ISO YYYY-MM-DD on the wire — only DISPLAY changes.

/** ISO 'YYYY-MM-DD' (or full ISO datetime) → 'DD/MM/YYYY'. Returns '' if invalid/empty. */
export const fmtDate = (v) => {
  if (!v) return "";
  const s = String(v).trim();
  // ISO date or datetime
  const isoMatch = s.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (isoMatch) return `${isoMatch[3]}/${isoMatch[2]}/${isoMatch[1]}`;
  // Already DD/MM/YYYY
  const ddmm = s.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  if (ddmm) return s;
  // Try Date.parse (Locale)
  const d = new Date(s);
  if (!isNaN(d.getTime())) {
    const dd = String(d.getDate()).padStart(2, "0");
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    return `${dd}/${mm}/${d.getFullYear()}`;
  }
  return s;
};

/** ISO 'YYYY-MM-DDTHH:MM:SSZ' or 'YYYY-MM-DD HH:MM:SS' → 'DD/MM/YYYY HH:MM'. */
export const fmtDateTime = (v) => {
  if (!v) return "";
  const date = fmtDate(v);
  const m = String(v).match(/(\d{2}:\d{2})/);
  return m ? `${date} ${m[1]}` : date;
};

/** Convert 'DD/MM/YYYY' → 'YYYY-MM-DD' (for sending to backend). */
export const toIsoDate = (v) => {
  if (!v) return "";
  const m = String(v).match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  if (m) return `${m[3]}-${m[2]}-${m[1]}`;
  return v;
};

/** Today as ISO YYYY-MM-DD. */
export const todayIso = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
};

/** ISO date plus N years (returns ISO). */
export const isoPlusYears = (iso, years) => {
  if (!iso) return "";
  const d = new Date(iso);
  d.setFullYear(d.getFullYear() + (years || 0));
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
};
