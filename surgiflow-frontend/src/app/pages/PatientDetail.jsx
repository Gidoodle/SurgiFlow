import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";

const API_BASE = "http://127.0.0.1:8000/api";

export default function PatientDetail() {
  const { patientId } = useParams();

  const [patient, setPatient] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!patientId) return;

    setLoading(true);
    setError(null);

    fetch(`${API_BASE}/patients/${patientId}`)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to load patient");
        return res.json();
      })
      .then((data) => {
        setPatient(data);
      })
      .catch(() => {
        setError("Failed to load patient");
      })
      .finally(() => {
        setLoading(false);
      });
  }, [patientId]);

  if (loading) return <p>Loading patient…</p>;
  if (error) return <p>{error}</p>;
  if (!patient) return <p>Patient not found</p>;

  return (
    <div style={{ maxWidth: "700px" }}>
      <h1>{patient.preferred_name || patient.full_name}</h1>
      <p>
        {patient.joint_type ?? "-"} · {patient.age ?? "-"} · {patient.sex ?? "-"}
      </p>

      <h2 style={{ marginTop: "2rem" }}>Patient Details</h2>

      <table>
        <tbody>
          <tr><td><strong>Full name</strong></td><td>{patient.full_name}</td></tr>
          <tr><td><strong>Preferred name</strong></td><td>{patient.preferred_name || "-"}</td></tr>
          <tr><td><strong>Age</strong></td><td>{patient.age ?? "-"}</td></tr>
          <tr><td><strong>Sex</strong></td><td>{patient.sex ?? "-"}</td></tr>
          <tr><td><strong>Joint</strong></td><td>{patient.joint_type ?? "-"}</td></tr>
          <tr><td><strong>Phone</strong></td><td>{patient.phone || "-"}</td></tr>
          <tr><td><strong>Email</strong></td><td>{patient.email || "-"}</td></tr>
          <tr><td><strong>ID number</strong></td><td>{patient.id_number || "-"}</td></tr>
          <tr><td><strong>Medical aid</strong></td><td>{patient.medical_aid || "-"}</td></tr>
          <tr><td><strong>Medical aid #</strong></td><td>{patient.medical_aid_number || "-"}</td></tr>
          <tr><td><strong>Address</strong></td><td>{patient.address || "-"}</td></tr>
        </tbody>
      </table>
    </div>
  );
}
