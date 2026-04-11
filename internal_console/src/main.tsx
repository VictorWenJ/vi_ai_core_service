import React from "react";
import ReactDOM from "react-dom/client";

import App from "@/App";
import { AppConfigProvider } from "@/app/providers/AppConfigProvider";
import { AppQueryProvider } from "@/app/providers/QueryProvider";
import "@/styles/global.css";

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <AppConfigProvider>
      <AppQueryProvider>
        <App />
      </AppQueryProvider>
    </AppConfigProvider>
  </React.StrictMode>,
);
