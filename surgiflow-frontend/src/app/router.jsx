import { createBrowserRouter, Navigate } from "react-router-dom";
import AppLayout from "./layout/AppLayout";

import Dashboard from "./pages/Dashboard";
import Patients from "./pages/Patients";
import PatientDetail from "./pages/PatientDetail";
import CreatePatient from "./pages/CreatePatient";

export const router = createBrowserRouter([
  {
    element: <AppLayout />,
    children: [
      { path: "/", element: <Navigate to="/dashboard" /> },
      { path: "/dashboard", element: <Dashboard /> },
      { path: "/patients", element: <Patients /> },
      { path: "/patients/new", element: <CreatePatient /> },
      { path: "/patients/:id", element: <PatientDetail /> },
    ],
  },
]);
