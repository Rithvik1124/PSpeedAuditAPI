import asyncio
import openai
import os 
from playwright.async_api import async_playwright
from dotenv import load_dotenv, dotenv_values 



async def extract_performance_data(page,mode):
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
            # Ensure the element is visible and scrolled into view
            await page.wait_for_selector(selector, state='visible', timeout=60000)  # Increase timeout
            div = await page.query_selector(selector)
            if div:
                # Explicitly scroll into view and check visibility
                await div.scroll_into_view_if_needed(timeout=60000)
                if await div.is_visible():
                    performance_data[name] = await div.text_content()
                else:
                    performance_data[name] = "Error: Element is not visible"
            else:
                performance_data[name] = "Error: Element not found"
        except Exception as e:
            performance_data[name] = f"Error: {str(e)}"
            print(f"Error extracting {name} with selector {selector}: {str(e)}")

    return performance_data

async def main(url):
    combined_performance_data = {'mobile': {}, 'desktop': {}}
    url_mob = f'https://pagespeed.web.dev/analysis?url={url}'    

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        #MOBILE MODE        
        print(f"Scraping Current URL: {url_mob}")
        await page.goto(url_mob, timeout=90000)  
        await page.wait_for_load_state('networkidle')
        url_mob=page.url
        performance_data = await extract_performance_data(page,'[aria-labelledby="mobile_tab"]')
        combined_performance_data['mobile'] = performance_data
        
        #DESKTOP MODE
        
        url_desk=url_mob.replace('=mobile','=desktop')
        print(f"Scraping Current URL: {url_desk}")
        await page.goto(url_desk, timeout=90000)  
        await page.wait_for_load_state('networkidle')
        performance_data = await extract_performance_data(page,'[aria-labelledby="desktop_tab"]')
        combined_performance_data['desktop'] = performance_data

        # Generate the combined report using extracted data for both mobile and desktop
        performance_report = f'''Prompt for Advice on Optimizing My Webpage:
                                *"Act like an expert web performance consultant. I am running a Shopify website and I am a novice developer
                                who is not experienced with SEO or performance optimization.
                                I will paste the output from a Lighthouse / PageSpeed Insights / Playwright report.
                                Go through the results and give me a structured improvement plan:
                                Break it down by category: Performance, Accessibility, Best Practices, SEO.
                                Explain what the issue is in plain English.
                                Tell me why it matters and exactly how to fix it.
                                Include examples of the code changes, server headers, or settings to adjust.

                                Don't assume I know SEO or Core Web Vitals—spell out every step."*
                                 Page URL: {url}
                                 
                                ---
                                
                                1. **Performance Report:**
                                - **Performance Score (Mobile):** {performance_data['perf_mob']}  
                                - **Core Web Vitals:**  
                                  - **Largest Contentful Paint (LCP):** {performance_data['lcp']}
                                  - **Cumulative Layout Shift (CLS):** {performance_data['cls']}
                                - **Speed Index:** {performance_data['si']}
                                - **Total Blocking Time (TBT):** {performance_data['tbt']}  
                                - **First Contentful Paint (FCP):** {performance_data['fcp']}  
                                - **Diagnostics:** {performance_data['diag']}  
                                - **Performance Insights:** {performance_data['perf_insights']}  
                                - **Performance Passed:** {performance_data['perf_passed']}  
                                
                                ---
                                
                                2. **Accessibility Report:**
                                - **Accessibility Score:** {performance_data['access_score']}  
                                - **Color Contrast Issues:** {performance_data['color_cont']}
                                - **ARIA Issues:** {performance_data['aria']}
                                - **Navigation Issues:**  
                                  *(List any issues related to focus management, keyboard navigation, etc.)*  
                                - **Semantic HTML Issues:**  
                                  *(Are headings, lists, buttons used correctly?)*  
                                - **Accessible Forms Issues:**  
                                  *(Missing form labels or other issues with form elements)*  
                                - **Other Accessibility Issues:**  
                                  *(Any other problems like missing language attributes, screen reader issues, etc.)*  
                                - **Accessibility Passed:** {performance_data['access_passed']}  
                                
                                ---
                                
                                3. **Best Practices Report:**
                                - **Best Practices Score:** {performance_data['bp_score']} 
                                - **General Best Practices:** {performance_data['bp_gen']}
                                - **UX Best Practices:** {performance_data['bp_ux']}
                                - **Trust & Safety Best Practices:** {performance_data['bp_ts']}
                                - **Best Practices Passed:** {performance_data['bp_passed']}  
                                
                                ---
                                
                                4. **SEO Report:**
                                - **SEO Score:** {performance_data['seo_score']}
                                - **SEO Crawl Issues:** {performance_data['seo_crawl']}  
                                - **SEO Content Best Practices:** {performance_data['seo_bp']}  
                                - **SEO Passed:** {performance_data['seo_passed']}
                                
                                ---
                                
                                **Go through the above data and give me specific advice on how to improve each area (performance, accessibility, best practices, SEO)
                                and actionable steps for optimizing your webpage. Assume any unpecified/errors as not applicable**
                                '''

        # OpenAI API call for advice (on the combined data)
        load_dotenv()
        client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "You are a helpful and highly - detailed web performance optimization expert."},
                      {"role": "user", "content": performance_report}]
        )
        print(f"Optimization Advice:\n", response.choices[0].message.content)

        
        advice=response.choices[0].message.content
        await browser.close()
        return advice, combined_performance_data


