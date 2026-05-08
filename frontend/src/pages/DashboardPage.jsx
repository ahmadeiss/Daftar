import {
  AlertTriangle,
  CalendarClock,
  CheckCircle2,
  ShieldCheck,
  Users,
  UserRoundX,
  WalletCards,
} from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { apiRequest } from "../api/client.js";
import Button from "../components/Button.jsx";
import StatCard from "../components/StatCard.jsx";
import StatusBadge from "../components/StatusBadge.jsx";
import RiskBadge from "../components/RiskBadge.jsx";
import { formatDate, money } from "../utils.js";

export default function DashboardPage() {
  const { t } = useTranslation();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  async function load() {
    setError("");
    try {
      setData(await apiRequest("/dashboard/"));
    } catch (err) {
      setError(err.message || t("error"));
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function markPaid(id) {
    await apiRequest(`/installments/${id}/mark-paid/`, { method: "POST" });
    load();
  }

  if (!data && !error) {
    return <div className="py-10 text-center font-bold text-palm">{t("loading")}</div>;
  }

  return (
    <div className="space-y-4">
      {error && (
        <div className="rounded-card border border-red-200 bg-red-50 p-3 font-semibold text-red-700">
          {error}
        </div>
      )}

      {data && (
        <>
          <section className="grid grid-cols-2 gap-3">
            <StatCard icon={WalletCards} label={t("totalDebts")} value={money(data.total_debts)} />
            <StatCard icon={CheckCircle2} label={t("paid")} value={money(data.paid_amount)} tone="text-emerald-700" />
            <StatCard icon={AlertTriangle} label={t("overdue")} value={money(data.overdue_amount)} tone="text-red-700" />
            <StatCard icon={Users} label={t("customersCount")} value={data.customers_count} tone="text-blue-700" />
          </section>

          <InstallmentList
            title={t("overdue")}
            icon={AlertTriangle}
            items={data.overdue_installments}
            empty={t("noItems")}
            onPaid={markPaid}
          />
          <CustomerList
            title={t("committedCustomers")}
            icon={ShieldCheck}
            items={data.committed_customers || []}
            empty={t("noItems")}
          />
          <CustomerList
            title={t("riskyCustomers")}
            icon={UserRoundX}
            items={data.risky_customers || []}
            empty={t("noItems")}
          />
          <InstallmentList
            title={t("upcoming")}
            icon={CalendarClock}
            items={data.upcoming_installments}
            empty={t("noItems")}
            onPaid={markPaid}
          />
        </>
      )}
    </div>
  );
}

function CustomerList({ title, icon: Icon, items, empty }) {
  const { t } = useTranslation();

  return (
    <section className="rounded-card border border-slate-200 bg-white shadow-soft">
      <div className="flex items-center gap-2 border-b border-slate-100 px-4 py-3 font-black">
        <Icon size={20} aria-hidden="true" />
        {title}
      </div>
      <div className="divide-y divide-slate-100">
        {items.length === 0 && <div className="p-4 text-sm font-semibold text-slate-500">{empty}</div>}
        {items.map((customer) => (
          <div key={customer.id} className="grid grid-cols-[1fr_auto] gap-3 px-4 py-3">
            <div className="min-w-0">
              <div className="truncate font-bold text-ink">{customer.name}</div>
              <div className="ltr-num mt-1 text-sm font-semibold text-slate-500">{customer.phone}</div>
              <div className="mt-2 flex flex-wrap items-center gap-2">
                <RiskBadge level={customer.risk_level} />
                <span className="text-xs font-bold text-slate-500">
                  {t("commitmentScore")}: {customer.commitment_score}
                </span>
              </div>
            </div>
            <div className="text-end">
              <div className="ltr-num font-black text-ink">{money(customer.outstanding_amount)}</div>
              <div className="text-xs font-bold text-slate-500">{t("remainingAmount")}</div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function InstallmentList({ title, icon: Icon, items, empty, onPaid }) {
  const { t } = useTranslation();

  return (
    <section className="rounded-card border border-slate-200 bg-white shadow-soft">
      <div className="flex items-center gap-2 border-b border-slate-100 px-4 py-3 font-black">
        <Icon size={20} aria-hidden="true" />
        {title}
      </div>
      <div className="divide-y divide-slate-100">
        {items.length === 0 && <div className="p-4 text-sm font-semibold text-slate-500">{empty}</div>}
        {items.map((item) => (
          <div key={item.id} className="grid grid-cols-[1fr_auto] gap-3 px-4 py-3">
            <div className="min-w-0">
              <div className="font-bold text-ink">{item.customer_name}</div>
              <div className="truncate text-sm font-semibold text-slate-500">{item.debt_description}</div>
              <div className="mt-2 flex flex-wrap items-center gap-2">
                <StatusBadge status={item.status} />
                <span className="text-xs font-bold text-slate-500">{formatDate(item.due_date)}</span>
              </div>
            </div>
            <div className="flex flex-col items-end justify-between gap-2">
              <div className="ltr-num font-black text-ink">{money(item.amount)}</div>
              {item.status !== "paid" && (
                <Button variant="secondary" className="px-3 py-1.5 text-sm" onClick={() => onPaid(item.id)}>
                  {t("markPaid")}
                </Button>
              )}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
