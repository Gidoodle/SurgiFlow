import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import { apiGet } from "../../api/client";

export default function PatientDetail() {
  const { id } = useParams();

  const [patient, setPatient] = useState(null);
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      apiGet("/patients/"),
      apiGet(`/cases/by-patient/${id}`)
    ])
      .then(([patients, cases]) => {
        const p = patients.find(x => x.id === Number(id));
        setPatient(p);
        setCases(cases);
      })
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <p>Loading patient…</p>;
  if (!patient) return <p>Patient not found</p>;

  return (
    <div>
      <h1>{patient.full_name}</h1>
      <p>{patient.joint_type} · {patient.age} · {patient.sex}</p>

      <h2>Cases</h2>
      {!cases.length && <p>No cases yet</p>}
      <ul>
        {cases.map(c => (
          <li key={c.id}>
            Case #{c.id} – {c.case_type || "Surgery"}
          </li>
        ))}
      </ul>
    </div>
  );
}
