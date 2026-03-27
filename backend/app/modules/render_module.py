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
        
        await page.set_content(html_content)
        await page.wait_for_load_state("networkidle")
        await page.screenshot(path=output_path, type="png")
        await browser.close()

def generate_brand_html(image_url: str, text_on_image: str, brand_context: dict) -> str:
    """
    Apple/Nike tarzı: Görselin üzerinde koyu bir degrade (gradient overlay) ile
    maksimum okunabilirlik sağlayan premium, şık ve modern tipografi şablonu.
    """
    brand_name = brand_context.get("brand_details", {}).get("name", "The Brand")
    visuals = brand_context.get("visual_identity", {})
    primary_color = visuals.get("primary_color", "#005f56")
    font_family = visuals.get("typography", {}).get("primary", "sans-serif")

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@500;800;900&display=swap');
            
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
                display: flex;
                flex-direction: column;
                justify-content: flex-end; /* İçeriği en alta yaslar */
            }}
            
            /* Karanlık Degrade: Arka plandaki resim ne olursa olsun beyaz yazının %100 okunmasını sağlar */
            .overlay {{
                position: absolute;
                bottom: 0;
                left: 0;
                width: 100%;
                height: 65%;
                background: linear-gradient(to top, rgba(0,0,0,0.85) 0%, rgba(0,0,0,0.4) 50%, rgba(0,0,0,0) 100%);
                z-index: 1;
            }}

            .content-wrapper {{
                position: relative;
                z-index: 2;
                padding: 80px;
                color: white;
            }}

            /* Markanın Kurumsal Rengini Kullanan Modern Şık Rozet (Badge) */
            .brand-badge {{
                display: inline-block;
                background-color: {primary_color};
                color: #ffffff;
                padding: 14px 28px;
                border-radius: 100px;
                font-size: 22px;
                font-weight: 800;
                letter-spacing: 2px;
                text-transform: uppercase;
                margin-bottom: 30px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.4);
            }}

            /* Scroll Durduran Devasa Başlık */
            .headline {{
                font-size: 72px;
                font-weight: 900;
                line-height: 1.15;
                margin: 0;
                text-shadow: 0 4px 16px rgba(0,0,0,0.5);
                letter-spacing: -1px;
            }}
        </style>
    </head>
    <body>
        <div class="overlay"></div>
        <div class="content-wrapper">
            <div class="brand-badge">{brand_name}</div>
            <h1 class="headline">{text_on_image}</h1>
        </div>
    </body>
    </html>
    """
    return html