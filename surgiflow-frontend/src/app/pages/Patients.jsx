import { useEffect, useState } from "react";
import { apiGet } from "../../api/client";
import { Link } from "react-router-dom";

export default function Patients() {
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    apiGet("/patients/")
      .then(setPatients)
      .catch(() => setError("Failed to load patients"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p>Loading patients…</p>;
  if (error) return <p>{error}</p>;
  if (!patients.length) return <p>No patients yet</p>;

  return (
    <div>
      <h1>Patients</h1>
      <ul>
        {patients.map((p) => (
          <li key={p.id}>
            <Link to={`/patients/${p.id}`}>
              {p.preferred_name || p.full_name} – {p.joint_type}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
