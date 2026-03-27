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
        
        // Array to comma-separated string for easy editing
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
        primary_color: corporateColors.split(",")[0]?.trim() || "#005f56" // İlk rengi ana renk yapar
      },
      social_media: { competitors: competitors.split(",").map(c => c.trim()).filter(c => c) }
    };

    try {
      await updateBrand(brandId, brandData);
      alert("Settings saved successfully!");
      window.location.reload(); // Marka adının sol menüde güncellenmesi için
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

  if (loading) return <div style={{padding: "40px", color: "white"}}>Loading Settings...</div>;

  return (
    <div style={{ padding: "40px", maxWidth: "800px", color: "white" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "30px" }}>
        <h1 style={{ margin: 0 }}>Brand Settings</h1>
        <div style={{ display: "flex", gap: "10px" }}>
          <button onClick={handleDuplicate} style={{ padding: "10px 16px", background: "#3b82f6", color: "white", border: "none", borderRadius: "6px", cursor: "pointer", fontWeight: "bold" }}>Duplicate Brand</button>
          <button onClick={handleDelete} style={{ padding: "10px 16px", background: "#ef4444", color: "white", border: "none", borderRadius: "6px", cursor: "pointer", fontWeight: "bold" }}>Delete Brand</button>
        </div>
      </div>

      <div style={{ background: "rgba(255,255,255,0.05)", padding: "30px", borderRadius: "12px", display: "flex", flexDirection: "column", gap: "20px" }}>
        
        <div>
          <label style={{ display: "block", fontSize: "13px", fontWeight: "bold", marginBottom: "6px", color: "#a7f3d0" }}>8. Brand Name</label>
          <input type="text" value={name} onChange={e => setName(e.target.value)} style={{ width: "100%", padding: "12px", borderRadius: "6px", border: "1px solid rgba(255,255,255,0.2)", background: "rgba(0,0,0,0.2)", color: "white" }} />
        </div>

        <div>
          <label style={{ display: "block", fontSize: "13px", fontWeight: "bold", marginBottom: "6px", color: "#a7f3d0" }}>7. Brand Description (What does it do? Crucial for AI)</label>
          <textarea value={description} onChange={e => setDescription(e.target.value)} placeholder="e.g. A cloud-based HR software that helps companies manage employee payroll..." style={{ width: "100%", padding: "12px", borderRadius: "6px", border: "1px solid rgba(255,255,255,0.2)", background: "rgba(0,0,0,0.2)", color: "white", minHeight: "80px" }} />
        </div>

        <div style={{ display: "flex", gap: "20px" }}>
          <div style={{ flex: 1 }}>
            <label style={{ display: "block", fontSize: "13px", fontWeight: "bold", marginBottom: "6px", color: "#a7f3d0" }}>6. Target Audience</label>
            <input type="text" value={targetAudience} onChange={e => setTargetAudience(e.target.value)} placeholder="e.g. HR Managers in Europe" style={{ width: "100%", padding: "12px", borderRadius: "6px", border: "1px solid rgba(255,255,255,0.2)", background: "rgba(0,0,0,0.2)", color: "white" }} />
          </div>
          <div style={{ flex: 1 }}>
            <label style={{ display: "block", fontSize: "13px", fontWeight: "bold", marginBottom: "6px", color: "#a7f3d0" }}>2. Target Audience Language</label>
            <select value={language} onChange={e => setLanguage(e.target.value)} style={{ width: "100%", padding: "12px", borderRadius: "6px", border: "1px solid rgba(255,255,255,0.2)", background: "rgba(0,0,0,0.2)", color: "white" }}>
              <option value="English">English</option>
              <option value="Turkish">Turkish</option>
              <option value="German">German</option>
              <option value="Spanish">Spanish</option>
            </select>
          </div>
        </div>

        <div>
          <label style={{ display: "block", fontSize: "13px", fontWeight: "bold", marginBottom: "6px", color: "#a7f3d0" }}>5. Competitors (Names or URLs, comma separated)</label>
          <input type="text" value={competitors} onChange={e => setCompetitors(e.target.value)} placeholder="e.g. Workday, BambooHR" style={{ width: "100%", padding: "12px", borderRadius: "6px", border: "1px solid rgba(255,255,255,0.2)", background: "rgba(0,0,0,0.2)", color: "white" }} />
        </div>

        <div style={{ display: "flex", gap: "20px" }}>
          <div style={{ flex: 1 }}>
            <label style={{ display: "block", fontSize: "13px", fontWeight: "bold", marginBottom: "6px", color: "#a7f3d0" }}>3. Corporate Colors (Hex codes, comma separated)</label>
            <input type="text" value={corporateColors} onChange={e => setCorporateColors(e.target.value)} placeholder="#005f56, #ffffff" style={{ width: "100%", padding: "12px", borderRadius: "6px", border: "1px solid rgba(255,255,255,0.2)", background: "rgba(0,0,0,0.2)", color: "white" }} />
          </div>
          <div style={{ flex: 1 }}>
            <label style={{ display: "block", fontSize: "13px", fontWeight: "bold", marginBottom: "6px", color: "#a7f3d0" }}>4. Background Colors (Hex, leave empty for AI)</label>
            <input type="text" value={backgroundColors} onChange={e => setBackgroundColors(e.target.value)} placeholder="#f4f4f4, #1a1a1a" style={{ width: "100%", padding: "12px", borderRadius: "6px", border: "1px solid rgba(255,255,255,0.2)", background: "rgba(0,0,0,0.2)", color: "white" }} />
          </div>
        </div>

        <div>
          <label style={{ display: "block", fontSize: "13px", fontWeight: "bold", marginBottom: "6px", color: "#a7f3d0" }}>1. Brand Logo URL (For visual overlays)</label>
          <input type="text" value={logoUrl} onChange={e => setLogoUrl(e.target.value)} placeholder="https://example.com/logo.png" style={{ width: "100%", padding: "12px", borderRadius: "6px", border: "1px solid rgba(255,255,255,0.2)", background: "rgba(0,0,0,0.2)", color: "white" }} />
        </div>

        <div style={{ marginTop: "20px", borderTop: "1px solid rgba(255,255,255,0.1)", paddingTop: "20px", textAlign: "right" }}>
          <button onClick={handleSave} style={{ padding: "14px 28px", background: "#10b981", color: "white", border: "none", borderRadius: "6px", cursor: "pointer", fontSize: "16px", fontWeight: "bold", letterSpacing: "1px" }}>Save Settings</button>
        </div>

      </div>
    </div>
  );
}