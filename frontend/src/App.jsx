import { useEffect, useState } from "react";
import { getToken, warmupBackend } from "./api/client";
import { Layout } from "./components/Layout";
import { Auth } from "./pages/Auth";
import { Dashboard } from "./pages/Dashboard";

export default function App() {
  const [authed, setAuthed] = useState(Boolean(getToken()));

  useEffect(() => {
    warmupBackend();
  }, []);

  return (
    <Layout onLogout={() => setAuthed(false)}>
      {authed ? <Dashboard /> : <Auth onAuthed={() => setAuthed(true)} />}
    </Layout>
  );
}
