import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getCalendar, updateStatus, generateCalendar, regenerateItem, editField, deleteCalendar } from "../api";
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
  const [progress, setProgress] = useState(null);
  const navigate = useNavigate();

  const fetchCalendar = () => {
    setLoading(true);
    setError(null);
    getCalendar(year, month)
      .then(setCalendar)
      .catch(() => { setCalendar(null); })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchCalendar();
  }, [year, month]);

  const handleDragStart = (e, itemId) => { e.dataTransfer.setData("itemId", itemId); };

  const handleDrop = async (e, dateStr) => {
    e.preventDefault();
    const itemId = Number(e.dataTransfer.getData("itemId"));
    if (!itemId || !dateStr) return;

    setCalendar(prev => ({
      ...prev,
      items: prev.items.map(i => i.id === itemId ? { ...i, date: dateStr } : i)
    }));

    try {
      await editField(month, year, itemId, "date", dateStr);
    } catch (err) {
      console.error(err);
      alert("Tarih güncellenemedi!");
      fetchCalendar();
    }
  };

  // Akıllı Devam Etme (Resume) Fonksiyonu
  const fillMissingContent = async (calData) => {
    const pendingItems = calData.items.filter(i => i.status === 'pending' || i.status === 'error');
    if(pendingItems.length === 0) return;

    setProgress({ current: 0, total: pendingItems.length, text: "İçerikler üretiliyor..." });
    
    for (let i = 0; i < pendingItems.length; i++) {
      const item = pendingItems[i];
      setProgress({ 
        current: i + 1, 
        total: pendingItems.length, 
        text: `Yazılıyor: ${item.topic.substring(0, 25)}...` 
      });
      
      try {
        const res = await regenerateItem(month, year, item.id);
        setCalendar(prev => {
          if(!prev) return prev;
          const newItems = [...prev.items];
          const idx = newItems.findIndex(x => x.id === item.id);
          if(idx > -1) newItems[idx] = res.item;
          return { ...prev, items: newItems };
        });
      } catch(err) {
        console.error("Item gen failed", err);
      }
    }
    setProgress(null);
  };

  const handleGenerateCalendar = async () => {
    setError(null);
    setProgress({ current: 0, total: 14, text: "Takvim iskeleti ve strateji planlanıyor..." });

    try {
      await generateCalendar(month, year);
      const cal = await getCalendar(year, month);
      setCalendar(cal);
      await fillMissingContent(cal);
    } catch (err) {
      setError("Üretim sırasında hata: " + (err.response?.data?.detail || err.message));
      setProgress(null);
    }
  };

  // Komple Takvimi Silip Yeniden Üreten Fonksiyon
  const handleRebuildCalendar = async () => {
    if(!window.confirm("DİKKAT: Bu ayki tüm takvim ve içerikler KALICI OLARAK silinip yepyeni bir strateji ile baştan üretilecek. Emin misiniz?")) return;
    
    setProgress({ current: 0, total: 1, text: "Eski takvim siliniyor..." });
    try {
      await deleteCalendar(year, month);
      setCalendar(null);
      await handleGenerateCalendar();
    } catch(err) {
      alert("Silme işlemi başarısız oldu.");
      setProgress(null);
    }
  };

  const monthName = new Date(year, month - 1, 1).toLocaleString("en-US", { month: "long", year: "numeric" });
  const daysInMonth = new Date(year, month, 0).getDate();
  let firstDay = new Date(year, month - 1, 1).getDay() - 1;
  if (firstDay === -1) firstDay = 6;

  const blanks = Array.from({ length: firstDay });
  const days = Array.from({ length: daysInMonth }, (_, i) => {
    const d = i + 1;
    const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
    return { day: d, dateStr, items: calendar ? calendar.items.filter(item => item.date === dateStr) : [] };
  });

  return (
    <div className="calendar-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Content Calendar</h1>
          <p className="page-sub">{calendar ? `${calendar.total_items} items · ${monthName}` : monthName}</p>
          
          {/* Akıllı Aksiyon Butonları (Yenileme & Eksik Üretim) */}
          {calendar && !progress && (
            <div style={{ display: 'flex', gap: '10px', marginTop: '12px' }}>
              {calendar.items.some(i => i.status === 'pending' || i.status === 'error') && (
                <button onClick={() => fillMissingContent(calendar)} className="btn-generate-main" style={{ padding: '6px 12px', fontSize: '12px', background: '#F3B800', color: '#000' }}>
                  ⚡ Eksik İçerikleri Üret
                </button>
              )}
              <button onClick={handleRebuildCalendar} className="btn-generate-main" style={{ padding: '6px 12px', fontSize: '12px', background: '#F51E2E' }}>
                🔄 Sıfırdan Yenile
              </button>
            </div>
          )}
        </div>
        <div className="month-nav">
          <button className="btn-nav" onClick={() => { const d = new Date(year, month - 2); setYear(d.getFullYear()); setMonth(d.getMonth() + 1); }}>‹</button>
          <span className="month-label">{monthName}</span>
          <button className="btn-nav" onClick={() => { const d = new Date(year, month); setYear(d.getFullYear()); setMonth(d.getMonth() + 1); }}>›</button>
        </div>
      </div>

      {loading && <div className="state-msg">Loading calendar...</div>}

      {progress && (
        <div className="progress-overlay">
          <h3>🤖 Yapay Zeka İçerik Fabrikası Çalışıyor</h3>
          <p>{progress.text}</p>
          <div className="progress-bar-container">
            <div className="progress-bar-fill" style={{ width: `${(progress.current / progress.total) * 100}%` }}></div>
          </div>
          <p style={{ fontSize: '12px', color: 'var(--gray-600)' }}>Lütfen bu sayfadan ayrılmayın veya sekmeyi kapatmayın ({progress.current}/{progress.total})</p>
        </div>
      )}

      {!loading && !calendar && !progress && (
        <div className="state-msg">
            <p style={{ marginBottom: '16px' }}>Bu ay için henüz bir içerik takvimi oluşturulmamış.</p>
            <button onClick={handleGenerateCalendar} className="btn-generate-main">✦ Bu Ay İçin Takvim Üret</button>
        </div>
      )}

      {calendar && !progress && (
        <div className="calendar-grid">
          {['Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt', 'Paz'].map(d => <div className="cal-header-day" key={d}>{d}</div>)}
          {blanks.map((_, i) => <div key={`blank-${i}`} className="cal-day blank"></div>)}
          {days.map(d => (
            <div 
              key={d.dateStr} 
              className="cal-day"
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => handleDrop(e, d.dateStr)}
            >
              <div className="day-number">{d.day}</div>
              {d.items.map(item => {
                const s = STATUS_COLORS[item.status] || STATUS_COLORS.pending;
                return (
                  <div
                    draggable
                    onDragStart={(e) => handleDragStart(e, item.id)}
                    className={`cal-item-card status-${item.status}`}
                    key={item.id}
                    onClick={() => navigate(`/item/${year}/${month}/${item.id}`)}
                  >
                    <div className="cal-item-header">
                      <span>{PLATFORM_ICONS[item.platform]}</span>
                      <span className={`status-dot ${item.status}`}></span>
                    </div>
                    <div className="cal-item-title">{item.topic}</div>
                  </div>
                )
              })}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}