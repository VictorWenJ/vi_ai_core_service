import { createBrowserRouter } from "react-router-dom";

import { AppLayout } from "@/app/layout/AppLayout";
import { ChatPlaygroundPage } from "@/pages/ChatPlaygroundPage";

export const appRouter = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    children: [
      {
        index: true,
        element: <ChatPlaygroundPage />,
      },
    ],
  },
]);
