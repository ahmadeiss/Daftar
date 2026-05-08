import { useTranslation } from "react-i18next";

import { riskLabelKey, riskTone } from "../utils.js";

export default function RiskBadge({ level }) {
  const { t } = useTranslation();

  return (
    <span
      className={`inline-flex min-w-20 items-center justify-center rounded-full border px-3 py-1 text-xs font-bold ${riskTone(level)}`}
    >
      {t(riskLabelKey(level))}
    </span>
  );
}
