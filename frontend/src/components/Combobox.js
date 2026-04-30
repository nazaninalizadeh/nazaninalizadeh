import React, { useState, useRef, useEffect } from 'react';

/**
 * Lightweight searchable autocomplete (combobox) that doesn't depend on shadcn Command/Popover.
 * - `options`: array of strings OR [value, label] tuples.
 * - `value`: current string.
 * - `onChange(newValue)`.
 * - `placeholder`, `dataTestid`, `disabled`.
 */
export const Combobox = ({ options, value, onChange, placeholder, dataTestid, disabled }) => {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState(value || '');
  const ref = useRef(null);

  useEffect(() => { setQuery(value || ''); }, [value]);

  useEffect(() => {
    const onClick = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener('mousedown', onClick);
    return () => document.removeEventListener('mousedown', onClick);
  }, []);

  const norm = (opt) => Array.isArray(opt) ? { value: opt[0], label: opt[1] } : { value: opt, label: opt };
  const filtered = (options || [])
    .map(norm)
    .filter(o => !query || o.label.toLowerCase().includes(query.toLowerCase()) || o.value.toLowerCase().includes(query.toLowerCase()))
    .slice(0, 50);

  const pick = (o) => { onChange(o.value); setQuery(o.label); setOpen(false); };

  return (
    <div ref={ref} className="relative w-full">
      <input
        type="text"
        className="w-full px-3 py-2 rounded-xl text-sm luxury-input"
        placeholder={placeholder}
        value={query}
        disabled={disabled}
        onFocus={() => setOpen(true)}
        onChange={(e) => { setQuery(e.target.value); onChange(e.target.value); setOpen(true); }}
        data-testid={dataTestid}
      />
      {open && filtered.length > 0 && (
        <div
          className="absolute left-0 right-0 mt-1 rounded-xl shadow-lg z-50 max-h-56 overflow-y-auto"
          style={{ background: 'white', border: '1px solid rgba(217,42,42,0.2)' }}
        >
          {filtered.map((o, idx) => (
            <button
              key={`${o.value}-${idx}`}
              type="button"
              onClick={() => pick(o)}
              className="w-full text-left px-3 py-2 text-sm hover:bg-rose-50/50 transition-colors"
              style={{ color: '#0F172A' }}
            >
              {o.label}{Array.isArray(options[0]) && o.value !== o.label ? <span className="ml-2 text-xs" style={{ color: '#64748B' }}>({o.value})</span> : null}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default Combobox;
