import { useTranslation } from "react-i18next";

import { statusTone } from "../utils.js";

export default function StatusBadge({ status }) {
  const { t } = useTranslation();
  const labels = {
    paid: t("statusPaid"),
    unpaid: t("statusUnpaid"),
    late: t("statusLate"),
  };

  return (
    <span
      className={`inline-flex min-w-20 items-center justify-center rounded-full border px-3 py-1 text-xs font-bold ${statusTone(status)}`}
    >
      {labels[status] || status}
    </span>
  );
}
