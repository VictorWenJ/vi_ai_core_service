import { NavLink, Outlet } from "react-router-dom";
import { useAppConfig } from "@/hooks/useAppConfig";

export function AppLayout(): JSX.Element {
  const appConfig = useAppConfig();
  const navClassName = ({ isActive }: { isActive: boolean }): string | undefined =>
    isActive ? "active" : undefined;

  return (
    <div className="shell">
      <aside className="sidebar">
        <h1>VI AI Console</h1>
        <nav>
          <NavLink to="/chat-playground" className={navClassName}>
            Chat Playground
          </NavLink>
          <NavLink to="/knowledge-ingest" className={navClassName}>
            Knowledge Ingest
          </NavLink>
          <NavLink to="/chunk-inspector" className={navClassName}>
            Chunk Inspector
          </NavLink>
          <NavLink to="/evaluation-dashboard" className={navClassName}>
            Evaluation Dashboard
          </NavLink>
          <NavLink to="/runtime-config" className={navClassName}>
            Runtime Config
          </NavLink>
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
