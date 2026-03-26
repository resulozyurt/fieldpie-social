import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getCalendar, updateStatus, generateCalendar } from "../api";
import "./CalendarPage.css";

const STATUS_COLORS = {
  pending: { bg: "#FFF8E1", text: "#B8860B", label: "Pending" },
  content_generated: { bg: "#E3F2FD", text: "#1565C0", label: "Ready" },
  approved: { bg: "#E8F5E9", text: "#2E7D32", label: "Approved" },
  rejected: { bg: "#FFEBEE", text: "#C62828", label: "Rejected" },
  published: { bg: "#F3E5F5", text: "#6A1B9A", label: "Published" },
  error: { bg: "#FBE9E7", text: "#BF360C", label: "Error" },
};
const PLATFORM_ICONS = { LinkedIn: "💼", Instagram: "📷" };

export default function CalendarPage() {
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [calendar, setCalendar] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [updatingId, setUpdatingId] = useState(null);
  const [generating, setGenerating] = useState(false); // Yeni state
  const navigate = useNavigate();

  const fetchCalendar = () => {
    setLoading(true);
    setError(null);
    getCalendar(year, month)
      .then(setCalendar)
      .catch(() => {
          setCalendar(null);
          setError("No calendar found for this month.");
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchCalendar();
  }, [year, month]);

  const handleStatus = async (e, item, status) => {
    e.stopPropagation();
    setUpdatingId(item.id);
    try {
      await updateStatus(month, year, item.id, status);
      setCalendar((prev) => ({
        ...prev,
        items: prev.items.map((i) =>
          i.id === item.id ? { ...i, status } : i
        ),
      }));
    } finally {
      setUpdatingId(null);
    }
  };

  // Yeni Üretim Fonksiyonu
  const handleGenerateCalendar = async () => {
    setGenerating(true);
    setError(null);
    try {
      await generateCalendar(month, year);
      fetchCalendar(); // Üretim bitince takvimi yeniden çek
    } catch (err) {
      const msg = err.response?.data?.detail || err.message;
      setError("Takvim üretilemedi: " + msg);
    } finally {
      setGenerating(false);
    }
  };

  const monthName = new Date(year, month - 1, 1).toLocaleString("en-US", { month: "long", year: "numeric" });

  return (
    <div className="calendar-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Content Calendar</h1>
          <p className="page-sub">{calendar ? `${calendar.total_items} items · ${monthName}` : monthName}</p>
        </div>
        <div className="month-nav">
          <button className="btn-nav" onClick={() => { const d = new Date(year, month - 2); setYear(d.getFullYear()); setMonth(d.getMonth() + 1); }}>‹</button>
          <span className="month-label">{monthName}</span>
          <button className="btn-nav" onClick={() => { const d = new Date(year, month); setYear(d.getFullYear()); setMonth(d.getMonth() + 1); }}>›</button>
        </div>
      </div>

      {loading && <div className="state-msg">Loading calendar...</div>}

      {/* Veri Yoksa Gösterilecek Üretim Butonu Alanı */}
      {!loading && !calendar && (
        <div className="state-msg" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}>
            <p style={{ color: 'var(--gray-600)' }}>{error || "Bu ay için henüz bir içerik takvimi oluşturulmamış."}</p>
            <button 
                onClick={handleGenerateCalendar} 
                disabled={generating}
                style={{
                    background: 'var(--pm500)',
                    color: 'white',
                    padding: '10px 20px',
                    border: 'none',
                    borderRadius: '8px',
                    cursor: generating ? 'not-allowed' : 'pointer',
                    fontWeight: '600',
                    opacity: generating ? 0.7 : 1
                }}
            >
                {generating ? "🤖 Yapay Zeka Takvimi Oluşturuyor (30-60 sn)..." : "✦ Bu Ay İçin Takvim Üret"}
            </button>
        </div>
      )}

      {calendar && (
        <>
          <div className="stats-row">
            {Object.entries(
              calendar.items.reduce((acc, i) => {
                acc[i.status] = (acc[i.status] || 0) + 1;
                return acc;
              }, {})
            ).map(([status, count]) => {
              const s = STATUS_COLORS[status] || STATUS_COLORS.pending;
              return (
                <span key={status} className="stat-pill" style={{ background: s.bg, color: s.text }}>
                  {s.label}: {count}
                </span>
              );
            })}
          </div>

          <div className="items-list">
            {calendar.items.map((item) => {
              const s = STATUS_COLORS[item.status] || STATUS_COLORS.pending;
              const isUpdating = updatingId === item.id;
              return (
                <div
                  key={item.id}
                  className="item-card"
                  onClick={() => navigate(`/item/${year}/${month}/${item.id}`)}
                >
                  <div className="item-left">
                    <div className="item-date">{item.date}</div>
                    <div className="item-platform">
                      {PLATFORM_ICONS[item.platform]} {item.platform}
                    </div>
                  </div>

                  <div className="item-center">
                    <div className="item-topic">{item.topic}</div>
                    <div className="item-meta">
                      <span className="item-pillar">{item.content_pillar}</span>
                      <span className="item-format">{item.format}</span>
                    </div>
                    <div className="item-hook">"{item.hook}"</div>
                  </div>

                  <div className="item-right">
                    <span className="status-badge" style={{ background: s.bg, color: s.text }}>
                      {s.label}
                    </span>
                    {item.status === "content_generated" && (
                      <div className="action-btns" onClick={(e) => e.stopPropagation()}>
                        <button
                          className="btn-approve"
                          disabled={isUpdating}
                          onClick={(e) => handleStatus(e, item, "approved")}
                        >
                          ✓ Approve
                        </button>
                        <button
                          className="btn-reject"
                          disabled={isUpdating}
                          onClick={(e) => handleStatus(e, item, "rejected")}
                        >
                          ✗ Reject
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}