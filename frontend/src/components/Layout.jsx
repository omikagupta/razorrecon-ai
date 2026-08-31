import Sidebar from "./Sidebar";

function Layout({ children }) {
  return (
    <div className="app-layout">
      <Sidebar />

      <main className="main-content">
        <header className="topbar">
          <div>
            <p className="breadcrumb">
              Financial Operations / Reconciliation
            </p>
          </div>

          <div className="topbar-right">
            <div className="environment-badge">
              AI SYSTEM
            </div>

            <div className="user-avatar">
              O
            </div>
          </div>
        </header>

        <section className="page-content">
          {children}
        </section>
      </main>
    </div>
  );
}

export default Layout;