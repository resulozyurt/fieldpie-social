from playwright.async_api import async_playwright
import asyncio
from pathlib import Path

async def render_html_to_image(html_content: str, output_path: str):
    """
    Görünmez bir tarayıcı açar, HTML/CSS kodunu işler ve 
    1080x1080 çözünürlüğünde profesyonel bir PNG çıktısı alır.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1080, "height": 1080})
        
        # HTML'i sayfaya yükle
        await page.set_content(html_content)
        
        # Fontların ve görsellerin internetten tam inmesini bekle
        await page.wait_for_load_state("networkidle")
        
        # Figma kalitesinde ekran görüntüsünü al ve kaydet
        await page.screenshot(path=output_path, type="png")
        await browser.close()

def generate_brand_html(image_url: str, text_on_image: str, brand_context: dict) -> str:
    """
    Markanın kurumsal kimliğine (renk, font) uygun dinamik HTML/CSS şablonunu oluşturur.
    """
    brand_name = brand_context.get("brand", {}).get("name", "FieldPie")
    visuals = brand_context.get("visual_identity", {})
    primary_color = visuals.get("primary_color", "#005f56")
    font_family = visuals.get("typography", {}).get("primary", "sans-serif")

    # CSS Şablonu (Modern, şık, dergi kapağı kalitesinde)
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700;800&display=swap');
            
            body {{
                margin: 0;
                padding: 0;
                width: 1080px;
                height: 1080px;
                background-image: url('{image_url}');
                background-size: cover;
                background-position: center;
                font-family: 'Montserrat', {font_family}, sans-serif;
                position: relative;
            }}
            
            /* Markaya Özel Metin Kutusu (Modern Cam Efekti veya Şık Kutu) */
            .text-box {{
                position: absolute;
                bottom: 80px;
                left: 80px;
                right: 80px;
                background: rgba(255, 255, 255, 0.95);
                padding: 50px;
                border-radius: 24px;
                border-left: 16px solid {primary_color};
                box-shadow: 0 20px 50px rgba(0,0,0,0.3);
            }}
            
            .brand-badge {{
                font-size: 24px;
                font-weight: 800;
                color: {primary_color};
                text-transform: uppercase;
                letter-spacing: 2px;
                margin-bottom: 20px;
            }}
            
            .headline {{
                font-size: 56px;
                font-weight: 800;
                color: #1a1a1a;
                line-height: 1.2;
                margin: 0;
            }}
        </style>
    </head>
    <body>
        <div class="text-box">
            <div class="brand-badge">{brand_name}</div>
            <h1 class="headline">{text_on_image}</h1>
        </div>
    </body>
    </html>
    """
    return html