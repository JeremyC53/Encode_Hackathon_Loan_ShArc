// components/MainLayout.tsx
import React from "react";
import type { User, View } from "../types";

type MainLayoutProps = {
  user: User;
  currentView: View;
  onChangeView: (view: View) => void;
  onLogout: () => void;
  children: React.ReactNode;
};

const MainLayout: React.FC<MainLayoutProps> = ({
  user,
  currentView,
  onChangeView,
  onLogout,
  children,
}) => {
  const navItems: { id: View; label: string }[] = [
    { id: "dashboard", label: "Dashboard" },
    { id: "loans", label: "Loans" },
    { id: "settings", label: "Settings" },
  ];

  return (
    <div style={styles.app}>
      <aside style={styles.sidebar}>
        <div style={styles.logo}>Hackathon Bank</div>

        <nav style={styles.nav}>
          {navItems.map((item) => (
            <button
                key={item.id}
                type="button"
                onClick={() => onChangeView(item.id)}
                style={{
                ...styles.navItem,
                ...(currentView === item.id ? styles.navItemActive : {})
                }}
            >
                {item.label}
            </button>
            ))}
        </nav>

        <div style={styles.footer}>
          <div style={styles.userEmail}>{user.email}</div>
          <button style={styles.logoutButton} onClick={onLogout}>
            Log out
          </button>
        </div>
      </aside>

      <main style={styles.main}>{children}</main>
    </div>
  );
};

const styles: { [key: string]: React.CSSProperties } = {
  app: {
    display: "flex",
    minHeight: "100vh",
    backgroundColor: "#0f172a",
  },
  sidebar: {
    width: 240,
    backgroundColor: "#020617",
    color: "#e5e7eb",
    display: "flex",
    flexDirection: "column",
    padding: "20px 16px",
    boxSizing: "border-box",
    gap: 16,
  },
  logo: {
    fontSize: 20,
    fontWeight: 700,
    marginBottom: 8,
  },
  nav: {
    display: "flex",
    flexDirection: "column",
    gap: 8,
    marginTop: 8,
  },
  navItem: {
    textAlign: "left",
    borderRadius: 999,
    padding: "10px 16px",
    fontSize: 14,
    cursor: "pointer",

    // base (inactive) look
    appearance: "none",
    WebkitAppearance: "none",
    background: "transparent",
    border: "none",
    color: "white",

    // kill default button focus styles
    outline: "none",
    boxShadow: "none",
  },

    navItemActive: {
        background:
            "linear-gradient(135deg, rgba(59,130,246,0.95), rgba(79,70,229,0.95))",
        color: "#ffffff",
    },

  footer: {
    marginTop: "auto",
    borderTop: "1px solid rgba(148, 163, 184, 0.2)",
    paddingTop: 12,
    display: "flex",
    flexDirection: "column",
    gap: 8,
    fontSize: 12,
  },
  userEmail: {
    color: "#9ca3af",
  },
  logoutButton: {
    alignSelf: "flex-start",
    borderRadius: 999,
    border: "1px solid rgba(148,163,184,0.6)",
    backgroundColor: "transparent",
    color: "#e5e7eb",
    padding: "4px 10px",
    fontSize: 12,
    cursor: "pointer",
  },
  main: {
    flex: 1,
    backgroundColor: "#0b1120",
    color: "#e5e7eb",
    padding: "24px 28px",
    boxSizing: "border-box",
  },
};

export default MainLayout;
