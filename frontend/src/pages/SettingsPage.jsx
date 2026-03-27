import { useState, useEffect, useRef } from "react";
import { getBrand, updateBrand, deleteBrand, duplicateBrand, uploadLogo, assessBrand } from "../api";

export default function SettingsPage() {
  const brandId = localStorage.getItem("selectedBrandId");
  const [loading, setLoading] = useState(true);
  const fileInputRef = useRef(null);
  
  // Form States
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [targetAudience, setTargetAudience] = useState("");
  const [language, setLanguage] = useState("English");
  const [logoUrl, setLogoUrl] = useState("");
  
  // Dynamic Arrays
  const [competitors, setCompetitors] = useState([""]);
  const [corporateColors, setCorporateColors] = useState(["#005f56"]);
  const [backgroundColors, setBackgroundColors] = useState([]);

  // AI Assessment State
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
        
        setCompetitors(data.social_media?.competitors?.length ? data.social_media.competitors : [""]);
        setCorporateColors(data.visual_identity?.corporate_colors?.length ? data.visual_identity.corporate_colors : ["#005f56"]);
        setBackgroundColors(data.visual_identity?.background_colors || []);
        setLoading(false);
      });
    }
  }, [brandId]);

  // --- Dinamik Liste Yönetimi ---
  const handleArrayChange = (setter, array, index, value) => {
    const newArr = [...array];
    newArr[index] = value;
    setter(newArr);
  };
  const addArrayItem = (setter, array, defaultValue = "") => setter([...array, defaultValue]);
  const removeArrayItem = (setter, array, index) => setter(array.filter((_, i) => i !== index));

  // --- Logo Upload ---
  const handleLogoUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    try {
      const res = await uploadLogo(file);
      setLogoUrl(res.url);
    } catch (err) { alert("Logo upload failed."); }
  };

  // --- Yapay Zeka Testi ---
  const handleAssess = async () => {
    setAssessing(true);
    setAiAssessment("");
    try {
      const res = await assessBrand({ brand_name: name, description, target_audience: targetAudience, competitors: competitors.filter(c => c.trim() !== "") });
      setAiAssessment(res.assessment);
    } catch (err) { alert("AI assessment failed."); }
    setAssessing(false);
  };

  // --- Kaydetme ---
  const handleSave = async () => {
    const brandData = {
      name,
      brand_details: { name, description, target_audience: targetAudience, language },
      visual_identity: { 
        logo_url: logoUrl,
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

  const handleDelete = async () => {
    if (window.confirm("Are you sure you want to delete this brand?")) {
      await deleteBrand(brandId);
      localStorage.removeItem("selectedBrandId");
      window.location.href = "/";
    }
  };

  if (loading) return <div style={{padding: "40px", color: "#333"}}>Loading Settings...</div>;

  // --- Stiller ---
  const labelStyle = { display: "block", fontSize: "14px", fontWeight: "600", color: "#374151", marginBottom: "8px" };
  const inputStyle = { flex: 1, padding: "10px 14px", borderRadius: "8px", border: "1px solid #d1d5db", fontSize: "14px", color: "#111827", backgroundColor: "#f9fafb" };
  const cardStyle = { backgroundColor: "#ffffff", borderRadius: "12px", padding: "32px", marginBottom: "24px", boxShadow: "0 1px 3px rgba(0,0,0,0.1)", border: "1px solid #e5e7eb" };
  const btnAddStyle = { padding: "8px 12px", background: "#e5e7eb", border: "none", borderRadius: "6px", cursor: "pointer", fontSize: "12px", fontWeight: "bold", color: "#374151", marginTop: "10px" };
  const btnRemoveStyle = { padding: "10px", background: "#fee2e2", color: "#dc2626", border: "none", borderRadius: "8px", cursor: "pointer", fontWeight: "bold" };

  return (
    <div style={{ padding: "40px", maxWidth: "900px", margin: "0 auto", fontFamily: "system-ui, -apple-system, sans-serif" }}>
      
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "32px" }}>
        <div>
          <h1 style={{ margin: "0 0 8px 0", color: "#111827", fontSize: "32px", fontWeight: "800" }}>Brand Settings</h1>
          <p style={{ margin: 0, color: "#6b7280", fontSize: "15px" }}>Configure AI parameters, audience, and visual identity for <strong>{name}</strong>.</p>
        </div>
        <div style={{ display: "flex", gap: "12px" }}>
          <button onClick={async () => { const r = await duplicateBrand(brandId); localStorage.setItem("selectedBrandId", r.brand_id); window.location.href="/settings"; }} style={{ padding: "10px 18px", backgroundColor: "#f3f4f6", color: "#374151", border: "1px solid #d1d5db", borderRadius: "8px", cursor: "pointer", fontWeight: "600" }}>Copy Brand</button>
          <button onClick={handleDelete} style={{ padding: "10px 18px", backgroundColor: "#fef2f2", color: "#dc2626", border: "1px solid #fecaca", borderRadius: "8px", cursor: "pointer", fontWeight: "600" }}>Delete Brand</button>
        </div>
      </div>

      {/* 1. Brand Profile */}
      <div style={cardStyle}>
        <h2 style={{ fontSize: "18px", fontWeight: "700", borderBottom: "1px solid #e5e7eb", paddingBottom: "12px", marginBottom: "24px" }}>1. Brand Profile</h2>
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          <div>
            <label style={labelStyle}>Brand Name</label>
            <input type="text" value={name} onChange={e => setName(e.target.value)} style={{...inputStyle, width: "100%"}} />
          </div>
          <div>
            <label style={labelStyle}>Brand Description (What does it do?)</label>
            <textarea value={description} onChange={e => setDescription(e.target.value)} placeholder="Explain the product, features, and tone..." style={{ ...inputStyle, width: "100%", minHeight: "100px", resize: "vertical" }} />
          </div>
        </div>
      </div>

      {/* 2. Strategy & Audience */}
      <div style={cardStyle}>
        <h2 style={{ fontSize: "18px", fontWeight: "700", borderBottom: "1px solid #e5e7eb", paddingBottom: "12px", marginBottom: "24px" }}>2. Strategy & Audience</h2>
        <div style={{ display: "flex", gap: "24px", marginBottom: "20px" }}>
          <div style={{ flex: 2 }}>
            <label style={labelStyle}>Target Audience</label>
            <input type="text" value={targetAudience} onChange={e => setTargetAudience(e.target.value)} placeholder="e.g. HR Managers in Europe" style={{...inputStyle, width: "100%"}} />
          </div>
          <div style={{ flex: 1 }}>
            <label style={labelStyle}>Audience Language</label>
            <select value={language} onChange={e => setLanguage(e.target.value)} style={{...inputStyle, width: "100%", cursor: "pointer"}}>
              <option value="English">English</option>
              <option value="Turkish">Turkish</option>
              <option value="German">German</option>
              <option value="Spanish">Spanish</option>
            </select>
          </div>
        </div>
        
        <div>
          <label style={labelStyle}>Competitors</label>
          {competitors.map((comp, idx) => (
            <div key={idx} style={{ display: "flex", gap: "10px", marginBottom: "10px" }}>
              <input type="text" value={comp} onChange={(e) => handleArrayChange(setCompetitors, competitors, idx, e.target.value)} placeholder="Competitor Name or URL" style={inputStyle} />
              {competitors.length > 1 && <button onClick={() => removeArrayItem(setCompetitors, competitors, idx)} style={btnRemoveStyle}>X</button>}
            </div>
          ))}
          <button onClick={() => addArrayItem(setCompetitors, competitors)} style={btnAddStyle}>+ Add Competitor</button>
        </div>
      </div>

      {/* 3. Visual Identity */}
      <div style={cardStyle}>
        <h2 style={{ fontSize: "18px", fontWeight: "700", borderBottom: "1px solid #e5e7eb", paddingBottom: "12px", marginBottom: "24px" }}>3. Visual Identity</h2>
        
        <div style={{ marginBottom: "24px" }}>
          <label style={labelStyle}>Brand Logo</label>
          <div style={{ display: "flex", alignItems: "center", gap: "20px" }}>
            {logoUrl && <img src={logoUrl} alt="Logo" style={{ height: "60px", width: "60px", objectFit: "contain", background: "#f9fafb", border: "1px solid #e5e7eb", borderRadius: "8px", padding: "4px" }} />}
            <input type="file" ref={fileInputRef} onChange={handleLogoUpload} accept="image/*" style={{ display: "none" }} />
            <button onClick={() => fileInputRef.current.click()} style={{ padding: "10px 16px", background: "#f3f4f6", border: "1px solid #d1d5db", borderRadius: "8px", cursor: "pointer", fontWeight: "600", color: "#374151" }}>Upload Logo File</button>
          </div>
        </div>

        <div style={{ display: "flex", gap: "40px" }}>
          {/* Corporate Colors */}
          <div style={{ flex: 1 }}>
            <label style={labelStyle}>Corporate Colors</label>
            {corporateColors.map((color, idx) => (
              <div key={idx} style={{ display: "flex", gap: "10px", marginBottom: "10px" }}>
                <input type="color" value={color} onChange={(e) => handleArrayChange(setCorporateColors, corporateColors, idx, e.target.value)} style={{ width: "45px", height: "45px", padding: "0", border: "none", borderRadius: "8px", cursor: "pointer" }} />
                <input type="text" value={color} onChange={(e) => handleArrayChange(setCorporateColors, corporateColors, idx, e.target.value)} style={inputStyle} />
                {corporateColors.length > 1 && <button onClick={() => removeArrayItem(setCorporateColors, corporateColors, idx)} style={btnRemoveStyle}>X</button>}
              </div>
            ))}
            <button onClick={() => addArrayItem(setCorporateColors, corporateColors, "#000000")} style={btnAddStyle}>+ Add Color</button>
          </div>

          {/* Background Colors */}
          <div style={{ flex: 1 }}>
            <label style={labelStyle}>Background Colors (Optional)</label>
            {backgroundColors.map((color, idx) => (
              <div key={idx} style={{ display: "flex", gap: "10px", marginBottom: "10px" }}>
                <input type="color" value={color} onChange={(e) => handleArrayChange(setBackgroundColors, backgroundColors, idx, e.target.value)} style={{ width: "45px", height: "45px", padding: "0", border: "none", borderRadius: "8px", cursor: "pointer" }} />
                <input type="text" value={color} onChange={(e) => handleArrayChange(setBackgroundColors, backgroundColors, idx, e.target.value)} style={inputStyle} />
                <button onClick={() => removeArrayItem(setBackgroundColors, backgroundColors, idx)} style={btnRemoveStyle}>X</button>
              </div>
            ))}
            <button onClick={() => addArrayItem(setBackgroundColors, backgroundColors, "#ffffff")} style={btnAddStyle}>+ Add Background Color</button>
          </div>
        </div>
      </div>

      {/* 4. AI Assessment (Senin Harika Fikrin!) */}
      <div style={{ ...cardStyle, backgroundColor: "#f0fdfa", borderColor: "#ccfbf1" }}>
        <h2 style={{ fontSize: "18px", fontWeight: "700", color: "#0f766e", marginBottom: "12px" }}>4. AI Understanding Check</h2>
        <p style={{ color: "#0f766e", fontSize: "14px", marginBottom: "20px" }}>Test if the AI correctly understands your brand based on the inputs above before generating content.</p>
        
        {aiAssessment ? (
          <div style={{ padding: "16px", backgroundColor: "white", borderRadius: "8px", border: "1px solid #99f6e4", color: "#111827", fontSize: "15px", lineHeight: "1.6", fontStyle: "italic" }}>
            "{aiAssessment}"
          </div>
        ) : (
          <button onClick={handleAssess} disabled={assessing || !description} style={{ padding: "10px 20px", background: description ? "#0d9488" : "#99f6e4", color: "white", border: "none", borderRadius: "8px", cursor: description ? "pointer" : "not-allowed", fontWeight: "bold" }}>
            {assessing ? "AI is analyzing..." : "Run AI Test"}
          </button>
        )}
      </div>

      {/* Save Button */}
      <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: "60px" }}>
        <button onClick={handleSave} style={{ padding: "14px 32px", backgroundColor: "#047857", color: "white", border: "none", borderRadius: "8px", cursor: "pointer", fontSize: "16px", fontWeight: "700", boxShadow: "0 4px 6px -1px rgba(4, 120, 87, 0.4)" }}>
          Save Brand Settings
        </button>
      </div>

    </div>
  );
}