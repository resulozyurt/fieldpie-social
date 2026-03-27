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

def generate_brand_html(image_url: str, text_on_image: str, brand_context: dict, logo_b64: str = "") -> str:
    """
    Apple/Nike tarzı tipografi ve sol üstte Logo/Rozet konumu.
    """
    brand_name = brand_context.get("name", brand_context.get("brand_details", {}).get("name", ""))
    visuals = brand_context.get("visual_identity", {})
    primary_color = visuals.get("primary_color", "#005f56")
    font_family = visuals.get("typography", {}).get("primary", "sans-serif")

    # Eğer logo varsa sol üste logoyu koy, yoksa küçük zarif bir marka rozeti koy
    if logo_b64:
        top_left_element = f"<img src='{logo_b64}' class='brand-logo' />"
    elif brand_name:
        top_left_element = f"<div class='brand-badge'>{brand_name}</div>"
    else:
        top_left_element = ""

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
                justify-content: flex-end;
            }}
            
            /* Logo için Sol Üst Köşe Sabitlemesi */
            .brand-logo {{
                position: absolute;
                top: 40px;
                left: 40px;
                max-height: 60px;
                max-width: 250px;
                object-fit: contain;
                z-index: 10;
                filter: drop-shadow(0 4px 6px rgba(0,0,0,0.4));
            }}

            /* Eğer logo yoksa çıkacak zarif rozet */
            .brand-badge {{
                position: absolute;
                top: 40px;
                left: 40px;
                display: inline-block;
                background-color: {primary_color};
                color: #ffffff;
                padding: 10px 20px;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 800;
                letter-spacing: 2px;
                text-transform: uppercase;
                z-index: 10;
                box-shadow: 0 4px 10px rgba(0,0,0,0.3);
            }}
            
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
        {top_left_element}
        <div class="overlay"></div>
        <div class="content-wrapper">
            <h1 class="headline">{text_on_image}</h1>
        </div>
    </body>
    </html>
    """
    return html