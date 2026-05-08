import { BookOpenCheck } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";

import { useAuth } from "../api/auth.jsx";
import Button from "../components/Button.jsx";
import Field, { inputClass } from "../components/Field.jsx";

export default function LoginPage() {
  const { t } = useTranslation();
  const { login, register } = useAuth();
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
  });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const update = (field, value) => setForm((current) => ({ ...current, [field]: value }));

  async function submit(event) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      if (mode === "login") {
        await login(form.email, form.password);
      } else {
        await register({
          name: form.name,
          email: form.email,
          password: form.password,
        });
      }
    } catch (err) {
      setError(err.message || t("error"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-paper px-4 py-8">
      <section className="w-full max-w-md rounded-card border border-slate-200 bg-white p-5 shadow-soft">
        <div className="mb-6 flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-card bg-teal-50 text-palm">
            <BookOpenCheck size={28} aria-hidden="true" />
          </div>
          <div>
            <h1 className="text-2xl font-black text-ink">{t("appName")}</h1>
          </div>
        </div>

        <form onSubmit={submit} className="space-y-4">
          {mode === "register" && (
            <Field label={t("merchantName")}>
              <input
                className={inputClass}
                value={form.name}
                onChange={(event) => update("name", event.target.value)}
                autoComplete="organization"
              />
            </Field>
          )}

          <Field label={t("email")}>
            <input
              className={`${inputClass} ltr-num`}
              type="email"
              value={form.email}
              onChange={(event) => update("email", event.target.value)}
              autoComplete="email"
              required
            />
          </Field>

          <Field label={t("password")}>
            <input
              className={inputClass}
              type="password"
              value={form.password}
              onChange={(event) => update("password", event.target.value)}
              autoComplete={mode === "login" ? "current-password" : "new-password"}
              required
              minLength={8}
            />
          </Field>

          {error && (
            <div className="rounded-card border border-red-200 bg-red-50 px-3 py-2 text-sm font-semibold text-red-700">
              {error}
            </div>
          )}

          <Button type="submit" className="w-full" disabled={busy}>
            {mode === "login" ? t("enter") : t("createAccount")}
          </Button>
        </form>

        <button
          type="button"
          onClick={() => {
            setError("");
            setMode(mode === "login" ? "register" : "login");
          }}
          className="tap-target mt-4 w-full rounded-card text-center text-sm font-bold text-palm"
        >
          {mode === "login" ? t("newAccount") : t("haveAccount")}
        </button>
      </section>
    </main>
  );
}
