import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";

const API_BASE = "http://127.0.0.1:8000/api";

export default function PatientDetail() {
  const { patientId } = useParams();

  const [patient, setPatient] = useState(null);
  const [files, setFiles] = useState([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [uploadFile, setUploadFile] = useState(null);
  const [uploading, setUploading] = useState(false);

  // --------------------------------------------------
  // Load patient + files
  // --------------------------------------------------
  useEffect(() => {
    if (!patientId) return;

    async function load() {
      try {
        setLoading(true);
        setError(null);

        const patientRes = await fetch(`${API_BASE}/patients/${patientId}`);
        if (!patientRes.ok) throw new Error("Failed to load patient");
        const patientData = await patientRes.json();
        setPatient(patientData);

        const filesRes = await fetch(
          `${API_BASE}/patient-files/by-patient/${patientId}`
        );
        if (!filesRes.ok) throw new Error("Failed to load files");
        const filesData = await filesRes.json();
        setFiles(filesData);
      } catch (err) {
        setError("Failed to load patient");
      } finally {
        setLoading(false);
      }
    }

    load();
  }, [patientId]);

  // --------------------------------------------------
  // Upload + assign handler
  // --------------------------------------------------
  async function handleUpload(e) {
    e.preventDefault();
    if (!uploadFile) return;

    setUploading(true);

    try {
      const formData = new FormData();
      formData.append("patient_id", patientId);
      formData.append("uploaded_file", uploadFile);

      const res = await fetch(
        `${API_BASE}/patient-files/upload-and-assign`,
        {
          method: "POST",
          body: formData,
        }
      );

      if (!res.ok) throw new Error("Upload failed");

      const newFile = await res.json();
      setFiles((prev) => [...prev, newFile]);
      setUploadFile(null);
    } catch (err) {
      alert("File upload failed");
    } finally {
      setUploading(false);
    }
  }

  // --------------------------------------------------
  // Render states
  // --------------------------------------------------
  if (loading) return <p>Loading patient…</p>;
  if (error) return <p>{error}</p>;
  if (!patient) return <p>Patient not found</p>;

  return (
    <div style={{ maxWidth: "700px" }}>
      <h1>{patient.preferred_name || patient.full_name}</h1>
      <p>
        {patient.joint_type ?? "-"} · {patient.age ?? "-"} ·{" "}
        {patient.sex ?? "-"}
      </p>

      {/* ---------------- Patient Details ---------------- */}
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

      {/* ---------------- Patient Files ---------------- */}
      <h2 style={{ marginTop: "2.5rem" }}>Patient Files</h2>

      <form onSubmit={handleUpload} style={{ marginBottom: "1rem" }}>
        <input
          type="file"
          onChange={(e) => setUploadFile(e.target.files[0])}
        />
        <button type="submit" disabled={uploading}>
          {uploading ? "Uploading…" : "Upload File"}
        </button>
      </form>

      {files.length === 0 ? (
        <p>No files uploaded</p>
      ) : (
        <ul>
          {files.map((f) => (
            <li key={f.id}>{f.filename}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
