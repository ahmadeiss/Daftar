import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { useAuth } from "./api/auth.jsx";
import AppShell from "./components/AppShell.jsx";
import DashboardPage from "./pages/DashboardPage.jsx";
import CustomersPage from "./pages/CustomersPage.jsx";
import DebtsPage from "./pages/DebtsPage.jsx";
import LoginPage from "./pages/LoginPage.jsx";
import SettingsPage from "./pages/SettingsPage.jsx";

export default function App() {
  const { user, loading } = useAuth();
  const { t, i18n } = useTranslation();
  const [page, setPage] = useState("dashboard");

  useEffect(() => {
    document.documentElement.dir = i18n.language === "ar" ? "rtl" : "ltr";
    document.documentElement.lang = i18n.language;
  }, [i18n.language]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-paper text-lg font-bold text-palm">
        {t("loading")}
      </div>
    );
  }

  if (!user) return <LoginPage />;

  const pages = {
    dashboard: <DashboardPage />,
    customers: <CustomersPage />,
    debts: <DebtsPage />,
    settings: <SettingsPage />,
  };

  return (
    <AppShell page={page} setPage={setPage}>
      {pages[page]}
    </AppShell>
  );
}
