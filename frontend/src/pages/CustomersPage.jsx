import { Edit3, History, Plus, Search, Trash2, UserRoundCheck, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";

import { apiRequest } from "../api/client.js";
import Button from "../components/Button.jsx";
import Field, { inputClass } from "../components/Field.jsx";
import RiskBadge from "../components/RiskBadge.jsx";
import StatusBadge from "../components/StatusBadge.jsx";
import { formatDate, money, recommendationKey, unpack } from "../utils.js";

const blankForm = { name: "", phone: "", notes: "" };
const segments = ["all", "committed", "risky"];

export default function CustomersPage() {
  const { t } = useTranslation();
  const [customers, setCustomers] = useState([]);
  const [search, setSearch] = useState("");
  const [segment, setSegment] = useState("all");
  const [form, setForm] = useState(blankForm);
  const [editingId, setEditingId] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [profile, setProfile] = useState(null);
  const [profileLoading, setProfileLoading] = useState(false);
  const [error, setError] = useState("");

  async function load() {
    setError("");
    try {
      const query = search ? `?search=${encodeURIComponent(search)}` : "";
      setCustomers(unpack(await apiRequest(`/customers/${query}`)));
    } catch (err) {
      setError(err.message || t("error"));
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(load, 200);
    return () => window.clearTimeout(timer);
  }, [search]);

  const visibleCustomers = useMemo(() => {
    if (segment === "committed") {
      return customers.filter((customer) => ["trusted", "new"].includes(customer.risk_level));
    }
    if (segment === "risky") {
      return customers.filter((customer) => ["watch", "risky"].includes(customer.risk_level));
    }
    return customers;
  }, [customers, segment]);

  const update = (field, value) => setForm((current) => ({ ...current, [field]: value }));

  function reset() {
    setForm(blankForm);
    setEditingId(null);
    setShowForm(false);
  }

  async function submit(event) {
    event.preventDefault();
    const path = editingId ? `/customers/${editingId}/` : "/customers/";
    const method = editingId ? "PATCH" : "POST";
    try {
      await apiRequest(path, { method, body: form });
      reset();
      load();
    } catch (err) {
      setError(err.message || t("error"));
    }
  }

  async function remove(id) {
    if (!window.confirm(t("confirmDelete"))) return;
    await apiRequest(`/customers/${id}/`, { method: "DELETE" });
    load();
  }

  function edit(customer) {
    setEditingId(customer.id);
    setForm({ name: customer.name, phone: customer.phone, notes: customer.notes || "" });
    setShowForm(true);
  }

  async function openProfile(customer) {
    setProfileLoading(true);
    setProfile({ customer });
    try {
      setProfile(await apiRequest(`/customers/${customer.id}/profile/`));
    } catch (err) {
      setError(err.message || t("error"));
      setProfile(null);
    } finally {
      setProfileLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <label className="relative flex-1">
          <Search className="absolute top-3.5 text-slate-400 ltr:left-3 rtl:right-3" size={18} aria-hidden="true" />
          <input
            className={`${inputClass} ltr:pl-10 rtl:pr-10`}
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder={t("search")}
          />
        </label>
        <Button onClick={() => setShowForm(true)} className="px-3" aria-label={t("addCustomer")}>
          <Plus size={22} aria-hidden="true" />
        </Button>
      </div>

      <div className="grid grid-cols-3 gap-2">
        {segments.map((item) => (
          <button
            key={item}
            type="button"
            onClick={() => setSegment(item)}
            className={`tap-target rounded-card border px-3 py-2 text-sm font-bold ${
              segment === item ? "border-palm bg-teal-50 text-palm" : "border-slate-200 bg-white text-slate-600"
            }`}
          >
            {t(item)}
          </button>
        ))}
      </div>

      {error && (
        <div className="rounded-card border border-red-200 bg-red-50 p-3 font-semibold text-red-700">
          {error}
        </div>
      )}

      {showForm && (
        <form onSubmit={submit} className="space-y-3 rounded-card border border-slate-200 bg-white p-4 shadow-soft">
          <div className="flex items-center justify-between">
            <h2 className="font-black">{editingId ? t("editCustomer") : t("addCustomer")}</h2>
            <button type="button" onClick={reset} className="rounded-card p-2 text-slate-500" aria-label={t("cancel")}>
              <X size={20} aria-hidden="true" />
            </button>
          </div>
          <Field label={t("customerName")}>
            <input className={inputClass} value={form.name} onChange={(event) => update("name", event.target.value)} required />
          </Field>
          <Field label={t("phone")}>
            <input className={`${inputClass} ltr-num`} value={form.phone} onChange={(event) => update("phone", event.target.value)} required />
          </Field>
          <Field label={t("notes")}>
            <textarea className={`${inputClass} min-h-20`} value={form.notes} onChange={(event) => update("notes", event.target.value)} />
          </Field>
          <div className="grid grid-cols-2 gap-2">
            <Button type="submit">{t("save")}</Button>
            <Button variant="secondary" onClick={reset}>{t("cancel")}</Button>
          </div>
        </form>
      )}

      <section className="divide-y divide-slate-100 rounded-card border border-slate-200 bg-white shadow-soft">
        {visibleCustomers.length === 0 && <div className="p-4 text-sm font-semibold text-slate-500">{t("noItems")}</div>}
        {visibleCustomers.map((customer) => (
          <article key={customer.id} className="grid grid-cols-[1fr_auto] gap-3 p-4">
            <button type="button" onClick={() => openProfile(customer)} className="min-w-0 text-start">
              <div className="flex flex-wrap items-center gap-2">
                <h3 className="truncate text-lg font-black">{customer.name}</h3>
                <RiskBadge level={customer.risk_level} />
              </div>
              <p className="ltr-num mt-1 text-sm font-semibold text-slate-500">{customer.phone}</p>
              {customer.notes && <p className="mt-1 line-clamp-2 text-sm text-slate-500">{customer.notes}</p>}
              <div className="mt-2 flex flex-wrap items-center gap-3 text-sm font-bold">
                <span className="ltr-num text-clay">{t("remainingAmount")}: {money(customer.unpaid_amount)}</span>
                <span className="text-slate-500">{t("commitmentScore")}: {customer.commitment_score}</span>
              </div>
            </button>
            <div className="flex flex-col gap-2">
              <Button variant="secondary" className="px-3" onClick={() => openProfile(customer)} aria-label={t("viewProfile")}>
                <UserRoundCheck size={18} aria-hidden="true" />
              </Button>
              <Button variant="secondary" className="px-3" onClick={() => edit(customer)} aria-label={t("edit")}>
                <Edit3 size={18} aria-hidden="true" />
              </Button>
              <Button variant="danger" className="px-3" onClick={() => remove(customer.id)} aria-label={t("delete")}>
                <Trash2 size={18} aria-hidden="true" />
              </Button>
            </div>
          </article>
        ))}
      </section>

      {profile && (
        <CustomerProfile
          profile={profile}
          loading={profileLoading}
          onClose={() => setProfile(null)}
        />
      )}
    </div>
  );
}

function CustomerProfile({ profile, loading, onClose }) {
  const { t } = useTranslation();
  const customer = profile.customer;
  const reputation = profile.reputation || customer;
  const riskLevel = reputation.risk_level || customer.risk_level;

  return (
    <div className="fixed inset-0 z-30 flex items-end bg-slate-950/35 p-0 sm:items-center sm:p-4">
      <section className="max-h-[92vh] w-full overflow-y-auto rounded-t-card border border-slate-200 bg-paper p-4 shadow-soft sm:mx-auto sm:max-w-2xl sm:rounded-card">
        <div className="mb-4 flex items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="truncate text-2xl font-black">{customer.name}</h2>
              <RiskBadge level={riskLevel} />
            </div>
            <p className="ltr-num mt-1 text-sm font-semibold text-slate-500">{customer.phone}</p>
          </div>
          <button type="button" onClick={onClose} className="rounded-card p-2 text-slate-500" aria-label={t("close")}>
            <X size={22} aria-hidden="true" />
          </button>
        </div>

        {loading ? (
          <div className="py-8 text-center font-bold text-palm">{t("loading")}</div>
        ) : (
          <div className="space-y-4">
            <section className="rounded-card border border-slate-200 bg-white p-4 shadow-soft">
              <div className="mb-3 flex items-center gap-2 font-black">
                <UserRoundCheck size={20} aria-hidden="true" />
                {t("creditDecision")}
              </div>
              <div className="grid grid-cols-[auto_1fr] items-center gap-4">
                <div className="flex h-20 w-20 items-center justify-center rounded-full border-4 border-teal-100 bg-teal-50 text-2xl font-black text-palm">
                  {reputation.commitment_score}
                </div>
                <div>
                  <div className="font-black">{t("commitmentScore")}</div>
                  <p className="mt-1 text-sm font-semibold text-slate-600">{t(recommendationKey(riskLevel))}</p>
                </div>
              </div>
            </section>

            <section className="grid grid-cols-2 gap-3">
              <ProfileStat label={t("outstandingAmount")} value={money(reputation.outstanding_amount)} />
              <ProfileStat label={t("overdueAmount")} value={money(reputation.overdue_amount)} tone="text-red-700" />
              <ProfileStat label={t("paidInstallments")} value={reputation.paid_installments} tone="text-emerald-700" />
              <ProfileStat label={t("lateInstallments")} value={reputation.late_installments} tone="text-red-700" />
            </section>

            <section className="rounded-card border border-slate-200 bg-white shadow-soft">
              <div className="flex items-center gap-2 border-b border-slate-100 px-4 py-3 font-black">
                <History size={20} aria-hidden="true" />
                {t("customerHistory")}
              </div>
              <div className="divide-y divide-slate-100">
                {profile.recent_installments?.length === 0 && <div className="p-4 text-sm font-semibold text-slate-500">{t("noItems")}</div>}
                {profile.recent_installments?.map((item) => (
                  <div key={item.id} className="grid grid-cols-[1fr_auto] gap-2 p-4">
                    <div>
                      <div className="font-bold">{item.debt_description}</div>
                      <div className="mt-1 text-xs font-bold text-slate-500">{formatDate(item.due_date)}</div>
                    </div>
                    <div className="text-end">
                      <div className="ltr-num font-black">{money(item.amount)}</div>
                      <StatusBadge status={item.status} />
                    </div>
                  </div>
                ))}
              </div>
            </section>
          </div>
        )}
      </section>
    </div>
  );
}

function ProfileStat({ label, value, tone = "text-ink" }) {
  return (
    <div className="rounded-card border border-slate-200 bg-white p-3 shadow-soft">
      <div className="text-xs font-bold text-slate-500">{label}</div>
      <div className={`ltr-num mt-1 text-xl font-black ${tone}`}>{value}</div>
    </div>
  );
}
