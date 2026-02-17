import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";

const API_BASE = "http://127.0.0.1:8000/api";

export default function PatientDetail() {
  const { patientId } = useParams();

  const [patient, setPatient] = useState(null);
  const [files, setFiles] = useState([]);
  const [cases, setCases] = useState([]);

  // NEW - PROM schedule state
  const [promSchedules, setPromSchedules] = useState([]);
  const [promError, setPromError] = useState(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Upload state
  const [uploadFile, setUploadFile] = useState(null);
  const [uploading, setUploading] = useState(false);

  // Create case state
  const [showCaseForm, setShowCaseForm] = useState(false);
  const [creatingCase, setCreatingCase] = useState(false);
  const [caseError, setCaseError] = useState(null);
  const [caseForm, setCaseForm] = useState({
    date_of_surgery: "",
    surgeon_name: "",
    procedure_type: "",
    implant_notes: "",
  });

  // Edit case state
  const [editingCaseId, setEditingCaseId] = useState(null);
  const [editCaseError, setEditCaseError] = useState(null);
  const [savingEdit, setSavingEdit] = useState(false);
  const [editForm, setEditForm] = useState({
    date_of_surgery: "",
    surgeon_name: "",
    procedure_type: "",
    implant_notes: "",
  });

  // Action state for start/stop
  const [actionBusyId, setActionBusyId] = useState(null);
  const [actionError, setActionError] = useState(null);

  async function apiJson(url, options = {}) {
    const res = await fetch(url, options);
    if (!res.ok) {
      const txt = await res.text();
      throw new Error(txt || "Request failed");
    }
    return res.json();
  }

  function badgeStyle(status) {
    const s = (status || "PLANNED").toUpperCase();
    const base = {
      fontSize: 12,
      padding: "3px 8px",
      borderRadius: 999,
      border: "1px solid #ccc",
      display: "inline-block",
      lineHeight: 1.4,
      userSelect: "none",
    };

    if (s === "IN_PROGRESS") return { ...base, borderColor: "#2b6cb0" };
    if (s === "COMPLETED") return { ...base, borderColor: "#2f855a" };
    if (s === "CANCELLED") return { ...base, borderColor: "#c53030" };
    return { ...base, borderColor: "#777" }; // PLANNED
  }

  function formatDuration(minutes) {
    if (minutes === null || minutes === undefined) return "-";
    if (Number.isNaN(Number(minutes))) return "-";
    const m = Number(minutes);
    if (m < 0) return "-";
    const h = Math.floor(m / 60);
    const mm = m % 60;
    if (h <= 0) return `${mm} min`;
    return `${h}h ${mm}m`;
  }

  // NEW - PROM formatting helpers
  function promStatusBadgeStyle(status) {
    const s = (status || "pending").toLowerCase();
    const base = {
      fontSize: 12,
      padding: "3px 8px",
      borderRadius: 999,
      border: "1px solid #ccc",
      display: "inline-block",
      lineHeight: 1.4,
      userSelect: "none",
    };

    if (s === "completed") return { ...base, borderColor: "#2f855a" };
    return { ...base, borderColor: "#777" }; // pending
  }

  function isOverdue(dueDateStr, status) {
    if (!dueDateStr) return false;
    if ((status || "").toLowerCase() === "completed") return false;
    const due = new Date(dueDateStr);
    const today = new Date();
    // compare at day granularity
    due.setHours(0, 0, 0, 0);
    today.setHours(0, 0, 0, 0);
    return due < today;
  }

  useEffect(() => {
    if (!patientId) return;

    async function load() {
      setLoading(true);
      setError(null);
      setPromError(null);

      try {
        // Patient
        const patientData = await apiJson(`${API_BASE}/patients/${patientId}`);
        setPatient(patientData);

        // Files
        try {
          const filesData = await apiJson(
            `${API_BASE}/patient-files/by-patient/${patientId}`
          );
          setFiles(Array.isArray(filesData) ? filesData : []);
        } catch {
          setFiles([]);
        }

        // Cases
        try {
          const casesData = await apiJson(`${API_BASE}/cases/by-patient/${patientId}`);
          setCases(Array.isArray(casesData) ? casesData : []);
        } catch {
          setCases([]);
        }

        // NEW - PROM schedule for patient
        try {
          const sched = await apiJson(`${API_BASE}/proms/schedule/patient/${patientId}`);
          setPromSchedules(Array.isArray(sched) ? sched : []);
        } catch {
          setPromSchedules([]);
          setPromError("Could not load PROM schedule");
        }
      } catch (e) {
        setError("Failed to load patient");
      } finally {
        setLoading(false);
      }
    }

    load();
  }, [patientId]);

  // -----------------------------
  // Upload patient file
  // -----------------------------
  async function handleUpload(e) {
    e.preventDefault();
    if (!uploadFile) return;

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("patient_id", patientId);
      formData.append("uploaded_file", uploadFile);

      const created = await apiJson(`${API_BASE}/patient-files/upload-and-assign`, {
        method: "POST",
        body: formData,
      });

      setFiles((prev) => [...prev, created]);
      setUploadFile(null);
    } catch (e) {
      alert("File upload failed");
    } finally {
      setUploading(false);
    }
  }

  // -----------------------------
  // Create case
  // -----------------------------
  function handleCaseChange(e) {
    setCaseForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  }

  async function handleCreateCase(e) {
    e.preventDefault();
    if (!patient) return;

    setCreatingCase(true);
    setCaseError(null);

    try {
      const payload = {
        patient_id: Number(patientId),
        joint_type: patient.joint_type, // lock to patient
        date_of_surgery: caseForm.date_of_surgery || null,
        surgeon_name: caseForm.surgeon_name || null,
        procedure_type: caseForm.procedure_type || null,
        implant_notes: caseForm.implant_notes || null,
        // Times are captured by backend on Start/Stop
      };

      const createdCase = await apiJson(`${API_BASE}/cases/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      setCases((prev) => [createdCase, ...prev]);

      setShowCaseForm(false);
      setCaseForm({
        date_of_surgery: "",
        surgeon_name: "",
        procedure_type: "",
        implant_notes: "",
      });
    } catch (e) {
      setCaseError("Failed to create case");
    } finally {
      setCreatingCase(false);
    }
  }

  // -----------------------------
  // Edit case (inline)
  // -----------------------------
  function startEditCase(c) {
    setEditCaseError(null);
    setEditingCaseId(c.id);

    setEditForm({
      date_of_surgery: c.date_of_surgery || "",
      surgeon_name: c.surgeon_name || "",
      procedure_type: c.procedure_type || "",
      implant_notes: c.implant_notes || "",
    });
  }

  function cancelEdit() {
    setEditingCaseId(null);
    setEditCaseError(null);
    setSavingEdit(false);
  }

  function handleEditChange(e) {
    setEditForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  }

  async function saveEdit(caseId) {
    setSavingEdit(true);
    setEditCaseError(null);

    try {
      const payload = {
        date_of_surgery: editForm.date_of_surgery || null,
        surgeon_name: editForm.surgeon_name || null,
        procedure_type: editForm.procedure_type || null,
        implant_notes: editForm.implant_notes || null,
      };

      const updated = await apiJson(`${API_BASE}/cases/${caseId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      setCases((prev) => prev.map((c) => (c.id === caseId ? updated : c)));
      setEditingCaseId(null);
    } catch (e) {
      setEditCaseError("Failed to save changes");
    } finally {
      setSavingEdit(false);
    }
  }

  // -----------------------------
  // Start/Stop case actions
  // -----------------------------
  async function startCase(caseId) {
    setActionError(null);
    setActionBusyId(caseId);
    try {
      const updated = await apiJson(`${API_BASE}/cases/${caseId}/start`, {
        method: "POST",
      });
      setCases((prev) => prev.map((c) => (c.id === caseId ? updated : c)));
    } catch (e) {
      setActionError("Failed to start case");
    } finally {
      setActionBusyId(null);
    }
  }

  async function stopCase(caseId) {
    setActionError(null);
    setActionBusyId(caseId);
    try {
      const updated = await apiJson(`${API_BASE}/cases/${caseId}/stop`, {
        method: "POST",
      });
      setCases((prev) => prev.map((c) => (c.id === caseId ? updated : c)));

      // NEW - after Stop, PROM schedule is created by backend, so refresh PROM list
      try {
        const sched = await apiJson(`${API_BASE}/proms/schedule/patient/${patientId}`);
        setPromSchedules(Array.isArray(sched) ? sched : []);
        setPromError(null);
      } catch {
        setPromError("Could not refresh PROM schedule");
      }
    } catch (e) {
      setActionError("Failed to stop case");
    } finally {
      setActionBusyId(null);
    }
  }

  if (loading) return <p>Loading patient...</p>;
  if (error) return <p>{error}</p>;
  if (!patient) return <p>Patient not found</p>;

  // NEW - index PROM schedules by case_id for easy grouping under each case
  const schedulesByCaseId = promSchedules.reduce((acc, row) => {
    const key = String(row.case_id);
    if (!acc[key]) acc[key] = [];
    acc[key].push(row);
    return acc;
  }, {});

  // Sort each case schedule by due date
  Object.keys(schedulesByCaseId).forEach((k) => {
    schedulesByCaseId[k].sort((a, b) => {
      const da = new Date(a.due_date);
      const db = new Date(b.due_date);
      return da - db;
    });
  });

  return (
    <div style={{ maxWidth: "800px" }}>
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

      {/* CASES */}
      <h2 style={{ marginTop: "2rem" }}>Cases</h2>

      <button
        onClick={() => setShowCaseForm((v) => !v)}
        style={{ marginBottom: "1rem" }}
      >
        {showCaseForm ? "Cancel" : "Create Case"}
      </button>

      {showCaseForm && (
        <form onSubmit={handleCreateCase} style={{ marginBottom: "1rem" }}>
          {caseError && <p style={{ color: "red" }}>{caseError}</p>}

          <div style={{ display: "grid", gap: "10px", maxWidth: 520 }}>
            <label>
              Date of surgery
              <input
                name="date_of_surgery"
                type="date"
                value={caseForm.date_of_surgery}
                onChange={handleCaseChange}
                required
              />
            </label>

            <label>
              Surgeon name
              <input
                name="surgeon_name"
                value={caseForm.surgeon_name}
                onChange={handleCaseChange}
                placeholder="Dr X"
              />
            </label>

            <label>
              Procedure type
              <input
                name="procedure_type"
                value={caseForm.procedure_type}
                onChange={handleCaseChange}
                placeholder="TKA / THA / TSA..."
              />
            </label>

            <label>
              Implant notes
              <textarea
                name="implant_notes"
                value={caseForm.implant_notes}
                onChange={handleCaseChange}
                placeholder="Optional"
                rows={3}
              />
            </label>

            <button type="submit" disabled={creatingCase}>
              {creatingCase ? "Creating..." : "Create Case Episode"}
            </button>
          </div>

          <p style={{ marginTop: 8, fontSize: 12, color: "#555" }}>
            Cutting and closing times are captured automatically when you press Start and Stop.
          </p>
        </form>
      )}

      {actionError && <p style={{ color: "red" }}>{actionError}</p>}

      {cases.length === 0 ? (
        <p>No cases yet</p>
      ) : (
        <ul style={{ paddingLeft: "1.2rem" }}>
          {cases.map((c) => {
            const status = (c.case_status || "PLANNED").toUpperCase();
            const busy = actionBusyId === c.id;

            const schedRows = schedulesByCaseId[String(c.id)] || [];

            return (
              <li key={c.id} style={{ marginBottom: "1.1rem" }}>
                <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
                      <strong>Case #{c.id}</strong>
                      <span style={badgeStyle(status)}>{status}</span>
                      <span style={{ fontSize: 12, color: "#555" }}>
                        Duration: {formatDuration(c.duration_minutes)}
                      </span>
                    </div>

                    <div style={{ marginTop: 2 }}>
                      {c.date_of_surgery ?? "-"} · {c.procedure_type ?? "Surgery"}
                      {c.cutting_time ? ` · Cut: ${c.cutting_time}` : ""}
                      {c.closing_time ? ` · Close: ${c.closing_time}` : ""}
                    </div>
                  </div>

                  {/* Start/Stop buttons driven by status */}
                  {status === "PLANNED" && (
                    <button onClick={() => startCase(c.id)} disabled={busy}>
                      {busy ? "Starting..." : "Start"}
                    </button>
                  )}

                  {status === "IN_PROGRESS" && (
                    <button onClick={() => stopCase(c.id)} disabled={busy}>
                      {busy ? "Stopping..." : "Stop"}
                    </button>
                  )}

                  <button onClick={() => startEditCase(c)} disabled={busy}>
                    Edit
                  </button>
                </div>

                {/* NEW - PROM schedule under the case */}
                {schedRows.length > 0 && (
                  <div style={{ marginTop: 10, padding: "10px", border: "1px solid #eee" }}>
                    <div style={{ fontWeight: 600, marginBottom: 6 }}>PROM Schedule</div>

                    <div style={{ overflowX: "auto" }}>
                      <table style={{ width: "100%", borderCollapse: "collapse" }}>
                        <thead>
                          <tr>
                            <th style={{ textAlign: "left", padding: "6px 4px", borderBottom: "1px solid #eee" }}>
                              Due
                            </th>
                            <th style={{ textAlign: "left", padding: "6px 4px", borderBottom: "1px solid #eee" }}>
                              PROM
                            </th>
                            <th style={{ textAlign: "left", padding: "6px 4px", borderBottom: "1px solid #eee" }}>
                              Status
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          {schedRows.map((row) => {
                            const overdue = isOverdue(row.due_date, row.status);
                            return (
                              <tr key={row.id}>
                                <td style={{ padding: "6px 4px", borderBottom: "1px solid #f3f3f3" }}>
                                  <span style={{ color: overdue ? "#c53030" : "inherit" }}>
                                    {row.due_date}
                                    {overdue ? " (overdue)" : ""}
                                  </span>
                                </td>
                                <td style={{ padding: "6px 4px", borderBottom: "1px solid #f3f3f3" }}>
                                  {row.prom_name}
                                </td>
                                <td style={{ padding: "6px 4px", borderBottom: "1px solid #f3f3f3" }}>
                                  <span style={promStatusBadgeStyle(row.status)}>
                                    {(row.status || "pending").toLowerCase()}
                                  </span>
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>

                    <div style={{ marginTop: 6, fontSize: 12, color: "#666" }}>
                      Next step later: add a "Complete PROM" button for pending items.
                    </div>
                  </div>
                )}

                {editingCaseId === c.id && (
                  <div style={{ marginTop: "0.75rem", padding: "10px", border: "1px solid #ddd" }}>
                    {editCaseError && <p style={{ color: "red" }}>{editCaseError}</p>}

                    <div style={{ display: "grid", gap: "10px", maxWidth: 520 }}>
                      <label>
                        Date of surgery
                        <input
                          name="date_of_surgery"
                          type="date"
                          value={editForm.date_of_surgery}
                          onChange={handleEditChange}
                        />
                      </label>

                      <label>
                        Surgeon name
                        <input
                          name="surgeon_name"
                          value={editForm.surgeon_name}
                          onChange={handleEditChange}
                        />
                      </label>

                      <label>
                        Procedure type
                        <input
                          name="procedure_type"
                          value={editForm.procedure_type}
                          onChange={handleEditChange}
                        />
                      </label>

                      <label>
                        Implant notes
                        <textarea
                          name="implant_notes"
                          value={editForm.implant_notes}
                          onChange={handleEditChange}
                          rows={3}
                        />
                      </label>

                      <div style={{ display: "flex", gap: "10px" }}>
                        <button type="button" onClick={() => saveEdit(c.id)} disabled={savingEdit}>
                          {savingEdit ? "Saving..." : "Save"}
                        </button>
                        <button type="button" onClick={cancelEdit} disabled={savingEdit}>
                          Cancel
                        </button>
                      </div>

                      <p style={{ marginTop: 4, fontSize: 12, color: "#555" }}>
                        Times and status are controlled by Start and Stop.
                      </p>
                    </div>
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      )}

      {/* PROM Schedule summary for patient (optional top-level) */}
      <h2 style={{ marginTop: "2rem" }}>PROMs</h2>
      {promError && <p style={{ color: "red" }}>{promError}</p>}
      {promSchedules.length === 0 ? (
        <p style={{ color: "#666" }}>No PROM schedule yet. Complete a case to generate it.</p>
      ) : (
        <p style={{ color: "#666" }}>
          Total scheduled PROMs: <strong>{promSchedules.length}</strong>
        </p>
      )}

      {/* FILES */}
      <h2 style={{ marginTop: "2rem" }}>Patient Files</h2>

      <form onSubmit={handleUpload} style={{ marginBottom: "1rem" }}>
        <input
          type="file"
          onChange={(e) => setUploadFile(e.target.files?.[0] ?? null)}
        />
        <button type="submit" disabled={uploading || !uploadFile}>
          {uploading ? "Uploading..." : "Upload File"}
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
