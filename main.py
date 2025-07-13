from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
import uuid
import os
import shutil
import asyncio

from pagespeed_insights2 import main as run_scraper
from makedoc import generate_docx_from_advice
from pagespeed_screenshot import capture_all_screenshots

app = FastAPI()

OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.get("/analyze")
async def analyze(url: str = Query(..., description="Page URL to audit")):
    try:
        uid = str(uuid.uuid4())[:8]
        work_dir = os.path.join(OUTPUT_DIR, uid)
        os.makedirs(work_dir, exist_ok=True)

        # Step 1: Scrape PageSpeed + Get Advice
        advice, performance_data = await run_scraper(url)

        # Step 2: Generate .docx file
        docx_path = os.path.join(work_dir, f"{uid}_report.docx")
        generate_docx_from_advice(advice, url, docx_path)

        # Step 3: Take Screenshots
        screenshots = await capture_all_screenshots(url, uid)
        for path in screenshots:
            shutil.move(path, work_dir)

        # Step 4: Zip it
        zip_path = os.path.join(OUTPUT_DIR, f"{uid}_report.zip")
        shutil.make_archive(zip_path.replace('.zip', ''), 'zip', work_dir)

        return FileResponse(zip_path, media_type="application/zip", filename=f"{uid}_report.zip")

    except Exception as e:
        return {"error": str(e)}
