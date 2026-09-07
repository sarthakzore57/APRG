import { useState } from "react";
import { getToken } from "./api/client";
import { Layout } from "./components/Layout";
import { Auth } from "./pages/Auth";
import { Dashboard } from "./pages/Dashboard";

export default function App() {
  const [authed, setAuthed] = useState(Boolean(getToken()));
  return (
    <Layout onLogout={() => setAuthed(false)}>
      {authed ? <Dashboard /> : <Auth onAuthed={() => setAuthed(true)} />}
    </Layout>
  );
}
