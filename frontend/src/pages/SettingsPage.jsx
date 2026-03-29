import { useState, useEffect, useRef } from "react";
import { getBrand, updateBrand, deleteBrand, duplicateBrand, uploadLogo, uploadBrandAsset, assessBrand } from "../api";

export default function SettingsPage() {
  const brandId = localStorage.getItem("selectedBrandId");
  const [loading, setLoading] = useState(true);
  
  const logoInputRef = useRef(null);
  const elementInputRef = useRef(null);
  
  // Form States
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [targetAudience, setTargetAudience] = useState("");
  const [language, setLanguage] = useState("English");
  const [logoUrl, setLogoUrl] = useState("");
  const [brandElementUrl, setBrandElementUrl] = useState(""); // YENİ: Marka Filigranı/Öğesi
  
  // Dynamic Arrays
  const [competitors, setCompetitors] = useState([""]);
  const [corporateColors, setCorporateColors] = useState(["#005f56"]);
  const [backgroundColors, setBackgroundColors] = useState([]);

  // AI Assessment
  const [aiAssessment, setAiAssessment] = useState("");
  const [assessing, setAssessing] = useState(false);

  useEffect(() => {
    if (brandId) {
      getBrand(brandId).then(data => {
        setName(data.name || "");
        setDescription(data.brand_details?.description || "");
        setTargetAudience(data.brand_details?.target_audience || "");
        setLanguage(data.brand_details?.language || "English");
        
        setLogoUrl(data.visual_identity?.logo_url || "");
        setBrandElementUrl(data.visual_identity?.brand_element_url || ""); // Veritabanından çek
        
        setCompetitors(data.social_media?.competitors?.length ? data.social_media.competitors : [""]);
        setCorporateColors(data.visual_identity?.corporate_colors?.length ? data.visual_identity.corporate_colors : ["#005f56"]);
        setBackgroundColors(data.visual_identity?.background_colors || []);
        setLoading(false);
      });
    }
  }, [brandId]);

  const handleArrayChange = (setter, array, index, value) => {
    const newArr = [...array];
    newArr[index] = value;
    setter(newArr);
  };
  const addArrayItem = (setter, array, defaultValue = "") => setter([...array, defaultValue]);
  const removeArrayItem = (setter, array, index) => setter(array.filter((_, i) => i !== index));

  const handleLogoUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    try {
      const res = await uploadLogo(file);
      setLogoUrl(res.url);
    } catch (err) { alert("Logo upload failed."); }
  };

  // YENİ: Marka öğesi yükleme fonksiyonu
  const handleElementUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    try {
      const res = await uploadBrandAsset(file);
      setBrandElementUrl(res.url);
    } catch (err) { alert("Brand element upload failed."); }
  };

  const handleAssess = async () => {
    setAssessing(true);
    setAiAssessment("");
    try {
      const res = await assessBrand({ brand_name: name, description, target_audience: targetAudience, competitors: competitors.filter(c => c.trim() !== "") });
      setAiAssessment(res.assessment);
    } catch (err) { alert("AI assessment failed."); }
    setAssessing(false);
  };

  const handleSave = async () => {
    const brandData = {
      name,
      brand_details: { name, description, target_audience: targetAudience, language },
      visual_identity: { 
        logo_url: logoUrl,
        brand_element_url: brandElementUrl, // JSON'a ekleniyor
        corporate_colors: corporateColors.filter(c => c.trim() !== ""),
        background_colors: backgroundColors.filter(c => c.trim() !== ""),
        primary_color: corporateColors[0] || "#005f56" 
      },
      social_media: { competitors: competitors.filter(c => c.trim() !== "") }
    };

    try {
      await updateBrand(brandId, brandData);
      alert("Settings saved successfully!");
      window.location.reload(); 
    } catch (e) { alert("Error saving settings"); }
  };

  if (loading) return <div style={{padding: "40px", color: "#333"}}>Loading Settings...</div>;

  const labelStyle = { display: "block", fontSize: "14px", fontWeight: "600", color: "#374151", marginBottom: "8px" };
  const inputStyle = { flex: 1, padding: "10px 14px", borderRadius: "8px", border: "1px solid #d1d5db", fontSize: "14px", color: "#111827", backgroundColor: "#f9fafb" };
  const cardStyle = { backgroundColor: "#ffffff", borderRadius: "12px", padding: "32px", marginBottom: "24px", boxShadow: "0 1px 3px rgba(0,0,0,0.1)", border: "1px solid #e5e7eb" };
  const btnStyle = { padding: "10px 16px", background: "#f3f4f6", border: "1px solid #d1d5db", borderRadius: "8px", cursor: "pointer", fontWeight: "600", color: "#374151" };

  return (
    <div style={{ padding: "40px", maxWidth: "900px", margin: "0 auto", fontFamily: "system-ui, -apple-system, sans-serif" }}>
      
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "32px" }}>
        <div>
          <h1 style={{ margin: "0 0 8px 0", color: "#111827", fontSize: "32px", fontWeight: "800" }}>Brand Settings</h1>
        </div>
      </div>

      <div style={cardStyle}>
        <h2 style={{ fontSize: "18px", fontWeight: "700", borderBottom: "1px solid #e5e7eb", paddingBottom: "12px", marginBottom: "24px" }}>1. Brand Profile</h2>
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          <div><label style={labelStyle}>Brand Name</label><input type="text" value={name} onChange={e => setName(e.target.value)} style={{...inputStyle, width: "100%"}} /></div>
          <div><label style={labelStyle}>Brand Description (What does it do?)</label><textarea value={description} onChange={e => setDescription(e.target.value)} style={{ ...inputStyle, width: "100%", minHeight: "100px" }} /></div>
        </div>
      </div>

      <div style={cardStyle}>
        <h2 style={{ fontSize: "18px", fontWeight: "700", borderBottom: "1px solid #e5e7eb", paddingBottom: "12px", marginBottom: "24px" }}>2. Strategy & Audience</h2>
        <div style={{ display: "flex", gap: "24px", marginBottom: "20px" }}>
          <div style={{ flex: 2 }}><label style={labelStyle}>Target Audience</label><input type="text" value={targetAudience} onChange={e => setTargetAudience(e.target.value)} style={{...inputStyle, width: "100%"}} /></div>
          <div style={{ flex: 1 }}><label style={labelStyle}>Audience Language</label>
            <select value={language} onChange={e => setLanguage(e.target.value)} style={{...inputStyle, width: "100%", cursor: "pointer"}}>
              <option value="English">English</option><option value="Turkish">Turkish</option><option value="German">German</option>
            </select>
          </div>
        </div>
      </div>

      <div style={cardStyle}>
        <h2 style={{ fontSize: "18px", fontWeight: "700", borderBottom: "1px solid #e5e7eb", paddingBottom: "12px", marginBottom: "24px" }}>3. Visual Identity & Assets</h2>
        
        <div style={{ display: "flex", gap: "40px", marginBottom: "30px" }}>
          <div style={{ flex: 1 }}>
            <label style={labelStyle}>Brand Logo</label>
            <div style={{ display: "flex", alignItems: "center", gap: "15px" }}>
              {logoUrl && <img src={logoUrl} alt="Logo" style={{ height: "50px", width: "50px", objectFit: "contain", border: "1px solid #e5e7eb", borderRadius: "8px" }} />}
              <input type="file" ref={logoInputRef} onChange={handleLogoUpload} accept="image/*" style={{ display: "none" }} />
              <button onClick={() => logoInputRef.current.click()} style={btnStyle}>Upload Logo</button>
            </div>
          </div>
          <div style={{ flex: 1 }}>
            <label style={labelStyle}>Brand Element / Watermark (Optional)</label>
            <div style={{ display: "flex", alignItems: "center", gap: "15px" }}>
              {brandElementUrl && <img src={brandElementUrl} alt="Element" style={{ height: "50px", width: "50px", objectFit: "contain", border: "1px solid #e5e7eb", borderRadius: "8px" }} />}
              <input type="file" ref={elementInputRef} onChange={handleElementUpload} accept="image/*" style={{ display: "none" }} />
              <button onClick={() => elementInputRef.current.click()} style={btnStyle}>Upload Shape</button>
            </div>
          </div>
        </div>

        <div style={{ display: "flex", gap: "40px" }}>
          <div style={{ flex: 1 }}>
            <label style={labelStyle}>Corporate Colors</label>
            {corporateColors.map((color, idx) => (
              <div key={idx} style={{ display: "flex", gap: "10px", marginBottom: "10px" }}>
                <input type="color" value={color} onChange={(e) => handleArrayChange(setCorporateColors, corporateColors, idx, e.target.value)} style={{ width: "45px", height: "45px", border: "none", cursor: "pointer" }} />
                <input type="text" value={color} onChange={(e) => handleArrayChange(setCorporateColors, corporateColors, idx, e.target.value)} style={inputStyle} />
              </div>
            ))}
            <button onClick={() => addArrayItem(setCorporateColors, corporateColors, "#000000")} style={{...btnStyle, padding: "6px 10px", fontSize: "12px"}}>+ Add Color</button>
          </div>

          <div style={{ flex: 1 }}>
            <label style={labelStyle}>Background Colors</label>
            {backgroundColors.map((color, idx) => (
              <div key={idx} style={{ display: "flex", gap: "10px", marginBottom: "10px" }}>
                <input type="color" value={color} onChange={(e) => handleArrayChange(setBackgroundColors, backgroundColors, idx, e.target.value)} style={{ width: "45px", height: "45px", border: "none", cursor: "pointer" }} />
                <input type="text" value={color} onChange={(e) => handleArrayChange(setBackgroundColors, backgroundColors, idx, e.target.value)} style={inputStyle} />
              </div>
            ))}
            <button onClick={() => addArrayItem(setBackgroundColors, backgroundColors, "#ffffff")} style={{...btnStyle, padding: "6px 10px", fontSize: "12px"}}>+ Add Background Color</button>
          </div>
        </div>
      </div>

      <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: "60px" }}>
        <button onClick={handleSave} style={{ padding: "14px 32px", backgroundColor: "#047857", color: "white", border: "none", borderRadius: "8px", cursor: "pointer", fontSize: "16px", fontWeight: "700" }}>
          Save Brand Settings
        </button>
      </div>

    </div>
  );
}