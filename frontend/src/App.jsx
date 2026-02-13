import { BrowserRouter, Route, Routes } from "react-router-dom";

import { Layout } from "./components/Layout";
import { HomePage } from "./pages/HomePage";
import { HistoryPage } from "./pages/HistoryPage";
import { PushPage } from "./pages/PushPage";
import { StrategiesPage } from "./pages/StrategiesPage";
import { ROUTER_FUTURE } from "./routerFuture";

export default function App() {
  return (
    <BrowserRouter future={ROUTER_FUTURE}>
      <Layout>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/market/history" element={<HistoryPage />} />
          <Route path="/market/push" element={<PushPage />} />
          <Route path="/strategies" element={<StrategiesPage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}
