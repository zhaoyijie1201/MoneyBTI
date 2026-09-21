# -*- coding: utf-8 -*-
"""UI 验收：用 Playwright 打开本地服务，跑演示账单走完四个面板，截图到 eval/results/screens/，收集控制台错误。
用法: python eval/ui_smoke.py [http://127.0.0.1:7860] [T06] [basic|vip] [--compare]
"""
import os, sys, time
from playwright.sync_api import sync_playwright

base = next((a for a in sys.argv[1:] if a.startswith("http")), "http://127.0.0.1:7860")
sample = next((a for a in sys.argv[1:] if a.startswith("T")), "T06")
tier = "vip" if "vip" in sys.argv[1:] else "basic"
compare = "--compare" in sys.argv
english = "--en" in sys.argv
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "screens")
SUF = "_en" if "--en" in sys.argv else ""
os.makedirs(OUT, exist_ok=True)
errors = []

with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page(viewport={"width": 1400, "height": 1000})
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(base, wait_until="networkidle")
    page.wait_for_function("document.querySelector('#sample-select').options.length > 0", timeout=15000)
    if english:
        page.click(".language-switch__btn[data-lang='en']"); time.sleep(0.3)
    page.click(f"[data-tier={tier}]")
    if compare:
        page.check("#chk-compare")
    page.select_option("#sample-select", sample)
    page.screenshot(path=os.path.join(OUT, f"{sample}_{tier}{SUF}_1_upload.png"), full_page=False)
    page.click("#btn-demo")
    page.wait_for_selector("#panel-classify:not([hidden])", timeout=300000)
    time.sleep(0.5)
    print("② rows:", page.eval_on_selector_all("#txn-body tr", "els => els.length"), "|", page.inner_text("#classify-stats")[:80])
    page.screenshot(path=os.path.join(OUT, f"{sample}_{tier}{SUF}_2_classify.png"), full_page=False)
    # 改一笔分类，验证 M4 覆盖
    page.select_option("#txn-body tr:first-child select", "C9")
    page.click("#btn-confirm")
    page.wait_for_selector("#panel-metrics:not([hidden])", timeout=60000)
    time.sleep(0.5)
    print("③", page.inner_text("#metrics-lead")[:90], "| cands:", page.eval_on_selector_all(".cand__name", "els => els.map(e => e.textContent)"))
    page.locator("#panel-metrics").screenshot(path=os.path.join(OUT, f"{sample}_{tier}{SUF}_3_metrics.png"))
    page.click("#btn-generate")
    page.wait_for_selector("#panel-result:not([hidden])", timeout=120000)
    time.sleep(0.8)
    print("ticket modal:", not page.evaluate("document.querySelector('#ticket-modal').hidden"), "|", page.inner_text("#receipt-modal .tk-match").replace("\n", " "))
    page.locator("#ticket-modal .modal__box").screenshot(path=os.path.join(OUT, f"{sample}_{tier}{SUF}_ticket_modal.png"))
    page.click("#ticket-modal .modal__close"); time.sleep(0.3)
    print("④", page.inner_text("#result-lead"), "|", page.inner_text(".persona__name"), "|", page.inner_text(".tk-match").replace("\n", " "))
    page.locator("#panel-result").screenshot(path=os.path.join(OUT, f"{sample}_{tier}{SUF}_4_result.png"))
    print("buttons re-enabled:", not page.is_disabled("#btn-generate"), not page.is_disabled("#btn-confirm"), "| body busy:", page.evaluate("document.body.classList.contains('is-busy')"))
    print("analysis card:", page.inner_text("#analysis-state-label"), "|", page.inner_text("#persona-name"), "|", page.inner_text("#persona-badge"), "| stats:", page.locator("#category-stats .stat").count(), "| home ticket:", page.locator("#receipt-hero").count())
    page.click("#panel-result [data-fold-toggle]"); time.sleep(0.3)
    print("panel-4 fold collapsed:", page.get_attribute("#panel-result .tk-fold", "data-collapsed"))
    page.click("#panel-result [data-fold-toggle]"); time.sleep(0.3)
    nb = page.locator("#receipt [data-badge]").count()
    print("ticket badges:", nb)
    if nb:
        page.locator("#receipt [data-badge]").first.click(); time.sleep(0.4)
        print("badge modal visible:", page.is_visible("#badge-modal"), "|", page.inner_text("#badge-body h3"))
        page.locator("#badge-modal .modal__box").screenshot(path=f"{OUT}/{sample}_{tier}{SUF}_badge_modal.png")
        page.click("#badge-modal [data-close]"); time.sleep(0.2)
    page.locator(".analysis").screenshot(path=os.path.join(OUT, f"{sample}_{tier}{SUF}_analysis_card.png"))
    page.click("[data-theme=night]")
    page.locator("#receipt").screenshot(path=os.path.join(OUT, f"{sample}_{tier}{SUF}_receipt_night.png"))
    page.click("#btn-debug")
    time.sleep(0.3)
    print("drawer calls:", page.eval_on_selector_all("#drawer-body details", "els => els.length"))
    page.screenshot(path=os.path.join(OUT, f"{sample}_{tier}{SUF}_5_drawer.png"), full_page=False)
    page.click("#drawer [data-close]")
    page.click("[data-nav=gallery]")
    time.sleep(0.3)
    print("gallery cards:", page.eval_on_selector_all("#gallery-grid .gcard", "els => els.length"))
    page.screenshot(path=os.path.join(OUT, f"{sample}_{tier}{SUF}_6_gallery.png"), full_page=False)
    if compare:
        page.click("#gallery [data-close]")
        print("compare cols:", page.eval_on_selector_all("#compare-grid .compare__col", "els => els.length"))
        page.locator("#compare-grid").screenshot(path=os.path.join(OUT, f"{sample}_compare.png"))
    b.close()
print("console errors:", errors or "none")
