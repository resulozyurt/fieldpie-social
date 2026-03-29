from playwright.async_api import async_playwright
import asyncio
from pathlib import Path

async def render_html_to_image(html_content: str, output_path: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1080, "height": 1080})
        
        await page.set_content(html_content)
        await page.wait_for_load_state("networkidle")
        await page.screenshot(path=output_path, type="png")
        await browser.close()

def generate_brand_html(image_url: str, text_on_image: str, brand_context: dict, logo_b64: str = "", element_b64: str = "", layout_type: str = "overlay") -> str:
    brand_name = brand_context.get("name", brand_context.get("brand_details", {}).get("name", ""))
    visuals = brand_context.get("visual_identity", {})
    primary_color = visuals.get("primary_color", "#005f56")
    font_family = visuals.get("typography", {}).get("primary", "sans-serif")

    # Logo HTML (Sol üst)
    top_left_element = f"<img src='{logo_b64}' class='brand-logo' />" if logo_b64 else (f"<div class='brand-badge'>{brand_name}</div>" if brand_name else "")
    
    # Filigran HTML (Sağ alt köşe, opacity: 0.15 ile devasa bir şekilde)
    watermark_html = f"<img src='{element_b64}' class='brand-watermark' />" if element_b64 else ""

    # ŞABLON SEÇİCİ CSS
    layout_css = ""
    html_body = ""

    if layout_type == "split":
        # ŞABLON 1: Üst taraf resim, alt taraf kurumsal renkli solid kutu
        layout_css = f"""
        .split-container {{ display: flex; flex-direction: column; height: 1080px; width: 1080px; }}
        .split-image {{ flex: 5.5; background-image: url('{image_url}'); background-size: cover; background-position: center; position: relative; }}
        .split-text {{ flex: 4.5; background-color: {primary_color}; padding: 60px 80px; position: relative; overflow: hidden; display: flex; align-items: center; }}
        .headline {{ font-size: 64px; font-weight: 900; line-height: 1.15; margin: 0; color: white; letter-spacing: -1px; z-index: 2; }}
        """
        html_body = f"""
        <div class="split-container">
            <div class="split-image">{top_left_element}</div>
            <div class="split-text">
                {watermark_html}
                <h1 class="headline">{text_on_image}</h1>
            </div>
        </div>
        """
    elif layout_type == "card":
        # ŞABLON 2: Tam ekran bulanık resim, ortada Glassmorphism kart
        layout_css = f"""
        body {{ background-image: url('{image_url}'); background-size: cover; background-position: center; display: flex; align-items: center; justify-content: center; }}
        .glass-card {{ background: rgba(255, 255, 255, 0.95); padding: 80px; border-radius: 30px; width: 80%; max-width: 850px; box-shadow: 0 30px 60px rgba(0,0,0,0.3); position: relative; overflow: hidden; display: flex; flex-direction: column; }}
        .headline {{ font-size: 60px; font-weight: 900; line-height: 1.2; margin: 0; color: {primary_color}; z-index: 2; margin-top: 40px; }}
        .brand-logo {{ position: relative !important; top: 0 !important; left: 0 !important; max-height: 60px; filter: none; margin-bottom: 20px; }}
        """
        html_body = f"""
        {top_left_element} <div class="glass-card">
            {watermark_html}
            {f"<img src='{logo_b64}' style='max-height:50px; width:auto; z-index:2; align-self:flex-start;' />" if logo_b64 else ""}
            <h1 class="headline">{text_on_image}</h1>
        </div>
        """
    else:
        # ŞABLON 3 (Varsayılan): Tam ekran resim, alt taraf koyu degrade (Eski Apple tarzımız)
        layout_css = f"""
        body {{ background-image: url('{image_url}'); background-size: cover; background-position: center; display: flex; flex-direction: column; justify-content: flex-end; }}
        .overlay {{ position: absolute; bottom: 0; left: 0; width: 100%; height: 75%; background: linear-gradient(to top, rgba(0,0,0,0.9) 0%, rgba(0,0,0,0.5) 40%, rgba(0,0,0,0) 100%); z-index: 1; }}
        .content-wrapper {{ position: relative; z-index: 2; padding: 80px; color: white; overflow: hidden; }}
        .headline {{ font-size: 72px; font-weight: 900; line-height: 1.15; margin: 0; text-shadow: 0 4px 16px rgba(0,0,0,0.6); letter-spacing: -1px; z-index: 2; position: relative; }}
        """
        html_body = f"""
        {top_left_element}
        <div class="overlay"></div>
        <div class="content-wrapper">
            {watermark_html}
            <h1 class="headline">{text_on_image}</h1>
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@500;800;900&display=swap');
            body {{ margin: 0; padding: 0; width: 1080px; height: 1080px; font-family: 'Montserrat', {font_family}, sans-serif; position: relative; overflow: hidden; }}
            
            /* Evrensel Logo Sınıfı */
            .brand-logo {{ position: absolute; top: 50px; left: 50px; max-height: 55px; max-width: 250px; object-fit: contain; z-index: 10; filter: drop-shadow(0 4px 8px rgba(0,0,0,0.4)); }}
            .brand-badge {{ position: absolute; top: 50px; left: 50px; background-color: {primary_color}; color: #ffffff; padding: 12px 24px; border-radius: 8px; font-size: 18px; font-weight: 800; z-index: 10; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }}
            
            /* Evrensel Filigran Sınıfı (Pie vb. şekiller için) */
            .brand-watermark {{ position: absolute; bottom: -80px; right: -80px; width: 450px; opacity: 0.15; z-index: 1; pointer-events: none; }}
            
            {layout_css}
        </style>
    </head>
    <body>
        {html_body}
    </body>
    </html>
    """
    return html