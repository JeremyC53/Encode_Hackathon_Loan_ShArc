// App.tsx
import { useState } from "react";
import type { User, View } from "./types";
import LoginScreen from "./components/LoginScreen";
import MainLayout from "./components/MainLayout";
import DashboardScreen from "./screens/DashboardScreen";
import LoansScreen from "./screens/LoansScreen";
import SettingsScreen from "./screens/SettingsScreen";
import EarningsScreen from "./screens/EarningsScreen"; // 👈 NEW

export default function App() {
  const [user, setUser] = useState<User | null>(null);
  const [view, setView] = useState<View>("dashboard");

  if (!user) {
    return <LoginScreen onLogin={setUser} />;
  }

  let content;
  switch (view) {
    case "loans":
      content = <LoansScreen />;
      break;
    case "settings":
      content = <SettingsScreen />;
      break;
    case "earnings":
      content = <EarningsScreen />;
      break;
    case "dashboard":
    default:
      content = <DashboardScreen />;
  }

  return (
    <MainLayout
      user={user}
      currentView={view}
      onChangeView={setView}
      onLogout={() => {
        setUser(null);
        setView("dashboard");
      }}
    >
      {content}
    </MainLayout>
  );
}
