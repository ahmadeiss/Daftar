export default function StatCard({ icon: Icon, label, value, tone = "text-palm" }) {
  return (
    <div className="rounded-card border border-slate-200 bg-white p-4 shadow-soft">
      <div className={`mb-3 inline-flex h-10 w-10 items-center justify-center rounded-card bg-slate-50 ${tone}`}>
        <Icon size={22} aria-hidden="true" />
      </div>
      <div className="text-sm font-semibold text-slate-500">{label}</div>
      <div className="ltr-num mt-1 text-2xl font-bold text-ink">{value}</div>
    </div>
  );
}
