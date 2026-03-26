import { useEffect, useState, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getCalendar, updateStatus, regenerateItem, editField, generateImage } from "../api";
import "./ItemPage.css";

const BASE = import.meta.env.PROD ? "" : "http://localhost:8000";

function useAssetSlot(endpoint, itemId) {
  const [url, setUrl] = useState(null);
  const [uploading, setUploading] = useState(false);
  const inputRef = useRef(null);

  useEffect(() => {
    fetch(`${BASE}/api/item/${endpoint}/${itemId}`)
      .then(r => r.json())
      .then(data => {
        const key = Object.keys(data).find(k => k.endsWith("_url"));
        if (key && data[key]) setUrl(data[key]);
      })
      .catch(() => {});
  }, [endpoint, itemId]);

  const upload = async (file, uploadEndpoint) => {
    if (!file) return;
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("item_id", itemId);
      formData.append("file", file);
      const res = await fetch(`${BASE}/api/item/${uploadEndpoint}`, { method: "POST", body: formData });
      if (!res.ok) throw new Error();
      const data = await res.json();
      const key = Object.keys(data).find(k => k.endsWith("_url"));
      setUrl(data[key]);
      return true;
    } catch {
      return false;
    } finally {
      setUploading(false);
    }
  };

  const remove = async (deleteEndpoint) => {
    await fetch(`${BASE}/api/item/${deleteEndpoint}/${itemId}`, { method: "DELETE" });
    setUrl(null);
  };

  return { url, setUrl, uploading, inputRef, upload, remove };
}

