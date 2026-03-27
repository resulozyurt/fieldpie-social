import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import { useState, useEffect } from "react";
import CalendarPage from "./pages/CalendarPage";
import ItemPage from "./pages/ItemPage";
import { getBrands, createBrand } from "./api";
import "./App.css";

export default function App() {
  const [brands, setBrands] = useState([]);
  const [selectedBrandId, setSelectedBrandId] = useState(() => {
    return localStorage.getItem("selectedBrandId") || null;
  });
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newBrandName, setNewBrandName] = useState("");

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
    try {
      const res = await createBrand({ name: newBrandName });
      const newBrands = [...brands, { id: res.brand_id, name: res.name }];
      setBrands(newBrands);
      handleBrandSelect(res.brand_id); // Eklenen markayı hemen seç
      setIsModalOpen(false);
      setNewBrandName("");
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
        </nav>

        <main className="main-content">
          <Routes>
            <Route path="/" element={<CalendarPage />} />
            <Route path="/item/:year/:month/:id" element={<ItemPage />} />
          </Routes>
        </main>

        {/* --- YENİ MARKA EKLEME MODALI --- */}
        {isModalOpen && (
          <div className="modal-overlay">
            <div className="modal-content">
              <h3>Yeni Marka Ekle</h3>
              <p style={{fontSize: "13px", color: "gray", marginBottom: "16px"}}>Sisteme Evatro veya başka bir müşteri tanımlayın.</p>
              <input 
                type="text" 
                placeholder="Marka Adı (Örn: Evatro)" 
                value={newBrandName}
                onChange={(e) => setNewBrandName(e.target.value)}
                className="modal-input"
              />
              <div className="modal-actions">
                <button onClick={() => setIsModalOpen(false)} className="btn-cancel">İptal</button>
                <button onClick={handleAddBrand} className="btn-save">Ekle</button>
              </div>
            </div>
          </div>
        )}
        {/* -------------------------------- */}

      </div>
    </BrowserRouter>
  );
}