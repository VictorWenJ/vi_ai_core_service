import { Link, Outlet } from "react-router-dom";
import { useAppConfig } from "@/hooks/useAppConfig";

export function AppLayout(): JSX.Element {
  const appConfig = useAppConfig();

  return (
    <div className="shell">
      <aside className="sidebar">
        <h1>VI AI Console</h1>
        <nav>
          <Link to="/">Chat Playground</Link>
        </nav>
      </aside>

      <div className="main-pane">
        <header className="topbar">
          <div>
            <h2>Internal Console</h2>
            <p>Dev / Ops interface for `vi_ai_core_service`</p>
            <p className="muted">API Base URL: {appConfig.apiBaseUrl}</p>
          </div>
        </header>
        <main className="content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
