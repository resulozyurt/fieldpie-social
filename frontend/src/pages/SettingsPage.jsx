import { useState, useEffect } from "react";
import { getBrand, updateBrand, deleteBrand, duplicateBrand } from "../api";

export default function SettingsPage() {
  const brandId = localStorage.getItem("selectedBrandId");
  const [loading, setLoading] = useState(true);
  
  // Form States
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [targetAudience, setTargetAudience] = useState("");
  const [language, setLanguage] = useState("English");
  const [competitors, setCompetitors] = useState("");
  const [logoUrl, setLogoUrl] = useState("");
  const [corporateColors, setCorporateColors] = useState("");
  const [backgroundColors, setBackgroundColors] = useState("");

  useEffect(() => {
    if (brandId) {
      getBrand(brandId).then(data => {
        setName(data.name || "");
        setDescription(data.brand_details?.description || "");
        setTargetAudience(data.brand_details?.target_audience || "");
        setLanguage(data.brand_details?.language || "English");
        setLogoUrl(data.visual_identity?.logo_url || "");
        
        setCompetitors((data.social_media?.competitors || []).join(", "));
        setCorporateColors((data.visual_identity?.corporate_colors || []).join(", "));
        setBackgroundColors((data.visual_identity?.background_colors || []).join(", "));
        setLoading(false);
      });
    }
  }, [brandId]);

  const handleSave = async () => {
    const brandData = {
      name,
      brand_details: { name, description, target_audience: targetAudience, language },
      visual_identity: { 
        logo_url: logoUrl,
        corporate_colors: corporateColors.split(",").map(c => c.trim()).filter(c => c),
        background_colors: backgroundColors.split(",").map(c => c.trim()).filter(c => c),
        primary_color: corporateColors.split(",")[0]?.trim() || "#005f56" 
      },
      social_media: { competitors: competitors.split(",").map(c => c.trim()).filter(c => c) }
    };

    try {
      await updateBrand(brandId, brandData);
      alert("Settings saved successfully!");
      window.location.reload(); 
    } catch (e) { alert("Error saving settings"); }
  };

  const handleDelete = async () => {
    if (window.confirm("Are you sure you want to delete this brand? This action cannot be undone.")) {
      await deleteBrand(brandId);
      localStorage.removeItem("selectedBrandId");
      window.location.href = "/";
    }
  };

  const handleDuplicate = async () => {
    if (window.confirm("Duplicate this brand configuration?")) {
      const res = await duplicateBrand(brandId);
      localStorage.setItem("selectedBrandId", res.brand_id);
      window.location.href = "/settings";
    }
  };

  if (loading) return <div style={{padding: "40px", color: "#333"}}>Loading Settings...</div>;

  // --- Ortak Stil Objeleri (Clean UI) ---
  const labelStyle = { display: "block", fontSize: "14px", fontWeight: "600", color: "#374151", marginBottom: "8px" };
  const inputStyle = { width: "100%", padding: "12px 16px", borderRadius: "8px", border: "1px solid #d1d5db", fontSize: "14px", color: "#111827", backgroundColor: "#f9fafb", boxSizing: "border-box", transition: "all 0.2s" };
  const cardStyle = { backgroundColor: "#ffffff", borderRadius: "12px", padding: "32px", marginBottom: "24px", boxShadow: "0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06)", border: "1px solid #e5e7eb" };
  const sectionHeaderStyle = { fontSize: "18px", fontWeight: "700", color: "#111827", marginBottom: "24px", borderBottom: "1px solid #e5e7eb", paddingBottom: "12px" };

  return (
    <div style={{ padding: "40px", maxWidth: "900px", margin: "0 auto", fontFamily: "system-ui, -apple-system, sans-serif" }}>
      
      {/* Header Alani */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "32px" }}>
        <div>
          <h1 style={{ margin: "0 0 8px 0", color: "#111827", fontSize: "32px", fontWeight: "800", letterSpacing: "-0.5px" }}>Brand Settings</h1>
          <p style={{ margin: 0, color: "#6b7280", fontSize: "15px" }}>Configure AI parameters, audience, and visual identity for <strong>{name}</strong>.</p>
        </div>
        <div style={{ display: "flex", gap: "12px" }}>
          <button onClick={handleDuplicate} style={{ padding: "10px 18px", backgroundColor: "#f3f4f6", color: "#374151", border: "1px solid #d1d5db", borderRadius: "8px", cursor: "pointer", fontWeight: "600", transition: "all 0.2s" }} onMouseOver={e => e.target.style.backgroundColor="#e5e7eb"} onMouseOut={e => e.target.style.backgroundColor="#f3f4f6"}>Copy Brand</button>
          <button onClick={handleDelete} style={{ padding: "10px 18px", backgroundColor: "#fef2f2", color: "#dc2626", border: "1px solid #fecaca", borderRadius: "8px", cursor: "pointer", fontWeight: "600", transition: "all 0.2s" }} onMouseOver={e => e.target.style.backgroundColor="#fee2e2"} onMouseOut={e => e.target.style.backgroundColor="#fef2f2"}>Delete Brand</button>
        </div>
      </div>

      {/* 1. Brand Details Card */}
      <div style={cardStyle}>
        <h2 style={sectionHeaderStyle}>1. Brand Profile</h2>
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          <div>
            <label style={labelStyle}>Brand Name</label>
            <input type="text" value={name} onChange={e => setName(e.target.value)} style={inputStyle} />
          </div>
          <div>
            <label style={labelStyle}>Brand Description <span style={{fontWeight: "normal", color: "#6b7280"}}>(What does it do? Crucial for AI content generation)</span></label>
            <textarea value={description} onChange={e => setDescription(e.target.value)} placeholder="e.g. A cloud-based HR software that helps companies manage employee payroll..." style={{ ...inputStyle, minHeight: "100px", resize: "vertical" }} />
          </div>
        </div>
      </div>

      {/* 2. Strategy & Audience Card */}
      <div style={cardStyle}>
        <h2 style={sectionHeaderStyle}>2. Strategy & Audience</h2>
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          <div style={{ display: "flex", gap: "24px" }}>
            <div style={{ flex: 2 }}>
              <label style={labelStyle}>Target Audience</label>
              <input type="text" value={targetAudience} onChange={e => setTargetAudience(e.target.value)} placeholder="e.g. HR Managers in Europe" style={inputStyle} />
            </div>
            <div style={{ flex: 1 }}>
              <label style={labelStyle}>Audience Language</label>
              <select value={language} onChange={e => setLanguage(e.target.value)} style={{...inputStyle, cursor: "pointer"}}>
                <option value="English">English</option>
                <option value="Turkish">Turkish</option>
                <option value="German">German</option>
                <option value="Spanish">Spanish</option>
              </select>
            </div>
          </div>
          <div>
            <label style={labelStyle}>Competitors <span style={{fontWeight: "normal", color: "#6b7280"}}>(Names or URLs, comma separated)</span></label>
            <input type="text" value={competitors} onChange={e => setCompetitors(e.target.value)} placeholder="e.g. Workday, BambooHR" style={inputStyle} />
          </div>
        </div>
      </div>

      {/* 3. Visual Identity Card */}
      <div style={cardStyle}>
        <h2 style={sectionHeaderStyle}>3. Visual Identity</h2>
        <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
          <div>
            <label style={labelStyle}>Brand Logo URL <span style={{fontWeight: "normal", color: "#6b7280"}}>(For visual overlays)</span></label>
            <input type="text" value={logoUrl} onChange={e => setLogoUrl(e.target.value)} placeholder="https://example.com/logo.png" style={inputStyle} />
          </div>
          <div style={{ display: "flex", gap: "24px" }}>
            <div style={{ flex: 1 }}>
              <label style={labelStyle}>Corporate Colors <span style={{fontWeight: "normal", color: "#6b7280"}}>(Hex, comma separated)</span></label>
              <input type="text" value={corporateColors} onChange={e => setCorporateColors(e.target.value)} placeholder="#005f56, #ffffff" style={inputStyle} />
            </div>
            <div style={{ flex: 1 }}>
              <label style={labelStyle}>Background Colors <span style={{fontWeight: "normal", color: "#6b7280"}}>(Hex, leave empty for AI)</span></label>
              <input type="text" value={backgroundColors} onChange={e => setBackgroundColors(e.target.value)} placeholder="#f4f4f4, #1a1a1a" style={inputStyle} />
            </div>
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "10px", marginBottom: "60px" }}>
        <button onClick={handleSave} style={{ padding: "14px 32px", backgroundColor: "#047857", color: "white", border: "none", borderRadius: "8px", cursor: "pointer", fontSize: "16px", fontWeight: "700", boxShadow: "0 4px 6px -1px rgba(4, 120, 87, 0.4)", transition: "all 0.2s" }} onMouseOver={e => e.target.style.transform="translateY(-2px)"} onMouseOut={e => e.target.style.transform="translateY(0)"}>
          Save Brand Settings
        </button>
      </div>

    </div>
  );
}