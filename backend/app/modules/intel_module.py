from duckduckgo_search import DDGS

def get_competitor_intel(competitors: list) -> str:
    """
    Verilen rakiplerin son 1 aydaki dijital ayak izlerini (haber, blog, indexli sosyal medya)
    DuckDuckGo üzerinden ücretsiz tarar ve özetler.
    """
    if not competitors:
        return "Herhangi bir rakip belirtilmedi."

    intel_report = "--- RAKİP İSTİHBARAT RAPORU (SON 1 AY) ---\n"
    
    try:
        with DDGS() as ddgs:
            for comp in competitors:
                intel_report += f"\nHedef: {comp}\n"
                # Rakibin adıyla son 1 aydaki (timelimit='m') gelişmeleri arıyoruz
                query = f'"{comp}" software OR platform OR update OR news'
                results = ddgs.text(query, max_results=3, timelimit='m')
                
                if results:
                    for res in results:
                        title = res.get('title', '')
                        body = res.get('body', '')
                        intel_report += f"- {title}: {body}\n"
                else:
                    intel_report += "- Son 1 ayda majör bir dijital ayak izi bulunamadı.\n"
                    
    except Exception as e:
        print(f"Scraping Hatası: {e}")
        return "Rakiplerin güncel verisi çekilirken arama motoru limitine takıldı. Sektör geneli stratejiye odaklanın."

    return intel_report