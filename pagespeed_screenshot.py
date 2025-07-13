import asyncio
from playwright.async_api import async_playwright


desk_url=''
async def capture_all_screenshots(url: str, output_prefix: str) -> list:
    from pathlib import Path
    screenshots = []
    outdir = Path("outputs")
    outdir.mkdir(exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for i in [1, 2]:  # 1 = mobile, 2 = desktop
            d = {
                'performance': f'[aria-labelledby="{"desktop_tab" if i==2 else "mobile_tab"}"] div.lh-category.lh--hoisted-meta#performance',
                'accessibility': f'[aria-labelledby="{"desktop_tab" if i==2 else "mobile_tab"}"] div.lh-category#accessibility',
                'bestprac': f'[aria-labelledby="{"desktop_tab" if i==2 else "mobile_tab"}"] div.lh-category#best-practices',
                'seo': f'[aria-labelledby="{"desktop_tab" if i==2 else "mobile_tab"}"] div.lh-category#seo',
            }

            png_suffix = "Desk" if i == 2 else "Mobile"
            pgs_url = f"https://pagespeed.web.dev/analysis?url={url}"
            await page.goto(pgs_url, timeout=60000)
            await page.wait_for_load_state('networkidle')

            # Fix: replace form_factor in resolved URL
            if "form_factor=mobile" in page.url:
                resolved_url = page.url.replace("form_factor=mobile", "form_factor=desktop") if i == 2 else page.url
                await page.goto(resolved_url, timeout=60000)

            await page.evaluate('document.body.style.transform = "scale(0.5)"')
            await page.evaluate('document.body.style.transformOrigin = "0 0"')

            for category, selector in d.items():
                try:
                    await page.wait_for_selector(selector, timeout=30000)
                    div = await page.query_selector(selector)
                    if div:
                        await div.scroll_into_view_if_needed()
                        file_path = outdir / f"{category}-{output_prefix}-{png_suffix}.png"
                        await div.screenshot(path=str(file_path))
                        screenshots.append(str(file_path))
                except Exception as e:
                    print(f"Error capturing {category}: {str(e)}")

        await browser.close()
    return screenshots

# Main entry point
if __name__ == "__main__":
    url='https://turquoisemoose.com'
    pgs_url = f'https://pagespeed.web.dev/analysis?url={url}'
    for i in range(1,3):
        asyncio.run(capture_div(pgs_url,'TurqMoose',i))

