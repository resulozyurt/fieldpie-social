import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getCalendar, updateStatus, generateCalendar, regenerateItem, editField } from "../api";
import "./CalendarPage.css";

const PLATFORM_ICONS = { LinkedIn: "💼", Instagram: "📷" };

export default function CalendarPage() {
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [calendar, setCalendar] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [progress, setProgress] = useState(null); // Aşama aşama üretim takibi için
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

  // Sürükle-Bırak (Drag & Drop) İşlemleri
  const handleDragStart = (e, itemId) => {
    e.dataTransfer.setData("itemId", itemId);
  };

  const handleDrop = async (e, dateStr) => {
    e.preventDefault();
    const itemId = Number(e.dataTransfer.getData("itemId"));
    if (!itemId || !dateStr) return;

    // Arayüzde anında güncelle (Optimistic UI)
    setCalendar(prev => ({
      ...prev,
      items: prev.items.map(i => i.id === itemId ? { ...i, date: dateStr } : i)
    }));

    // Arka planda veritabanını güncelle
    try {
      await editField(month, year, itemId, "date", dateStr);
    } catch (err) {
      console.error(err); // <-- ESLint kızmasın diye err değişkenini kullandık
      alert("Tarih güncellenemedi!");
      fetchCalendar(); // Hata olursa eski haline döndür
    }
  };

  // Aşama Aşama Takvim Üretim Motoru
  const handleGenerateCalendar = async () => {
    setError(null);
    setProgress({ current: 0, total: 14, text: "Takvim iskeleti ve strateji planlanıyor..." });

    try {
      // 1. İskeleti Üret ve Kaydet
      await generateCalendar(month, year);
      const cal = await getCalendar(year, month);
      setCalendar(cal);

      // 2. Her bir içerik için sırayla detayları üret
      for (let i = 0; i < cal.items.length; i++) {
        const item = cal.items[i];
        if (item.status === 'pending' || item.status === 'error') {
          setProgress({ 
            current: i + 1, 
            total: cal.items.length, 
            text: `Yapay Zeka İçerik Yazıyor: ${item.topic.substring(0, 25)}...` 
          });
          
          const res = await regenerateItem(month, year, item.id);
          
          // Arayüzde üretilen içeriğin statüsünü anında güncelle
          setCalendar(prev => {
            const newItems = [...prev.items];
            const idx = newItems.findIndex(x => x.id === item.id);
            if(idx > -1) newItems[idx] = res.item;
            return { ...prev, items: newItems };
          });
        }
      }
      setProgress(null); // İşlem bitti
    } catch (err) {
      setError("Üretim sırasında hata: " + (err.response?.data?.detail || err.message));
      setProgress(null);
    }
  };

  const monthName = new Date(year, month - 1, 1).toLocaleString("en-US", { month: "long", year: "numeric" });

  // Takvim Grid'ini Hesaplama (Pazartesi'den başlar)
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
        </div>
        <div className="month-nav">
          <button className="btn-nav" onClick={() => { const d = new Date(year, month - 2); setYear(d.getFullYear()); setMonth(d.getMonth() + 1); }}>‹</button>
          <span className="month-label">{monthName}</span>
          <button className="btn-nav" onClick={() => { const d = new Date(year, month); setYear(d.getFullYear()); setMonth(d.getMonth() + 1); }}>›</button>
        </div>
      </div>

      {loading && <div className="state-msg">Loading calendar...</div>}

      {/* Progress Bar Ekranı */}
      {progress && (
        <div className="progress-overlay">
          <h3>🤖 Yapay Zeka İçerik Fabrikası Çalışıyor</h3>
          <p>{progress.text}</p>
          <div className="progress-bar-container">
            <div className="progress-bar-fill" style={{ width: `${(progress.current / progress.total) * 100}%` }}></div>
          </div>
          <p style={{ fontSize: '12px', color: 'var(--gray-600)' }}>Lütfen bu sayfadan ayrılmayın ({progress.current}/{progress.total})</p>
        </div>
      )}

      {/* Veri Yoksa Üret Butonu */}
      {!loading && !calendar && !progress && (
        <div className="state-msg">
            <p style={{ marginBottom: '16px' }}>{error || "Bu ay için henüz bir içerik takvimi oluşturulmamış."}</p>
            <button onClick={handleGenerateCalendar} className="btn-generate-main">✦ Bu Ay İçin Takvim Üret</button>
        </div>
      )}

      {/* Gerçek Takvim Grid Mimarisi */}
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
              {d.items.map(item => (
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
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}