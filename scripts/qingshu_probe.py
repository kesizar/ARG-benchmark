import asyncio,json
from pathlib import Path
from playwright.async_api import async_playwright
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch(channel="msedge",headless=True);page=await b.new_page()
  await page.goto("https://mc-zian.github.io/argqingshu/");await page.wait_for_timeout(1000)
  d={"url":page.url,"body_text":await page.locator("body").inner_text(),"body_children":await page.locator("body > *").count(),"scripts":await page.locator("script").count()}
  await page.screenshot(path="judge/qingshu-shizong/forum-blank.png");Path("judge/qingshu-shizong/forum-ui.json").write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding="utf-8");print(d);await b.close()
asyncio.run(main())
