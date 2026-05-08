export default function Field({ label, children }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-sm font-semibold text-slate-700">{label}</span>
      {children}
    </label>
  );
}

export const inputClass =
  "tap-target w-full rounded-card border border-slate-200 bg-white px-3 py-2.5 text-base text-ink outline-none focus:border-palm focus:ring-2 focus:ring-teal-100";
