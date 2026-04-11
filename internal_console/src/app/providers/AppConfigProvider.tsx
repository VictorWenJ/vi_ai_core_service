import { createContext, useMemo, useContext, type PropsWithChildren } from "react";
import { appEnvConfig, type AppEnvConfig } from "@/config/env";

const AppConfigContext = createContext<AppEnvConfig | null>(null);

export function AppConfigProvider({
  children,
}: PropsWithChildren): JSX.Element {
  const config = useMemo(() => appEnvConfig, []);
  return (
    <AppConfigContext.Provider value={config}>
      {children}
    </AppConfigContext.Provider>
  );
}

export function useAppConfigContext(): AppEnvConfig {
  const context = useContext(AppConfigContext);
  if (!context) {
    throw new Error("AppConfigProvider is missing in component tree.");
  }
  return context;
}
