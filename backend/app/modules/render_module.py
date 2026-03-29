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

def generate_brand_html(image_url: str, text_on_image: str, brand_context: dict, logo_b64: str = "", element_b64: str = "", layout_type: str = "split") -> str:
    brand_name = brand_context.get("name", brand_context.get("brand_details", {}).get("name", ""))
    visuals = brand_context.get("visual_identity", {})
    
    corporate_colors = visuals.get("corporate_colors", ["#005f56", "#2d3748"])
    primary_color = corporate_colors[0] if len(corporate_colors) > 0 else "#005f56"
    secondary_color = corporate_colors[1] if len(corporate_colors) > 1 else "#2d3748"
    
    bg_colors = visuals.get("background_colors", ["#ffffff"])
    bg_color = bg_colors[0] if len(bg_colors) > 0 else "#ffffff"
    
    font_family = visuals.get("typography", {}).get("primary", "sans-serif")

    words = text_on_image.split()
    if len(words) > 3:
        hook_text = " ".join(words[:2])
        main_text = " ".join(words[2:])
    else:
        hook_text = brand_name
        main_text = text_on_image

    # --- ŞABLON 1: SPLIT ROUNDED (Dinamik Yükseklik ve Köşe Filigranı) ---
    if layout_type == "split" or layout_type == "split-rounded":
        html_body = f"""
        <div style="background-color: {secondary_color}; width: 1080px; height: 1080px; display: flex; flex-direction: column;">
            
            <div style="padding: 60px 60px 40px 60px; position: relative; overflow: hidden; z-index: 2;">
                {f'<img src="{element_b64}" style="position: absolute; top: -50px; right: -50px; width: 300px; opacity: 0.15; z-index: 1; pointer-events: none; transform: rotate(15deg);" />' if element_b64 else ''}
                
                <div style="position: relative; z-index: 2; display: flex; flex-direction: column; gap: 15px;">
                    <div style="align-self: flex-start; background-color: {primary_color}; color: white; padding: 10px 25px; border-radius: 50px; font-size: 32px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;">
                        {hook_text}
                    </div>
                    <h1 style="color: #ffffff; font-size: 64px; font-weight: 900; line-height: 1.1; margin: 0; letter-spacing: -1px;">
                        {main_text}
                    </h1>
                </div>
            </div>

            <div style="flex: 1; background-image: url('{image_url}'); background-size: cover; background-position: center; border-radius: 60px 60px 0 0; border: 8px solid {secondary_color}; border-bottom: none; z-index: 3; position: relative; box-shadow: 0 -10px 30px rgba(0,0,0,0.2);">
                {f'<img src="{logo_b64}" style="position: absolute; bottom: 40px; left: 40px; max-height: 50px; z-index: 10; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.4));" />' if logo_b64 else ''}
            </div>
        </div>
        """

    # --- Diğer Şablonlar (Aynı mantıkla optimize edildi) ---
    elif layout_type == "card" or layout_type == "framed-pill":
        html_body = f"""
        <div style="background-color: {bg_color}; width: 1080px; height: 1080px; position: relative; overflow: hidden; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 60px 0;">
            {f'<img src="{element_b64}" style="position: absolute; bottom: -100px; right: -100px; width: 450px; opacity: 0.1; z-index: 1;" />' if element_b64 else ''}
            {f'<img src="{logo_b64}" style="position: absolute; bottom: 50px; left: 50px; max-height: 50px; z-index: 10;" />' if logo_b64 else ''}
            <div style="text-align: center; z-index: 2; width: 85%; margin-bottom: 40px;">
                <h1 style="color: {primary_color}; font-size: 64px; font-weight: 900; line-height: 1.1; margin: 0 0 20px 0; letter-spacing: -1px;">{main_text}</h1>
                <div style="display: inline-block; background-color: {primary_color}; color: white; padding: 12px 40px; border-radius: 50px; font-size: 36px; font-weight: 800;">{hook_text}</div>
            </div>
            <div style="width: 85%; flex: 1; background-image: url('{image_url}'); background-size: cover; background-position: center; border-radius: 40px; z-index: 2; box-shadow: 0 20px 40px rgba(0,0,0,0.15);"></div>
        </div>
        """
    else:
        html_body = f"""
        <div style="background-image: url('{image_url}'); background-size: cover; background-position: center; width: 1080px; height: 1080px; position: relative; display: flex; flex-direction: column; justify-content: flex-end;">
            {f'<img src="{logo_b64}" style="position: absolute; top: 50px; left: 50px; max-height: 55px; z-index: 10; filter: drop-shadow(0 4px 8px rgba(0,0,0,0.4));" />' if logo_b64 else ''}
            {f'<img src="{element_b64}" style="position: absolute; bottom: -80px; right: -80px; width: 450px; opacity: 0.15; z-index: 1;" />' if element_b64 else ''}
            <div style="position: absolute; bottom: 0; left: 0; width: 100%; height: 60%; background: linear-gradient(to top, rgba(0,0,0,0.9) 0%, rgba(0,0,0,0) 100%); z-index: 1;"></div>
            <div style="position: relative; z-index: 2; padding: 80px; color: white;">
                <div style="display: inline-block; background-color: {primary_color}; color: white; padding: 10px 20px; border-radius: 8px; font-size: 24px; font-weight: 800; margin-bottom: 20px;">{hook_text}</div>
                <h1 style="font-size: 68px; font-weight: 900; line-height: 1.15; margin: 0; text-shadow: 0 4px 16px rgba(0,0,0,0.6);">{main_text}</h1>
            </div>
        </div>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@500;800;900&display=swap');
            body {{ margin: 0; padding: 0; font-family: 'Montserrat', {font_family}, sans-serif; -webkit-font-smoothing: antialiased; background-color: #fff; }}
        </style>
    </head>
    <body>
        {html_body}
    </body>
    </html>
    """