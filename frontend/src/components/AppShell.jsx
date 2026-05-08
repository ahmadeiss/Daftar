import {
  LayoutDashboard,
  Settings,
  Users,
  WalletCards,
} from "lucide-react";
import { useTranslation } from "react-i18next";

const navItems = [
  { id: "dashboard", icon: LayoutDashboard },
  { id: "customers", icon: Users },
  { id: "debts", icon: WalletCards },
  { id: "settings", icon: Settings },
];

export default function AppShell({ page, setPage, children }) {
  const { t } = useTranslation();

  return (
    <div className="min-h-screen bg-paper text-ink">
      <header className="sticky top-0 z-10 border-b border-slate-200 bg-paper/95 backdrop-blur">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-3">
          <div>
            <div className="text-lg font-black text-palm">{t("appName")}</div>
            <div className="text-xs font-semibold text-slate-500">{t(page)}</div>
          </div>
        </div>
      </header>

      <main className="safe-bottom mx-auto max-w-3xl px-4 py-4">{children}</main>

      <nav className="fixed inset-x-0 bottom-0 z-20 border-t border-slate-200 bg-white">
        <div className="mx-auto grid max-w-3xl grid-cols-4 px-2 pb-[env(safe-area-inset-bottom)] pt-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = page === item.id;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => setPage(item.id)}
                className={`tap-target flex flex-col items-center justify-center gap-1 rounded-card px-2 py-2 text-xs font-bold ${
                  active ? "bg-teal-50 text-palm" : "text-slate-500"
                }`}
                aria-label={t(item.id)}
                title={t(item.id)}
              >
                <Icon size={22} aria-hidden="true" />
                <span>{t(item.id)}</span>
              </button>
            );
          })}
        </div>
      </nav>
    </div>
  );
}
