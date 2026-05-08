import { Languages, LogOut, Server } from "lucide-react";
import { useTranslation } from "react-i18next";

import { useAuth } from "../api/auth.jsx";
import { getApiBase } from "../api/client.js";
import Button from "../components/Button.jsx";

export default function SettingsPage() {
  const { t, i18n } = useTranslation();
  const { user, logout } = useAuth();
  const nextLanguage = i18n.language === "ar" ? "en" : "ar";

  return (
    <div className="space-y-4">
      <section className="rounded-card border border-slate-200 bg-white p-4 shadow-soft">
        <div className="text-sm font-semibold text-slate-500">{t("merchantName")}</div>
        <div className="mt-1 text-lg font-black">{user?.first_name || user?.email}</div>
        <div className="ltr-num mt-1 text-sm font-semibold text-slate-500">{user?.email}</div>
      </section>

      <section className="space-y-3 rounded-card border border-slate-200 bg-white p-4 shadow-soft">
        <Button
          variant="secondary"
          className="w-full justify-between"
          onClick={() => i18n.changeLanguage(nextLanguage)}
        >
          <span className="inline-flex items-center gap-2">
            <Languages size={20} aria-hidden="true" />
            {t("language")}
          </span>
          <span>{nextLanguage === "ar" ? t("arabic") : t("english")}</span>
        </Button>

        <div className="flex items-center gap-2 rounded-card bg-slate-50 p-3 text-sm font-semibold text-slate-600">
          <Server size={18} aria-hidden="true" />
          <span className="ltr-num truncate">{getApiBase()}</span>
        </div>

        <Button variant="danger" className="w-full" onClick={logout}>
          <LogOut size={20} aria-hidden="true" />
          {t("logout")}
        </Button>
      </section>
    </div>
  );
}
