import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import { useState, useEffect } from "react";
import CalendarPage from "./pages/CalendarPage";
import ItemPage from "./pages/ItemPage";
import { getBrands, createBrand } from "./api";
import "./App.css";
import SettingsPage from "./pages/SettingsPage";

export default function App() {
  const [brands, setBrands] = useState([]);
  const [selectedBrandId, setSelectedBrandId] = useState(() => {
    return localStorage.getItem("selectedBrandId") || null;
  });
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  
  // Yeni Marka Form Değişkenleri
  const [newBrandName, setNewBrandName] = useState("");
  const [newBrandPrimaryColor, setNewBrandPrimaryColor] = useState("#005f56");
  const [newBrandTarget, setNewBrandTarget] = useState("");
  const [newBrandCompetitors, setNewBrandCompetitors] = useState("");

  // Sayfa yüklendiğinde markaları veritabanından çek
  useEffect(() => {
    getBrands().then((data) => {
      setBrands(data);
      // Eğer hafızada marka yoksa ve data geldiyse ilk markayı seç
      if (data.length > 0 && !selectedBrandId) {
        setSelectedBrandId(data[0].id);
        localStorage.setItem("selectedBrandId", data[0].id);
      }
    }).catch(err => console.error("Markalar yüklenemedi", err));
  }, [selectedBrandId]);

  // Marka Değiştirme Aksiyonu
  const handleBrandSelect = (id) => {
    setSelectedBrandId(id);
    localStorage.setItem("selectedBrandId", id);
    setIsDropdownOpen(false);
    // Marka değiştiğinde verilerin o markaya göre tazelenmesi için sayfayı yeniliyoruz
    window.location.href = "/"; 
  };

  // Yeni Marka Ekleme Aksiyonu
  const handleAddBrand = async () => {
    if (!newBrandName.trim()) return;
    
    // Virgülle ayrılmış rakipleri diziye (array) çevir
    const compArray = newBrandCompetitors.split(",").map(c => c.trim()).filter(c => c);

    const brandData = {
      name: newBrandName,
      brand_details: { 
        name: newBrandName, 
        target_audience: newBrandTarget || "Genel Kitle" 
      },
      visual_identity: { 
        primary_color: newBrandPrimaryColor,
        typography: { primary: "sans-serif" }
      },
      social_media: { 
        competitors: compArray 
      }
    };

    try {
      const res = await createBrand(brandData);
      const newBrands = [...brands, { id: res.brand_id, name: res.name }];
      setBrands(newBrands);
      handleBrandSelect(res.brand_id); // Eklenen markayı hemen seç
      setIsModalOpen(false);
      
      // Formu temizle
      setNewBrandName(""); 
      setNewBrandPrimaryColor("#005f56"); 
      setNewBrandTarget(""); 
      setNewBrandCompetitors("");
    } catch (error) {
      alert("Marka eklenirken hata oluştu.");
    }
  };

  const selectedBrand = brands.find(b => b.id == selectedBrandId) || { name: "Yükleniyor..." };

  return (
    <BrowserRouter>
      <div className="app-shell">
        <nav className="sidebar">
          
          {/* --- MARKA SEÇİCİ (BRAND SWITCHER) --- */}
          <div className="brand-switcher-container">
            <div 
              className="brand-selector" 
              onClick={() => setIsDropdownOpen(!isDropdownOpen)}
            >
              <div className="brand-name-display">
                <span className="brand-icon">✦</span>
                <span className="brand-text">{selectedBrand.name}</span>
              </div>
              <span className="dropdown-arrow">{isDropdownOpen ? "▲" : "▼"}</span>
            </div>
            
            {isDropdownOpen && (
              <div className="brand-dropdown-menu">
                {brands.map(brand => (
                  <div 
                    key={brand.id} 
                    className={`brand-option ${brand.id == selectedBrandId ? 'active' : ''}`}
                    onClick={() => handleBrandSelect(brand.id)}
                  >
                    {brand.name}
                  </div>
                ))}
                <div className="brand-option add-new" onClick={() => {setIsDropdownOpen(false); setIsModalOpen(true);}}>
                  + Yeni Marka Ekle
                </div>
              </div>
            )}
          </div>
          {/* ------------------------------------- */}

          <NavLink to="/" end className={({ isActive }) => isActive ? "nav-item active" : "nav-item"}>
            📅 Calendar
          </NavLink>
          {/* YENİ EKLENEN SETTINGS MENÜSÜ */}
          <NavLink to="/settings" className={({ isActive }) => isActive ? "nav-item active" : "nav-item"}>
            ⚙️ Settings
          </NavLink>
        </nav>

        <main className="main-content">
          <Routes>
            <Route path="/" element={<CalendarPage />} />
            <Route path="/item/:year/:month/:id" element={<ItemPage />} />
            {/* YENİ EKLENEN SETTINGS SAYFASI */}
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </main>

        {/* --- YENİ MARKA EKLEME MODALI --- */}
        {isModalOpen && (
          <div className="modal-overlay">
            <div className="modal-content">
              <h3>Yeni Marka Tanımla</h3>
              <p style={{fontSize: "13px", color: "gray", marginBottom: "16px"}}>Markanın kurumsal kimliğini ve rakiplerini belirleyin.</p>
              
              <div style={{marginBottom: "12px"}}>
                <label style={{display:"block", fontSize:"12px", fontWeight:"bold", marginBottom:"4px"}}>Marka Adı</label>
                <input type="text" placeholder="Örn: Marka Adı" value={newBrandName} onChange={(e) => setNewBrandName(e.target.value)} className="modal-input" style={{marginBottom:0}}/>
              </div>

              <div style={{marginBottom: "12px"}}>
                <label style={{display:"block", fontSize:"12px", fontWeight:"bold", marginBottom:"4px"}}>Kurumsal Renk (Hex)</label>
                <div style={{display: "flex", gap: "10px"}}>
                    <input type="color" value={newBrandPrimaryColor} onChange={(e) => setNewBrandPrimaryColor(e.target.value)} style={{height: "40px", cursor:"pointer"}}/>
                    <input type="text" value={newBrandPrimaryColor} onChange={(e) => setNewBrandPrimaryColor(e.target.value)} className="modal-input" style={{marginBottom:0, flex:1}}/>
                </div>
              </div>

              <div style={{marginBottom: "12px"}}>
                <label style={{display:"block", fontSize:"12px", fontWeight:"bold", marginBottom:"4px"}}>Hedef Kitle</label>
                <input type="text" placeholder="Örn: Türkiye'deki IK Yöneticileri" value={newBrandTarget} onChange={(e) => setNewBrandTarget(e.target.value)} className="modal-input" style={{marginBottom:0}}/>
              </div>

              <div style={{marginBottom: "20px"}}>
                <label style={{display:"block", fontSize:"12px", fontWeight:"bold", marginBottom:"4px"}}>Rakipler (Virgülle ayırın)</label>
                <input type="text" placeholder="Örn: KolayIK, Logo Yazılım" value={newBrandCompetitors} onChange={(e) => setNewBrandCompetitors(e.target.value)} className="modal-input" style={{marginBottom:0}}/>
              </div>

              <div className="modal-actions">
                <button onClick={() => setIsModalOpen(false)} className="btn-cancel">İptal</button>
                <button onClick={handleAddBrand} className="btn-save">Markayı Yarat</button>
              </div>
            </div>
          </div>
        )}
        {/* -------------------------------- */}

      </div>
    </BrowserRouter>
  );
}