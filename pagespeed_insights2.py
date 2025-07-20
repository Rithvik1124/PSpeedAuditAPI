import asyncio
import openai
import os
from playwright.async_api import async_playwright

async def extract_performance_data(page, mode):
    selectors = [
        # Performance
        ('perf_mob', f'{mode} .lh-exp-gauge__percentage'),
        ('lcp', f'{mode} .lh-metric#largest-contentful-paint'),
        ('cls', f'{mode} .lh-metric#cumulative-layout-shift'),
        ('si', f'{mode} .lh-metric#speed-index'),
        ('tbt', f'{mode} .lh-metric#total-blocking-time'),
        ('fcp', f'{mode} .lh-metric#first-contentful-paint'),
        ('perf_insights', f'{mode} .lh-audit-group--insights'),
        ('diag', f'{mode} .lh-audit-group--diagnostics'),
        ('perf_passed', f'{mode} .lh-category#performance .lh-clump--passed'),

        # Accessibility
        ('access_score', f'{mode} .lh-category#accessibility .lh-clump--passed'),
        ('namesNlabel', f'{mode} .lh-audit-group--a11y-names-labels'),
        ('best_prac', f'{mode} .lh-audit-group--a11y-best-practices'),
        ('color_cont', f'{mode} .lh-audit-group--a11y-color-contrast'),
        ('aria', f'{mode} .lh-audit-group--a11y-aria'),
        ('navigation', f'{mode} .lh-audit-group--a11y-navigation'),
        ('access_passed', f'{mode} .lh-category#accessibility .lh-clump--passed'),

        # Best Practices
        ('bp_score', f'{mode} .lh-category#best-practices .lh-gauge__percentage'),
        ('bp_gen', f'{mode} .lh-audit-group--best-practices-general'),
        ('bp_ux', f'{mode} .lh-audit-group--best-practices-ux'),
        ('bp_ts', f'{mode} .lh-audit-group--best-practices-trust-safety'),
        ('bp_passed', f'{mode} .lh-category#best-practices .lh-clump--passed'),

        # SEO
        ('seo_score', f'{mode} .lh-category#seo .lh-gauge__percentage'),
        ('seo_crawl', f'{mode} .lh-audit-group--seo-crawl'),
        ('seo_bp', f'{mode} .lh-audit-group--seo-content'),
        ('seo_passed', f'{mode} .lh-category#seo .lh-clump--passed'),
    ]

    performance_data = {}
    for name, selector in selectors:
        try:
            await page.wait_for_selector(selector, state='visible', timeout=60000)
            div = await page.query_selector(selector)
            if div:
                await div.scroll_into_view_if_needed(timeout=60000)
                if await div.is_visible():
                    text = await div.text_content()
                    performance_data[name] = text.strip() if text else "No content"
                else:
                    performance_data[name] = "Error: Element is not visible"
            else:
                performance_data[name] = "Error: Element not found"
        except Exception as e:
            performance_data[name] = f"Error: {str(e)}"
            print(f"Error extracting {name} with selector {selector}: {str(e)}")

    return performance_data

def build_prompt(device_type, data, url):
    def safe(k):
        return data.get(k, "N/A") if not str(data.get(k, "")).startswith("Error") else "N/A"

    return f"""
Act like an expert web performance consultant. I am running a Shopify website and I'm a beginner developer.

Below is a {device_type} Lighthouse report for my site: {url}

Please give me a step-by-step improvement plan, divided into:
1. Performance
2. Accessibility
3. Best Practices
4. SEO

Explain:
- What each issue means
- Why it matters
- How exactly to fix it (show code examples, settings, etc.)

---

**Performance Report:**
- Score: {safe('perf_mob')}
- LCP: {safe('lcp')}
- CLS: {safe('cls')}
- FCP: {safe('fcp')}
- Speed Index: {safe('si')}
- Total Blocking Time: {safe('tbt')}
- Diagnostics: {safe('diag')}
- Insights: {safe('perf_insights')}
- Passed Audits: {safe('perf_passed')}

---

**Accessibility Report:**
- Score: {safe('access_score')}
- Color Contrast: {safe('color_cont')}
- ARIA: {safe('aria')}
- Navigation: {safe('navigation')}
- Labels & Forms: {safe('namesNlabel')}
- Best Practices: {safe('best_prac')}
- Passed Audits: {safe('access_passed')}

---

**Best Practices Report:**
- Score: {safe('bp_score')}
- General: {safe('bp_gen')}
- UX: {safe('bp_ux')}
- Trust & Safety: {safe('bp_ts')}
- Passed Audits: {safe('bp_passed')}

---

**SEO Report:**
- Score: {safe('seo_score')}
- Crawl Issues: {safe('seo_crawl')}
- Content Issues: {safe('seo_bp')}
- Passed Audits: {safe('seo_passed')}
"""

async def main(url):
    combined_performance_data = {'mobile': {}, 'desktop': {}}
    url_mob = f'https://pagespeed.web.dev/analysis?url={url}'

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Mobile mode
        print(f"Scraping Mobile: {url_mob}")
        await page.goto(url_mob, timeout=90000)
        await page.wait_for_load_state('networkidle')
        mobile_data = await extract_performance_data(page, '[aria-labelledby="mobile_tab"]')
        combined_performance_data['mobile'] = mobile_data

        # Desktop mode
        url_desk = url_mob.replace('=mobile', '=desktop')
        print(f"Scraping Desktop: {url_desk}")
        await page.goto(url_desk, timeout=90000)
        await page.wait_for_load_state('networkidle')
        desktop_data = await extract_performance_data(page, '[aria-labelledby="desktop_tab"]')
        combined_performance_data['desktop'] = desktop_data

        await browser.close()

    # Set API Key
    openai.api_key = os.getenv("OPENAI_API_KEY")

    # Generate Prompts
    mobile_prompt = build_prompt("mobile", mobile_data, url)
    desktop_prompt = build_prompt("desktop", desktop_data, url)

    # Get GPT Advice (Mobile)
    response_mobile = await asyncio.to_thread(
        openai.ChatCompletion.create,
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful web performance optimization expert."},
            {"role": "user", "content": mobile_prompt}
        ],
        max_tokens=5000
    )

    # Get GPT Advice (Desktop)
    response_desktop = await asyncio.to_thread(
        openai.ChatCompletion.create,
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful web performance optimization expert."},
            {"role": "user", "content": desktop_prompt}
        ],
        max_tokens=5000
    )

    # Print & Return Results
    advice_mobile = response_mobile.choices[0].message.content
    advice_desktop = response_desktop.choices[0].message.content

    print("\n--- Mobile Optimization Advice ---\n")
    print(advice_mobile)
    print("\n--- Desktop Optimization Advice ---\n")
    print(advice_desktop)

    return {
        "mobile_advice": advice_mobile,
        "desktop_advice": advice_desktop,
        "combined_data": combined_performance_data
    }
