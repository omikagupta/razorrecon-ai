import { BrowserRouter, Routes, Route } from "react-router-dom";

import Layout from "./components/Layout.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Exceptions from "./pages/Exceptions.jsx";
import ExceptionDetails from "./pages/ExceptionDetails.jsx";
import Runs from "./pages/Runs.jsx";
import RunDetails from "./pages/RunDetails.jsx";

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          {/* Dashboard */}
          <Route
            path="/"
            element={<Dashboard />}
          />

          {/* Exceptions */}
          <Route
            path="/exceptions"
            element={<Exceptions />}
          />

          <Route
            path="/exceptions/:exceptionId"
            element={<ExceptionDetails />}
          />

          {/* Reconciliation Runs */}
          <Route
            path="/runs"
            element={<Runs />}
          />

          <Route
            path="/runs/:runId"
            element={<RunDetails />}
          />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;