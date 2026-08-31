import { BrowserRouter, Routes, Route } from "react-router-dom";

import Layout from "./components/Layout.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Exceptions from "./pages/Exceptions.jsx";
import Runs from "./pages/Runs.jsx";

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route
            path="/exceptions"
            element={<Exceptions />}
          />
          <Route path="/runs" element={<Runs />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;