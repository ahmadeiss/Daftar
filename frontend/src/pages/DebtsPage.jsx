import {
  CheckCircle2,
  Edit3,
  ImagePlus,
  MinusCircle,
  Plus,
  PlusCircle,
  Trash2,
  X,
} from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { apiRequest } from "../api/client.js";
import Button from "../components/Button.jsx";
import Field, { inputClass } from "../components/Field.jsx";
import RiskBadge from "../components/RiskBadge.jsx";
import StatusBadge from "../components/StatusBadge.jsx";
import { formatDate, money, todayInput, unpack } from "../utils.js";

const blankForm = {
  customer: "",
  total_amount: "",
  description: "",
  start_date: todayInput(),
  installment_count: "1",
  receipt_image: null,
};

const blankAction = {
  debtId: null,
  type: "payment",
  amount: "",
  note: "",
  due_date: todayInput(),
};

export default function DebtsPage() {
  const { t } = useTranslation();
  const [debts, setDebts] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [form, setForm] = useState(blankForm);
  const [action, setAction] = useState(blankAction);
  const [editingId, setEditingId] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState("");

  async function load() {
    setError("");
    try {
      const [debtsData, customersData] = await Promise.all([
        apiRequest("/debts/"),
        apiRequest("/customers/"),
      ]);
      const customerList = unpack(customersData);
      setDebts(unpack(debtsData));
      setCustomers(customerList);
      setForm((current) => ({
        ...current,
        customer: current.customer || customerList[0]?.id || "",
      }));
    } catch (err) {
      setError(err.message || t("error"));
    }
  }

  useEffect(() => {
    load();
  }, []);

  const update = (field, value) => setForm((current) => ({ ...current, [field]: value }));
  const updateAction = (field, value) => setAction((current) => ({ ...current, [field]: value }));

  function reset() {
    setForm({
      ...blankForm,
      customer: customers[0]?.id || "",
      start_date: todayInput(),
    });
    setEditingId(null);
    setShowForm(false);
  }

  function resetAction() {
    setAction({ ...blankAction, due_date: todayInput() });
  }

  async function submit(event) {
    event.preventDefault();
    const payload = new FormData();
    payload.append("customer", form.customer);
    payload.append("total_amount", form.total_amount);
    payload.append("description", form.description);
    payload.append("start_date", form.start_date);
    payload.append("installment_count", form.installment_count || "1");
    if (form.receipt_image) payload.append("receipt_image", form.receipt_image);

    const path = editingId ? `/debts/${editingId}/` : "/debts/";
    const method = editingId ? "PATCH" : "POST";
    try {
      await apiRequest(path, { method, body: payload });
      reset();
      load();
    } catch (err) {
      setError(err.message || t("error"));
    }
  }

  async function submitAction(event) {
    event.preventDefault();
    const endpoint = action.type === "payment" ? "record-payment" : "add-charge";
    const body = {
      amount: action.amount,
      note: action.note,
    };
    if (action.type === "charge") body.due_date = action.due_date;

    try {
      await apiRequest(`/debts/${action.debtId}/${endpoint}/`, {
        method: "POST",
        body,
      });
      resetAction();
      load();
    } catch (err) {
      setError(err.message || t("error"));
    }
  }

  async function remove(id) {
    if (!window.confirm(t("confirmDelete"))) return;
    await apiRequest(`/debts/${id}/`, { method: "DELETE" });
    load();
  }

  function edit(debt) {
    setEditingId(debt.id);
    setForm({
      customer: debt.customer,
      total_amount: debt.total_amount,
      description: debt.description,
      start_date: debt.start_date,
      installment_count: debt.installment_count,
      receipt_image: null,
    });
    setShowForm(true);
  }

  function openAction(debt, type) {
    setAction({
      debtId: debt.id,
      type,
      amount: type === "payment" ? debt.remaining_amount : "",
      note: "",
      due_date: todayInput(),
    });
  }

  async function markPaid(id) {
    await apiRequest(`/installments/${id}/mark-paid/`, { method: "POST" });
    load();
  }

  return (
    <div className="space-y-4">
      <Button onClick={() => setShowForm(true)} className="w-full">
        <Plus size={22} aria-hidden="true" />
        {t("addDebt")}
      </Button>

      {error && (
        <div className="rounded-card border border-red-200 bg-red-50 p-3 font-semibold text-red-700">
          {error}
        </div>
      )}

      {showForm && (
        <form onSubmit={submit} className="space-y-3 rounded-card border border-slate-200 bg-white p-4 shadow-soft">
          <div className="flex items-center justify-between">
            <h2 className="font-black">{editingId ? t("editDebt") : t("addDebt")}</h2>
            <button type="button" onClick={reset} className="rounded-card p-2 text-slate-500" aria-label={t("cancel")}>
              <X size={20} aria-hidden="true" />
            </button>
          </div>

          {customers.length === 0 ? (
            <div className="rounded-card border border-amber-200 bg-amber-50 p-3 text-sm font-bold text-amber-800">
              {t("addFirstCustomer")}
            </div>
          ) : (
            <>
              <Field label={t("customer")}>
                <select className={inputClass} value={form.customer} onChange={(event) => update("customer", event.target.value)} required>
                  {customers.map((customer) => (
                    <option key={customer.id} value={customer.id}>
                      {customer.name}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label={t("amount")}>
                <input className={`${inputClass} ltr-num`} type="number" min="0.01" step="0.01" value={form.total_amount} onChange={(event) => update("total_amount", event.target.value)} required />
              </Field>
              <Field label={t("description")}>
                <input className={inputClass} value={form.description} onChange={(event) => update("description", event.target.value)} required />
              </Field>
              <div className="grid grid-cols-2 gap-3">
                <Field label={t("startDate")}>
                  <input className={`${inputClass} ltr-num`} type="date" value={form.start_date} onChange={(event) => update("start_date", event.target.value)} required />
                </Field>
                <Field label={t("installments")}>
                  <input className={`${inputClass} ltr-num`} type="number" min="1" max="60" value={form.installment_count} onChange={(event) => update("installment_count", event.target.value)} required />
                </Field>
              </div>
              <Field label={t("receipt")}>
                <label className="tap-target flex cursor-pointer items-center justify-center gap-2 rounded-card border border-dashed border-slate-300 bg-slate-50 px-3 py-3 font-bold text-slate-600">
                  <ImagePlus size={20} aria-hidden="true" />
                  {form.receipt_image?.name || t("chooseFile")}
                  <input
                    className="hidden"
                    type="file"
                    accept="image/*"
                    onChange={(event) => update("receipt_image", event.target.files?.[0] || null)}
                  />
                </label>
              </Field>
              <div className="grid grid-cols-2 gap-2">
                <Button type="submit">{t("save")}</Button>
                <Button variant="secondary" onClick={reset}>{t("cancel")}</Button>
              </div>
            </>
          )}
        </form>
      )}

      <section className="space-y-3">
        {debts.length === 0 && (
          <div className="rounded-card border border-slate-200 bg-white p-4 text-sm font-semibold text-slate-500 shadow-soft">
            {t("noItems")}
          </div>
        )}
        {debts.map((debt) => (
          <article key={debt.id} className="rounded-card border border-slate-200 bg-white shadow-soft">
            <div className="grid grid-cols-[1fr_auto] gap-3 border-b border-slate-100 p-4">
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <h3 className="truncate text-lg font-black">{debt.customer_detail?.name}</h3>
                  <StatusBadge status={debt.status} />
                  <RiskBadge level={debt.customer_detail?.risk_level} />
                </div>
                <p className="mt-1 truncate text-sm font-semibold text-slate-500">{debt.description}</p>
                <div className="mt-2 grid grid-cols-3 gap-2 text-sm font-bold">
                  <DebtNumber label={t("totalDebts")} value={money(debt.total_amount)} />
                  <DebtNumber label={t("paidAmount")} value={money(debt.paid_amount)} tone="text-emerald-700" />
                  <DebtNumber label={t("remainingAmount")} value={money(debt.remaining_amount)} tone="text-clay" />
                </div>
                {debt.receipt_url && <a className="mt-2 inline-block text-sm font-bold text-palm" href={debt.receipt_url} target="_blank" rel="noreferrer">{t("receiptAttached")}</a>}
              </div>
              <div className="flex flex-col gap-2">
                <Button variant="secondary" className="px-3" onClick={() => edit(debt)} aria-label={t("edit")}>
                  <Edit3 size={18} aria-hidden="true" />
                </Button>
                <Button variant="danger" className="px-3" onClick={() => remove(debt.id)} aria-label={t("delete")}>
                  <Trash2 size={18} aria-hidden="true" />
                </Button>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2 border-b border-slate-100 p-3">
              <Button variant="secondary" onClick={() => openAction(debt, "payment")}>
                <MinusCircle size={18} aria-hidden="true" />
                {t("addPayment")}
              </Button>
              <Button variant="secondary" onClick={() => openAction(debt, "charge")}>
                <PlusCircle size={18} aria-hidden="true" />
                {t("addCharge")}
              </Button>
            </div>

            {action.debtId === debt.id && (
              <form onSubmit={submitAction} className="space-y-3 border-b border-slate-100 bg-slate-50 p-3">
                <div className="flex items-center justify-between">
                  <h4 className="font-black">{action.type === "payment" ? t("addPayment") : t("addCharge")}</h4>
                  <button type="button" onClick={resetAction} className="rounded-card p-2 text-slate-500" aria-label={t("cancel")}>
                    <X size={18} aria-hidden="true" />
                  </button>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <Field label={action.type === "payment" ? t("paymentAmount") : t("chargeAmount")}>
                    <input className={`${inputClass} ltr-num`} type="number" min="0.01" step="0.01" value={action.amount} onChange={(event) => updateAction("amount", event.target.value)} required />
                  </Field>
                  {action.type === "charge" && (
                    <Field label={t("dueDateOptional")}>
                      <input className={`${inputClass} ltr-num`} type="date" value={action.due_date} onChange={(event) => updateAction("due_date", event.target.value)} />
                    </Field>
                  )}
                </div>
                <Field label={t("actionNote")}>
                  <input className={inputClass} value={action.note} onChange={(event) => updateAction("note", event.target.value)} />
                </Field>
                <Button type="submit" className="w-full">
                  {action.type === "payment" ? t("submitPayment") : t("submitCharge")}
                </Button>
              </form>
            )}

            <div className="divide-y divide-slate-100">
              {debt.installments.map((installment) => (
                <div key={installment.id} className="grid grid-cols-[1fr_auto] gap-2 px-4 py-3">
                  <div>
                    <div className="ltr-num font-black">{money(installment.amount)}</div>
                    <div className="mt-1 flex flex-wrap gap-2 text-xs font-bold text-slate-500">
                      <span>{formatDate(installment.due_date)}</span>
                      {Number(installment.paid_amount) > 0 && Number(installment.remaining_amount) > 0 && (
                        <span className="ltr-num text-clay">{t("partial")}: {money(installment.paid_amount)}</span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <StatusBadge status={installment.status} />
                    {installment.status !== "paid" && (
                      <Button variant="secondary" className="px-3 py-1.5 text-sm" onClick={() => markPaid(installment.id)} aria-label={t("markPaid")}>
                        <CheckCircle2 size={18} aria-hidden="true" />
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {debt.activities?.length > 0 && (
              <div className="border-t border-slate-100 bg-slate-50 px-4 py-3">
                <div className="mb-2 text-sm font-black text-slate-600">{t("activity")}</div>
                <div className="space-y-1">
                  {debt.activities.slice(0, 4).map((item) => (
                    <div key={item.id} className="flex items-center justify-between gap-2 text-xs font-bold text-slate-600">
                      <span className="truncate">{activityLabel(t, item.activity_type)} {item.note ? `- ${item.note}` : ""}</span>
                      <span className="ltr-num shrink-0">{money(item.amount)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </article>
        ))}
      </section>
    </div>
  );
}

function DebtNumber({ label, value, tone = "text-ink" }) {
  return (
    <div className="rounded-card bg-slate-50 p-2">
      <div className="text-[11px] font-bold text-slate-500">{label}</div>
      <div className={`ltr-num mt-1 text-sm font-black ${tone}`}>{value}</div>
    </div>
  );
}

function activityLabel(t, type) {
  if (type === "payment") return t("activityPayment");
  if (type === "charge") return t("activityCharge");
  return t("activityNote");
}
