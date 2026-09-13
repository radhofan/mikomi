import React, { useState, useEffect, useCallback } from "react"

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000"

const EXAMPLE_BATCH_JSON = JSON.stringify(
  [
    {
      name: "Alex Mercer",
      email: "alex.mercer@apex.io",
      phone: "+14155552671",
      company: "Apex Corp",
      country: "United States",
      message: "Interested in enterprise pricing"
    },
    {
      name: "Sarah Connor",
      email: "sarah.c@cyberdyne.com",
      phone: "+14155559812",
      company: "Cyberdyne Systems",
      country: "United States",
      message: "Requesting a demo"
    }
  ],
  null,
  2
)

export default function App() {
  const [activeTab, setActiveTab] = useState("leads")

  // Dashboard metrics
  const [dashboard, setDashboard] = useState(null)
  const [dashLoading, setDashLoading] = useState(false)

  // Leads list
  const [leads, setLeads] = useState([])
  const [loadingLeads, setLoadingLeads] = useState(false)
  const [statusFilter, setStatusFilter] = useState("")
  const [ownerFilter, setOwnerFilter] = useState("")
  const [countryFilter, setCountryFilter] = useState("")
  const [searchQuery, setSearchQuery] = useState("")
  const [pageOffset, setPageOffset] = useState(0)
  const [totalCount, setTotalCount] = useState(0)
  const pageLimit = 25

  // Edit lead modal
  const [editingLead, setEditingLead] = useState(null)
  const [editStatus, setEditStatus] = useState("")
  const [editOwner, setEditOwner] = useState("")
  const [editNotes, setEditNotes] = useState("")
  const [savingEdit, setSavingEdit] = useState(false)

  // Deduplication
  const [dedupThreshold, setDedupThreshold] = useState(0.5)
  const [dedupLimit, setDedupLimit] = useState("")
  const [dedupClusters, setDedupClusters] = useState([])
  const [dedupPage, setDedupPage] = useState(1)
  const dedupPageSize = 3
  const [loadingDedup, setLoadingDedup] = useState(false)
  const [dedupError, setDedupError] = useState("")

  // Source extraction
  const [extractText, setExtractText] = useState("")
  const [extractResult, setExtractResult] = useState(null)
  const [loadingExtract, setLoadingExtract] = useState(false)
  const [extractError, setExtractError] = useState("")

  // Ingest form
  const [ingestName, setIngestName] = useState("")
  const [ingestEmail, setIngestEmail] = useState("")
  const [ingestPhone, setIngestPhone] = useState("")
  const [ingestCompany, setIngestCompany] = useState("")
  const [ingestCountry, setIngestCountry] = useState("")
  const [ingestMessage, setIngestMessage] = useState("")
  const [ingestResult, setIngestResult] = useState(null)
  const [loadingIngest, setLoadingIngest] = useState(false)
  const [ingestError, setIngestError] = useState("")

  // Batch Ingest
  const [batchJson, setBatchJson] = useState("")
  const [loadingBatch, setLoadingBatch] = useState(false)
  const [batchError, setBatchError] = useState("")
  const [batchResult, setBatchResult] = useState(null)

  // Fetch Dashboard
  const fetchDashboard = useCallback(async () => {
    setDashLoading(true)
    try {
      const res = await fetch(`${API_BASE}/dashboard`)
      if (res.ok) {
        const data = await res.json()
        setDashboard(data)
      }
    } catch {
      // API unavailable or booting up
    } finally {
      setDashLoading(false)
    }
  }, [])

  // Fetch Leads
  const fetchLeads = useCallback(async () => {
    setLoadingLeads(true)
    try {
      const params = new URLSearchParams()
      if (statusFilter) params.append("status", statusFilter)
      if (ownerFilter) params.append("owner", ownerFilter)
      if (countryFilter) params.append("country", countryFilter)
      if (searchQuery) params.append("q", searchQuery)
      params.append("limit", String(pageLimit))
      params.append("offset", String(pageOffset))

      const res = await fetch(`${API_BASE}/leads?${params.toString()}`)
      if (res.ok) {
        const totalHeader = res.headers.get("x-total-count") || res.headers.get("X-Total-Count")
        if (totalHeader) {
          setTotalCount(parseInt(totalHeader, 10))
        } else if (dashboard?.total_leads) {
          setTotalCount(dashboard.total_leads)
        }
        const data = await res.json()
        setLeads(data)
      }
    } catch {
      setLeads([])
    } finally {
      setLoadingLeads(false)
    }
  }, [statusFilter, ownerFilter, countryFilter, searchQuery, pageOffset, dashboard?.total_leads])

  useEffect(() => {
    fetchDashboard()
  }, [fetchDashboard])

  useEffect(() => {
    if (dashboard?.total_leads && totalCount === 0) {
      setTotalCount(dashboard.total_leads)
    }
  }, [dashboard?.total_leads, totalCount])

  useEffect(() => {
    if (activeTab === "leads") {
      fetchLeads()
    }
  }, [activeTab, fetchLeads])

  // Save Lead Updates
  const handleSaveEdit = async () => {
    if (!editingLead) return
    setSavingEdit(true)
    try {
      const res = await fetch(`${API_BASE}/leads/${editingLead.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          lead_status: editStatus || undefined,
          contact_owner: editOwner || undefined,
          notes: editNotes || undefined
        })
      })
      if (res.ok) {
        setEditingLead(null)
        fetchLeads()
        fetchDashboard()
      }
    } finally {
      setSavingEdit(false)
    }
  }

  // Run Deduplication
  const handleRunDedup = async () => {
    setLoadingDedup(true)
    setDedupError("")
    try {
      const params = new URLSearchParams({
        threshold: String(dedupThreshold)
      })
      if (dedupLimit) {
        params.append("limit", String(dedupLimit))
      }
      const res = await fetch(`${API_BASE}/leads/dedupe-candidates?${params.toString()}`, {
        method: "POST"
      })
      if (res.ok) {
        const data = await res.json()
        setDedupClusters(data)
        setDedupPage(1)
      } else {
        setDedupError(`Server responded with ${res.status}`)
      }
    } catch (err) {
      setDedupError(err.message || "Failed to run deduplication")
    } finally {
      setLoadingDedup(false)
    }
  }

  // Run Source Extraction
  const handleExtract = async () => {
    if (!extractText.trim()) return
    setLoadingExtract(true)
    setExtractError("")
    setExtractResult(null)
    try {
      const res = await fetch(`${API_BASE}/leads/source-extract`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: extractText })
      })
      if (res.ok) {
        const data = await res.json()
        setExtractResult(data)
      } else {
        const errJson = await res.json().catch(() => ({}))
        setExtractError(errJson.detail || `Error: ${res.status}`)
      }
    } catch (err) {
      setExtractError(err.message || "Failed to extract source")
    } finally {
      setLoadingExtract(false)
    }
  }

  // Handle Form Ingest
  const handleIngest = async (e) => {
    e.preventDefault()
    setLoadingIngest(true)
    setIngestError("")
    setIngestResult(null)
    try {
      const res = await fetch(`${API_BASE}/leads/ingest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: ingestName,
          email: ingestEmail,
          phone: ingestPhone || undefined,
          company: ingestCompany || undefined,
          country: ingestCountry || undefined,
          message: ingestMessage || undefined
        })
      })
      if (res.ok) {
        const data = await res.json()
        setIngestResult(data)
        fetchDashboard()
      } else {
        setIngestError(`Ingest failed with status ${res.status}`)
      }
    } catch (err) {
      setIngestError(err.message || "Failed to ingest lead")
    } finally {
      setLoadingIngest(false)
    }
  }

  // Handle Batch Ingest
  const handleBatchIngest = async (e) => {
    e.preventDefault()
    setLoadingBatch(true)
    setBatchError("")
    setBatchResult(null)
    try {
      let parsed
      try {
        parsed = JSON.parse(batchJson)
      } catch {
        setBatchError("Invalid JSON syntax. Please verify the JSON format.")
        setLoadingBatch(false)
        return
      }
      if (!Array.isArray(parsed)) {
        setBatchError("JSON payload must be an array of lead objects.")
        setLoadingBatch(false)
        return
      }
      const res = await fetch(`${API_BASE}/leads/ingest`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(parsed)
      })
      if (res.ok) {
        const data = await res.json()
        setBatchResult(data)
        fetchDashboard()
      } else {
        const errJson = await res.json().catch(() => ({}))
        setBatchError(errJson.detail ? JSON.stringify(errJson.detail) : `Batch ingest failed with status ${res.status}`)
      }
    } catch (err) {
      setBatchError(err.message || "Failed to submit batch ingest")
    } finally {
      setLoadingBatch(false)
    }
  }

  const exportUrl = `${API_BASE}/leads/export?${new URLSearchParams({
    status: statusFilter,
    owner: ownerFilter,
    country: countryFilter,
    q: searchQuery
  }).toString()}`

  const currentPage = Math.floor(pageOffset / pageLimit) + 1
  const effectiveTotal = totalCount || (leads.length ? pageOffset + leads.length : 0)
  const totalPages = Math.max(1, Math.ceil(effectiveTotal / pageLimit))

  return (
    <div className="container">
      <header>
        <h1>AI-Assisted Lead Management</h1>
        <p>HubSpot replacement prototype with probabilistic deduplication and AI source extraction</p>
      </header>

      {/* Top Dashboard Metrics */}
      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-title">
            Total Leads <span style={{ color: "var(--text-secondary)", fontSize: "11px", fontWeight: "normal", textTransform: "none", marginLeft: "6px" }}>[GET /dashboard]</span>
          </div>
          <div className="kpi-value">{dashboard ? dashboard.total_leads : "-"}</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-title">
            Qualified Leads <span style={{ color: "var(--text-secondary)", fontSize: "11px", fontWeight: "normal", textTransform: "none", marginLeft: "6px" }}>[GET /dashboard]</span>
          </div>
          <div className="kpi-value">{dashboard?.by_status?.Qualified || 0}</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-title">
            Opportunity <span style={{ color: "var(--text-secondary)", fontSize: "11px", fontWeight: "normal", textTransform: "none", marginLeft: "6px" }}>[GET /dashboard]</span>
          </div>
          <div className="kpi-value">{dashboard?.by_status?.Opportunity || 0}</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-title">
            Closed Won <span style={{ color: "var(--text-secondary)", fontSize: "11px", fontWeight: "normal", textTransform: "none", marginLeft: "6px" }}>[GET /dashboard]</span>
          </div>
          <div className="kpi-value">{dashboard?.by_status?.["Closed Won"] || 0}</div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="nav-tabs">
        <button
          className={`tab-btn ${activeTab === "leads" ? "active" : ""}`}
          onClick={() => setActiveTab("leads")}
        >
          Leads Directory <span style={{ color: "#94a3b8", fontSize: "11px", fontWeight: "normal", marginLeft: "6px" }}>[GET /leads]</span>
        </button>
        <button
          className={`tab-btn ${activeTab === "dedup" ? "active" : ""}`}
          onClick={() => setActiveTab("dedup")}
        >
          AI Deduplication <span style={{ color: "#94a3b8", fontSize: "11px", fontWeight: "normal", marginLeft: "6px" }}>[POST /leads/dedupe-candidates]</span>
        </button>
        <button
          className={`tab-btn ${activeTab === "extract" ? "active" : ""}`}
          onClick={() => setActiveTab("extract")}
        >
          AI Source Extraction <span style={{ color: "#94a3b8", fontSize: "11px", fontWeight: "normal", marginLeft: "6px" }}>[POST /leads/source-extract]</span>
        </button>
        <button
          className={`tab-btn ${activeTab === "ingest" ? "active" : ""}`}
          onClick={() => setActiveTab("ingest")}
        >
          Website Ingest <span style={{ color: "#94a3b8", fontSize: "11px", fontWeight: "normal", marginLeft: "6px" }}>[POST /leads/ingest]</span>
        </button>
      </div>

      {/* Tab 1: Leads Directory */}
      {activeTab === "leads" && (
        <div className="panel">
          <div className="filter-bar">
            <input
              type="text"
              placeholder="Search name, company, email..."
              className="input"
              value={searchQuery}
              onChange={(e) => { setSearchQuery(e.target.value); setPageOffset(0); }}
              style={{ minWidth: "220px" }}
            />
            <select
              className="select"
              value={statusFilter}
              onChange={(e) => { setStatusFilter(e.target.value); setPageOffset(0); }}
            >
              <option value="">All Statuses</option>
              <option value="New">New</option>
              <option value="Contacted">Contacted</option>
              <option value="Connected">Connected</option>
              <option value="Qualified">Qualified</option>
              <option value="Opportunity">Opportunity</option>
              <option value="Closed Won">Closed Won</option>
              <option value="Closed Lost">Closed Lost</option>
            </select>
            <input
              type="text"
              placeholder="Filter owner..."
              className="input"
              value={ownerFilter}
              onChange={(e) => { setOwnerFilter(e.target.value); setPageOffset(0); }}
            />
            <input
              type="text"
              placeholder="Filter country..."
              className="input"
              value={countryFilter}
              onChange={(e) => { setCountryFilter(e.target.value); setPageOffset(0); }}
            />
            <a href={exportUrl} download className="btn btn-secondary">
              Export CSV
            </a>
          </div>

          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Record ID</th>
                  <th>Name</th>
                  <th>Company</th>
                  <th>Email</th>
                  <th>Country</th>
                  <th>Status</th>
                  <th>Owner</th>
                  <th>Channel</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {loadingLeads ? (
                  <tr>
                    <td colSpan="9" style={{ textAlign: "center", padding: "24px" }}>
                      Loading leads...
                    </td>
                  </tr>
                ) : leads.length === 0 ? (
                  <tr>
                    <td colSpan="9" style={{ textAlign: "center", padding: "24px", color: "var(--text-secondary)" }}>
                      No leads found. Check database or filters.
                    </td>
                  </tr>
                ) : (
                  leads.map((lead) => (
                    <tr key={lead.id}>
                      <td>{lead.record_id}</td>
                      <td><strong>{lead.full_name || "—"}</strong></td>
                      <td>{lead.company_name || "—"}</td>
                      <td>{lead.email}</td>
                      <td>{lead.country}</td>
                      <td>
                        <span className={`badge badge-${lead.lead_status.toLowerCase().replace(/\s+/g, "")}`}>
                          {lead.lead_status}
                        </span>
                      </td>
                      <td>{lead.contact_owner}</td>
                      <td>{lead.source_channel || "—"}</td>
                      <td>
                        <button
                          className="btn btn-secondary"
                          style={{ padding: "4px 8px", fontSize: "12px" }}
                          onClick={() => {
                            setEditingLead(lead)
                            setEditStatus(lead.lead_status)
                            setEditOwner(lead.contact_owner)
                            setEditNotes(lead.notes || "")
                          }}
                        >
                          Edit
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <div className="pagination">
            <span>
              Page {currentPage} of {totalPages} ({effectiveTotal.toLocaleString()} leads)
            </span>
            <div style={{ display: "flex", gap: "8px" }}>
              <button
                className="btn btn-secondary"
                disabled={currentPage <= 1 || pageOffset === 0}
                onClick={() => setPageOffset((prev) => Math.max(0, prev - pageLimit))}
              >
                Previous
              </button>
              <button
                className="btn btn-secondary"
                disabled={currentPage >= totalPages || leads.length < pageLimit}
                onClick={() => setPageOffset((prev) => prev + pageLimit)}
              >
                Next
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: AI Deduplication */}
      {activeTab === "dedup" && (
        <div className="panel">
          <h2 style={{ fontSize: "18px", marginBottom: "8px" }}>AI Lead Deduplication (Splink 4)</h2>
          <p style={{ color: "var(--text-secondary)", fontSize: "14px", marginBottom: "16px" }}>
            Executes Fellegi-Sunter probabilistic record linkage and connected components graph clustering to surface duplicate entities.
          </p>

          <div className="filter-bar">
            <label style={{ fontSize: "14px" }}>
              Confidence Threshold: <strong>{dedupThreshold}</strong>
              <input
                type="range"
                min="0.1"
                max="0.99"
                step="0.05"
                value={dedupThreshold}
                onChange={(e) => setDedupThreshold(parseFloat(e.target.value))}
                style={{ marginLeft: "8px", verticalAlign: "middle" }}
              />
            </label>
            <label style={{ fontSize: "14px" }}>
              Limit:
              <input
                type="number"
                min="1"
                placeholder="All"
                value={dedupLimit}
                onChange={(e) => setDedupLimit(e.target.value ? parseInt(e.target.value, 10) : "")}
                className="input"
                style={{ width: "80px", marginLeft: "8px" }}
              />
            </label>
            <button className="btn btn-primary" onClick={handleRunDedup} disabled={loadingDedup}>
              {loadingDedup ? "Clustering..." : "Run Deduplication"}
            </button>
          </div>

          {dedupError && (
            <div style={{ color: "var(--danger)", padding: "12px", background: "#fef2f2", borderRadius: "8px", marginBottom: "16px" }}>
              {dedupError}
            </div>
          )}

          <div>
            {dedupClusters.length === 0 && !loadingDedup ? (
              <p style={{ color: "var(--text-secondary)", padding: "20px 0" }}>
                Click "Run Deduplication" to inspect duplicate entity clusters.
              </p>
            ) : (
              <>
                {dedupClusters
                  .slice((dedupPage - 1) * dedupPageSize, dedupPage * dedupPageSize)
                  .map((cluster) => (
                    <div key={cluster.cluster_id} className="cluster-card">
                      <div className="cluster-header">
                        <div>
                          <strong>Cluster #{cluster.cluster_id}</strong>
                          <span style={{ marginLeft: "12px", fontSize: "13px", color: "var(--text-secondary)" }}>
                            {cluster.lead_count} duplicate records
                          </span>
                        </div>
                        <span className="badge badge-qualified">
                          Confidence: {(cluster.confidence * 100).toFixed(4)}%
                        </span>
                      </div>
                      <div className="table-wrapper">
                        <table>
                          <thead>
                            <tr>
                              <th>Record ID</th>
                              <th>Full Name</th>
                              <th>Company</th>
                              <th>Email</th>
                              <th>Phone Digits</th>
                            </tr>
                          </thead>
                          <tbody>
                            {cluster.leads.map((l) => (
                              <tr key={l.record_id}>
                                <td>{l.record_id}</td>
                                <td>{l.full_name}</td>
                                <td>{l.company_name}</td>
                                <td>{l.email}</td>
                                <td>{l.phone_digits}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  ))}

                {dedupClusters.length > 0 && (
                  <div className="pagination" style={{ marginTop: "16px" }}>
                    <span>
                      Page {dedupPage} of {Math.max(1, Math.ceil(dedupClusters.length / dedupPageSize))} ({dedupClusters.length} clusters)
                    </span>
                    <div style={{ display: "flex", gap: "8px" }}>
                      <button
                        className="btn btn-secondary"
                        disabled={dedupPage <= 1}
                        onClick={() => setDedupPage((prev) => Math.max(1, prev - 1))}
                      >
                        Previous
                      </button>
                      <button
                        className="btn btn-secondary"
                        disabled={dedupPage >= Math.ceil(dedupClusters.length / dedupPageSize)}
                        onClick={() => setDedupPage((prev) => Math.min(Math.ceil(dedupClusters.length / dedupPageSize), prev + 1))}
                      >
                        Next
                      </button>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}

      {/* Tab 3: AI Source Extraction */}
      {activeTab === "extract" && (
        <div className="panel">
          <h2 style={{ fontSize: "18px", marginBottom: "8px" }}>AI Source Extraction (LiteLLM + Instructor)</h2>
          <p style={{ color: "var(--text-secondary)", fontSize: "14px", marginBottom: "16px" }}>
            Extracts structured acquisition channels and factual source evidence from raw notes.
          </p>

          <div style={{ marginBottom: "12px" }}>
            <label style={{ display: "block", fontSize: "13px", fontWeight: "600", marginBottom: "6px" }}>
              Quick Test Prompts:
            </label>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
              <button
                className="btn btn-secondary"
                style={{ fontSize: "12px", padding: "4px 8px" }}
                onClick={() => setExtractText("Met him at the SFF booth, scanned our QR code")}
              >
                Event Example
              </button>
              <button
                className="btn btn-secondary"
                style={{ fontSize: "12px", padding: "4px 8px" }}
                onClick={() => setExtractText("Found us through organic google search then booked a demo")}
              >
                Search Example
              </button>
              <button
                className="btn btn-secondary"
                style={{ fontSize: "12px", padding: "4px 8px" }}
                onClick={() => setExtractText("Sarah from Acme referred John to us")}
              >
                Referral Example
              </button>
              <button
                className="btn btn-secondary"
                style={{ fontSize: "12px", padding: "4px 8px" }}
                onClick={() => setExtractText("Connected with him on LinkedIn and discussed our product")}
              >
                LinkedIn Example
              </button>
            </div>
          </div>

          <div style={{ marginBottom: "16px" }}>
            <textarea
              className="textarea"
              rows="3"
              style={{ width: "100%" }}
              placeholder="Enter raw lead notes..."
              value={extractText}
              onChange={(e) => setExtractText(e.target.value)}
            />
          </div>

          <button className="btn btn-primary" onClick={handleExtract} disabled={loadingExtract || !extractText.trim()}>
            {loadingExtract ? "Extracting..." : "Extract Source"}
          </button>

          {extractError && (
            <div style={{ color: "var(--danger)", padding: "12px", background: "#fef2f2", borderRadius: "8px", marginTop: "16px" }}>
              {extractError}
            </div>
          )}

          {extractResult && (
            <div style={{ marginTop: "20px" }}>
              <h3 style={{ fontSize: "15px", marginBottom: "8px" }}>Structured Output:</h3>
              <div className="code-box">
                {JSON.stringify(extractResult, null, 2)}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab 4: Ingest Form */}
      {activeTab === "ingest" && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(420px, 1fr))", gap: "20px", alignItems: "start" }}>
          {/* Left Column: Single Form Ingest */}
          <div className="panel">
            <h2 style={{ fontSize: "18px", marginBottom: "8px" }}>Website Form Ingest</h2>
            <p style={{ color: "var(--text-secondary)", fontSize: "14px", marginBottom: "16px" }}>
              Submits a new website lead. Automatically deduplicates on email or phone and updates existing leads.
            </p>

            <form onSubmit={handleIngest} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              <div>
                <label style={{ display: "block", fontSize: "13px", marginBottom: "4px" }}>Full Name *</label>
                <input
                  type="text"
                  required
                  className="input"
                  style={{ width: "100%" }}
                  value={ingestName}
                  onChange={(e) => setIngestName(e.target.value)}
                />
              </div>
              <div>
                <label style={{ display: "block", fontSize: "13px", marginBottom: "4px" }}>Email *</label>
                <input
                  type="email"
                  required
                  className="input"
                  style={{ width: "100%" }}
                  value={ingestEmail}
                  onChange={(e) => setIngestEmail(e.target.value)}
                />
              </div>
              <div>
                <label style={{ display: "block", fontSize: "13px", marginBottom: "4px" }}>Phone</label>
                <input
                  type="text"
                  className="input"
                  style={{ width: "100%" }}
                  value={ingestPhone}
                  onChange={(e) => setIngestPhone(e.target.value)}
                />
              </div>
              <div>
                <label style={{ display: "block", fontSize: "13px", marginBottom: "4px" }}>Company</label>
                <input
                  type="text"
                  className="input"
                  style={{ width: "100%" }}
                  value={ingestCompany}
                  onChange={(e) => setIngestCompany(e.target.value)}
                />
              </div>
              <div>
                <label style={{ display: "block", fontSize: "13px", marginBottom: "4px" }}>Country</label>
                <input
                  type="text"
                  className="input"
                  style={{ width: "100%" }}
                  value={ingestCountry}
                  onChange={(e) => setIngestCountry(e.target.value)}
                />
              </div>
              <div>
                <label style={{ display: "block", fontSize: "13px", marginBottom: "4px" }}>Message / Notes</label>
                <textarea
                  className="textarea"
                  rows="2"
                  style={{ width: "100%" }}
                  value={ingestMessage}
                  onChange={(e) => setIngestMessage(e.target.value)}
                />
              </div>

              <button type="submit" className="btn btn-primary" disabled={loadingIngest} style={{ marginTop: "8px" }}>
                {loadingIngest ? "Submitting..." : "Submit Ingest"}
              </button>
            </form>

            {ingestError && (
              <div style={{ color: "var(--danger)", padding: "12px", background: "#fef2f2", borderRadius: "8px", marginTop: "16px" }}>
                {ingestError}
              </div>
            )}

            {ingestResult && (
              <div style={{ marginTop: "20px" }}>
                <div style={{ padding: "12px", background: "#f0fdf4", color: "#166534", borderRadius: "8px", marginBottom: "8px" }}>
                  Result Action: <strong>{ingestResult.action.toUpperCase()}</strong>
                </div>
                <div className="code-box">
                  {JSON.stringify(ingestResult.lead, null, 2)}
                </div>
              </div>
            )}
          </div>

          {/* Right Column: Batch JSON Ingest */}
          <div className="panel">
            <h2 style={{ fontSize: "18px", marginBottom: "8px" }}>Batch JSON Ingest</h2>
            <p style={{ color: "var(--text-secondary)", fontSize: "14px", marginBottom: "16px" }}>
              Submit multiple leads in a JSON array. Each lead is deduplicated and either created or updated.
            </p>

            <form onSubmit={handleBatchIngest} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              <div>
                <label style={{ display: "block", fontSize: "13px", marginBottom: "4px" }}>JSON Payload *</label>
                <textarea
                  className="textarea"
                  rows="10"
                  style={{ width: "100%", fontFamily: "monospace", fontSize: "13px" }}
                  placeholder="Paste JSON array of lead objects..."
                  value={batchJson}
                  onChange={(e) => setBatchJson(e.target.value)}
                  required
                />
              </div>

              <div style={{ display: "flex", gap: "8px" }}>
                <button type="submit" className="btn btn-primary" disabled={loadingBatch || !batchJson.trim()}>
                  {loadingBatch ? "Processing Batch..." : "Submit Batch Ingest"}
                </button>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setBatchJson(EXAMPLE_BATCH_JSON)}
                >
                  Fill Example
                </button>
              </div>
            </form>

            {batchError && (
              <div style={{ color: "var(--danger)", padding: "12px", background: "#fef2f2", borderRadius: "8px", marginTop: "16px" }}>
                {batchError}
              </div>
            )}

            {batchResult && (
              <div style={{ marginTop: "20px" }}>
                <div style={{ padding: "10px 14px", background: "#f0fdf4", color: "#166534", borderRadius: "8px", marginBottom: "8px", fontSize: "14px", fontWeight: "600" }}>
                  Processed {batchResult.length} leads ({batchResult.filter((r) => r.action === "created").length} created, {batchResult.filter((r) => r.action === "updated").length} updated)
                </div>
                <div className="code-box" style={{ maxHeight: "250px", overflowY: "auto" }}>
                  {JSON.stringify(batchResult, null, 2)}
                </div>
              </div>
            )}

            {/* Example Format Below It */}
            <div style={{ marginTop: "20px", borderTop: "1px solid var(--border-color)", paddingTop: "14px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                <label style={{ fontSize: "13px", fontWeight: "600" }}>
                  Example Format:
                </label>
              </div>
              <pre className="code-box" style={{ fontSize: "12px", maxHeight: "190px", overflowY: "auto" }}>
                {EXAMPLE_BATCH_JSON}
              </pre>
            </div>
          </div>
        </div>
      )}

      {/* Edit Lead Modal */}
      {editingLead && (
        <div className="modal-backdrop">
          <div className="modal-content">
            <div className="modal-header">
              <h3>Edit Lead #{editingLead.record_id}</h3>
              <button
                className="btn btn-secondary"
                style={{ padding: "2px 8px" }}
                onClick={() => setEditingLead(null)}
              >
                ✕
              </button>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              <div>
                <label style={{ display: "block", fontSize: "13px", marginBottom: "4px" }}>Lead Status</label>
                <select
                  className="select"
                  style={{ width: "100%" }}
                  value={editStatus}
                  onChange={(e) => setEditStatus(e.target.value)}
                >
                  <option value="New">New</option>
                  <option value="Contacted">Contacted</option>
                  <option value="Connected">Connected</option>
                  <option value="Qualified">Qualified</option>
                  <option value="Opportunity">Opportunity</option>
                  <option value="Closed Won">Closed Won</option>
                  <option value="Closed Lost">Closed Lost</option>
                </select>
              </div>
              <div>
                <label style={{ display: "block", fontSize: "13px", marginBottom: "4px" }}>Contact Owner</label>
                <input
                  type="text"
                  className="input"
                  style={{ width: "100%" }}
                  value={editOwner}
                  onChange={(e) => setEditOwner(e.target.value)}
                />
              </div>
              <div>
                <label style={{ display: "block", fontSize: "13px", marginBottom: "4px" }}>Notes</label>
                <textarea
                  className="textarea"
                  rows="3"
                  style={{ width: "100%" }}
                  value={editNotes}
                  onChange={(e) => setEditNotes(e.target.value)}
                />
              </div>
              <div style={{ display: "flex", justifyContent: "flex-end", gap: "8px", marginTop: "12px" }}>
                <button className="btn btn-secondary" onClick={() => setEditingLead(null)}>
                  Cancel
                </button>
                <button className="btn btn-primary" onClick={handleSaveEdit} disabled={savingEdit}>
                  {savingEdit ? "Saving..." : "Save Changes"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
