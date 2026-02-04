import { useState } from "react";
import { useNavigate } from "react-router-dom";

const API_BASE = "http://127.0.0.1:8000/api";

export default function CreatePatient() {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    full_name: "",
    preferred_name: "",
    id_number: "",
    email: "",
    phone: "",
    address: "",
    age: "",
    sex: "",
    joint_type: "",
    medical_aid: "",
    medical_aid_number: "",
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  function handleChange(e) {
    setForm({ ...form, [e.target.name]: e.target.value });
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/patients/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("axiom_token")}`,
        },
        body: JSON.stringify(form),
      });

      if (!res.ok) {
        throw new Error(await res.text());
      }

      const patient = await res.json();

      // patient.id EXISTS here
      navigate(`/patients/${patient.id}`);
    } catch (err) {
      console.error(err);
      setError("Failed to create patient");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ maxWidth: 600 }}>
      <h1>New Patient</h1>

      {error && <p style={{ color: "red" }}>{error}</p>}

      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        <input name="full_name" placeholder="Full name *" required onChange={handleChange} />
        <input name="preferred_name" placeholder="Preferred name" onChange={handleChange} />
        <input name="id_number" placeholder="ID number" onChange={handleChange} />
        <input name="email" placeholder="Email" onChange={handleChange} />
        <input name="phone" placeholder="Phone" onChange={handleChange} />
        <input name="address" placeholder="Address" onChange={handleChange} />
        <input name="age" type="number" placeholder="Age" onChange={handleChange} />
        <input name="sex" placeholder="Sex (m/f)" onChange={handleChange} />
        <input name="joint_type" placeholder="Joint (Knee, Hip, Shoulder) *" required onChange={handleChange} />
        <input name="medical_aid" placeholder="Medical aid" onChange={handleChange} />
        <input name="medical_aid_number" placeholder="Medical aid number" onChange={handleChange} />

        <button type="submit" disabled={loading}>
          {loading ? "Creating…" : "Create Patient"}
        </button>
      </form>
    </div>
  );
}