export default function ItemPage() {
  const { year, month, id } = useParams();
  const navigate = useNavigate();

  const [item, setItem] = useState(null);
  const [loading, setLoading] = useState(true);
  const [regenerating, setRegenerating] = useState(false);
  const [generatingImage, setGeneratingImage] = useState(false);
  const [imageHistory, setImageHistory] = useState([]);
  const [editingField, setEditingField] = useState(null);
  const [editValue, setEditValue] = useState("");
  const [saving, setSaving] = useState(false);
  const [statusMsg, setStatusMsg] = useState(null);

  const styleSlot = useAssetSlot("style", id);
  const elementSlot = useAssetSlot("element", id);

  useEffect(() => {
    getCalendar(Number(year), Number(month))
      .then((cal) => {
        const found = cal.items.find((i) => i.id === Number(id));
        setItem(found || null);
      })
      .finally(() => setLoading(false));
  }, [year, month, id]);

  const loadHistory = () => {
    fetch(`${BASE}/api/item/image-history/${id}`)
      .then(r => r.json())
      .then(data => setImageHistory(data.images || []))
      .catch(() => {});
  };

  useEffect(() => { loadHistory(); }, [id]);

  const showMsg = (msg, isError = false) => {
    setStatusMsg({ text: msg, error: isError });
    setTimeout(() => setStatusMsg(null), 4000);
  };

  const handleStatus = async (status) => {
    await updateStatus(Number(month), Number(year), Number(id), status);
    setItem((prev) => ({ ...prev, status }));
    showMsg(`Status: ${status}`);
  };

  const handleRegenerate = async () => {
    setRegenerating(true);
    try {
      const res = await regenerateItem(Number(month), Number(year), Number(id));
      setItem(res.item);
      showMsg("Content regenerated.");
    } catch (e) {
      const detail = e?.response?.data?.detail || e?.message || "Unknown error";
      showMsg("Regenerate failed: " + detail, true);
      console.error("Regenerate error:", e);
    } finally {
      setRegenerating(false);
    }
  };

  const handleGenerateImage = async () => {
    setGeneratingImage(true);
    try {
      const res = await generateImage(Number(month), Number(year), Number(id));
      setItem(res.item);
      loadHistory();
      showMsg("Image generated successfully!");
    } catch (e) {
      const detail = e?.response?.data?.detail || e?.message || "Unknown error";
      console.error("Generate image error:", e);
      showMsg("Generation failed: " + detail, true);
    } finally {
      setGeneratingImage(false);
    }
  };

  const startEdit = (field, currentValue) => {
    setEditingField(field);
    setEditValue(currentValue || "");
  };

  const saveEdit = async () => {
    setSaving(true);
    try {
      await editField(Number(month), Number(year), Number(id), editingField, editValue);
      setItem((prev) => {
        const topLevel = ["topic", "hook", "notes"];
        if (topLevel.includes(editingField)) return { ...prev, [editingField]: editValue };
        return { ...prev, content: { ...prev.content, [editingField]: editValue } };
      });
      setEditingField(null);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="item-page"><div className="state-msg">Loading...</div></div>;
  if (!item) return <div className="item-page"><div className="state-msg error">Item not found.</div></div>;

  const content = item.content || {};
  const canGenerateImage = item.status === "approved" || item.status === "image_generated";

  return (
    <div className="item-page">
      <button className="back-btn" onClick={() => navigate(-1)}>← Back to Calendar</button>

      {statusMsg && <div className={`status-toast${statusMsg.error ? ' status-toast--error' : ''}`}>{statusMsg.text}</div>}

      <div className="item-header">
        <div>
          <div className="item-date-platform">{item.date} · {item.platform}</div>
          <h1 className="item-title">{item.topic}</h1>
          <div className="item-badges">
            <span className="badge">{item.content_pillar}</span>
            <span className="badge">{item.format}</span>
            <span className={`badge status-${item.status}`}>{item.status.replace(/_/g, " ")}</span>
          </div>
        </div>
        <div className="header-actions">
          <button className="btn btn-secondary" onClick={handleRegenerate} disabled={regenerating}>
            {regenerating ? "Regenerating..." : "↺ Regenerate"}
          </button>
          {item.status !== "approved" && item.status !== "image_generated" && (
            <button className="btn btn-approve" onClick={() => handleStatus("approved")}>✓ Approve</button>
          )}
          {item.status !== "rejected" && (
            <button className="btn btn-reject" onClick={() => handleStatus("rejected")}>✗ Reject</button>
          )}
        </div>
      </div>

      <div className="item-grid">

        {/* Caption */}
        <div className="card full-width">
          <div className="card-header">
            <h3>Caption</h3>
            <button className="edit-btn" onClick={() => startEdit("caption", content.caption)}>Edit</button>
          </div>
          {editingField === "caption" ? (
            <div className="edit-block">
              <textarea rows={10} value={editValue} onChange={(e) => setEditValue(e.target.value)} />
              <div className="edit-actions">
                <button className="btn btn-save" onClick={saveEdit} disabled={saving}>{saving ? "Saving..." : "Save"}</button>
                <button className="btn btn-cancel" onClick={() => setEditingField(null)}>Cancel</button>
              </div>
            </div>
          ) : (
            <pre className="caption-text">{content.caption || "Not generated yet"}</pre>
          )}
        </div>

        {/* Text on Image */}
        <div className="card">
          <div className="card-header">
            <h3>Text on Image</h3>
            <button className="edit-btn" onClick={() => startEdit("text_on_image", content.text_on_image)}>Edit</button>
          </div>
          {editingField === "text_on_image" ? (
            <div className="edit-block">
              <textarea rows={3} value={editValue} onChange={(e) => setEditValue(e.target.value)} />
              <div className="edit-actions">
                <button className="btn btn-save" onClick={saveEdit} disabled={saving}>{saving ? "Saving..." : "Save"}</button>
                <button className="btn btn-cancel" onClick={() => setEditingField(null)}>Cancel</button>
              </div>
            </div>
          ) : (
            <p className="highlight-text">{content.text_on_image || "—"}</p>
          )}
        </div>

        {/* Description */}
        <div className="card">
          <div className="card-header">
            <h3>Alt Text / Description</h3>
            <button className="edit-btn" onClick={() => startEdit("description", content.description)}>Edit</button>
          </div>
          {editingField === "description" ? (
            <div className="edit-block">
              <textarea rows={4} value={editValue} onChange={(e) => setEditValue(e.target.value)} />
              <div className="edit-actions">
                <button className="btn btn-save" onClick={saveEdit} disabled={saving}>{saving ? "Saving..." : "Save"}</button>
                <button className="btn btn-cancel" onClick={() => setEditingField(null)}>Cancel</button>
              </div>
            </div>
          ) : (
            <p className="body-text">{content.description || "—"}</p>
          )}
        </div>

        {/* Image Prompt */}
        <div className="card full-width">
          <div className="card-header">
            <h3>Image Prompt</h3>
            <button className="edit-btn" onClick={() => startEdit("image_prompt", content.image_prompt)}>Edit</button>
          </div>
          {editingField === "image_prompt" ? (
            <div className="edit-block">
              <textarea rows={5} value={editValue} onChange={(e) => setEditValue(e.target.value)} />
              <div className="edit-actions">
                <button className="btn btn-save" onClick={saveEdit} disabled={saving}>{saving ? "Saving..." : "Save"}</button>
                <button className="btn btn-cancel" onClick={() => setEditingField(null)}>Cancel</button>
              </div>
            </div>
          ) : (
            <p className="prompt-text">{content.image_prompt || "—"}</p>
          )}
        </div>

        {/* Style Reference + Design Element side by side */}
        <div className="card">
          <div className="card-header">
            <h3>Style Reference</h3>
            <div className="slot-actions">
              {styleSlot.url && (
                <button className="btn btn-danger-sm" onClick={() => { styleSlot.remove("delete-style"); showMsg("Style reference removed."); }}>✕</button>
              )}
              <button className="btn btn-secondary" onClick={() => styleSlot.inputRef.current?.click()} disabled={styleSlot.uploading}>
                {styleSlot.uploading ? "Uploading..." : styleSlot.url ? "↺ Replace" : "+ Upload"}
              </button>
              <input ref={styleSlot.inputRef} type="file" accept=".jpg,.jpeg,.png,.webp" style={{ display: "none" }}
                onChange={async (e) => { const ok = await styleSlot.upload(e.target.files[0], "upload-style"); showMsg(ok ? "Style reference saved!" : "Upload failed."); e.target.value = ""; }} />
            </div>
          </div>
          <p className="slot-desc">A post you like — Ideogram will match its visual mood and composition style.</p>
          {styleSlot.url ? (
            <img src={`${BASE}${styleSlot.url}`} alt="Style ref" className="slot-img" />
          ) : (
            <div className="slot-placeholder">No style reference<br/><span>Optional</span></div>
          )}
        </div>

        <div className="card">
          <div className="card-header">
            <h3>Design Element</h3>
            <div className="slot-actions">
              {elementSlot.url && (
                <button className="btn btn-danger-sm" onClick={() => { elementSlot.remove("delete-element"); showMsg("Design element removed."); }}>✕</button>
              )}
              <button className="btn btn-secondary" onClick={() => elementSlot.inputRef.current?.click()} disabled={elementSlot.uploading}>
                {elementSlot.uploading ? "Uploading..." : elementSlot.url ? "↺ Replace" : "+ Upload"}
              </button>
              <input ref={elementSlot.inputRef} type="file" accept=".jpg,.jpeg,.png,.webp" style={{ display: "none" }}
                onChange={async (e) => { const ok = await elementSlot.upload(e.target.files[0], "upload-element"); showMsg(ok ? "Design element saved!" : "Upload failed."); e.target.value = ""; }} />
            </div>
          </div>
          <p className="slot-desc">A mockup, screenshot or asset — Ideogram will incorporate it into the design.</p>
          {elementSlot.url ? (
            <img src={`${BASE}${elementSlot.url}`} alt="Design element" className="slot-img" />
          ) : (
            <div className="slot-placeholder">No design element<br/><span>Optional</span></div>
          )}
        </div>

        {/* Generated Image */}
        <div className="card full-width image-card">
          <div className="card-header">
            <h3>Generated Image</h3>
            {canGenerateImage && (
              <button className="btn btn-generate" onClick={handleGenerateImage} disabled={generatingImage}>
                {generatingImage ? "Generating..." : item.image_url ? "↺ Regenerate Image" : "✦ Generate Image"}
              </button>
            )}
          </div>

          {item.image_url ? (
            <div className="image-result">
              <img src={`${BASE}${item.image_url}`} alt={content.text_on_image} className="generated-image" />
              <div className="image-actions">
                <a href={`${BASE}${item.image_url}`} download className="btn btn-secondary">↓ Download</a>
                {item.image_style_ref_used && <span className="ref-badge">✓ Style ref used</span>}
                {item.image_element_used && <span className="ref-badge">✓ Element used</span>}
              </div>
            </div>
          ) : (
            <div className="image-placeholder">
              {generatingImage ? (
                <div className="generating-spinner">
                  <div className="spinner" />
                  <p>Generating{styleSlot.url || elementSlot.url ? " with your references" : ""}...</p>
                  <p className="placeholder-sub">Usually takes 10–20 seconds.</p>
                </div>
              ) : (
                <>
                  <span>No image generated yet</span>
                  <p className="placeholder-sub">
                    {canGenerateImage ? "Click 'Generate Image' above." : "Approve this item first."}
                  </p>
                </>
              )}
            </div>
          )}
        </div>

      </div>

      {/* Image History */}
      {imageHistory.length > 1 && (
        <div className="history-section">
          <h3 className="history-title">Previous Versions <span>({imageHistory.length} total)</span></h3>
          <div className="history-grid">
            {imageHistory.map((img, i) => (
              <div
                key={img.filename}
                className={`history-item ${item.image_url === img.url ? 'history-item--active' : ''}`}
                onClick={() => setItem(prev => ({ ...prev, image_url: img.url }))}
              >
                <img src={`${BASE}${img.url}`} alt={`Version ${imageHistory.length - i}`} />
                <div className="history-label">
                  {i === 0 ? 'Latest' : `v${imageHistory.length - i}`}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

    </div>
  );
}
