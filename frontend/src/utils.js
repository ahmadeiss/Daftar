export function unpack(data) {
  if (Array.isArray(data)) return data;
  return data?.results || [];
}

export function money(value) {
  const number = Number(value || 0);
  return `${number.toFixed(2)} ₪`;
}

export function todayInput() {
  return new Date().toISOString().slice(0, 10);
}

export function statusTone(status) {
  if (status === "paid") return "bg-emerald-50 text-emerald-700 border-emerald-200";
  if (status === "late") return "bg-red-50 text-red-700 border-red-200";
  return "bg-amber-50 text-amber-800 border-amber-200";
}

export function riskTone(level) {
  if (level === "trusted") return "bg-emerald-50 text-emerald-700 border-emerald-200";
  if (level === "risky") return "bg-red-50 text-red-700 border-red-200";
  if (level === "watch") return "bg-amber-50 text-amber-800 border-amber-200";
  return "bg-blue-50 text-blue-700 border-blue-200";
}

export function riskLabelKey(level) {
  if (level === "trusted") return "riskTrusted";
  if (level === "risky") return "riskRisky";
  if (level === "watch") return "riskWatch";
  return "riskNew";
}

export function recommendationKey(level) {
  if (level === "trusted") return "recommendationTrusted";
  if (level === "risky") return "recommendationRisky";
  if (level === "watch") return "recommendationWatch";
  return "recommendationNew";
}

export function formatDate(value) {
  if (!value) return "";
  return new Intl.DateTimeFormat(document.documentElement.lang || "ar", {
    year: "numeric",
    month: "short",
    day: "numeric",
  }).format(new Date(`${value}T12:00:00`));
}
