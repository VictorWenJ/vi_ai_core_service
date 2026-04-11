import { Navigate, createBrowserRouter } from "react-router-dom";

import { AppLayout } from "@/app/layout/AppLayout";
import { ChatPlaygroundPage } from "@/pages/ChatPlaygroundPage";
import { ChunkInspectorPage } from "@/pages/ChunkInspectorPage";
import { EvaluationDashboardPage } from "@/pages/EvaluationDashboardPage";
import { KnowledgeIngestPage } from "@/pages/KnowledgeIngestPage";
import { RuntimeConfigPage } from "@/pages/RuntimeConfigPage";

export const appRouter = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    children: [
      {
        index: true,
        element: <Navigate to="/chat-playground" replace />,
      },
      {
        path: "chat-playground",
        element: <ChatPlaygroundPage />,
      },
      {
        path: "knowledge-ingest",
        element: <KnowledgeIngestPage />,
      },
      {
        path: "chunk-inspector",
        element: <ChunkInspectorPage />,
      },
      {
        path: "evaluation-dashboard",
        element: <EvaluationDashboardPage />,
      },
      {
        path: "runtime-config",
        element: <RuntimeConfigPage />,
      },
    ],
  },
]);
