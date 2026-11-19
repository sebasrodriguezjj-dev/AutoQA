"""Render existing acceptance records for visual QA; never rerun external tests."""

import re
from pathlib import Path

from playwright.sync_api import sync_playwright

from autoqa.core import Project
from autoqa.reporting import report


def main():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": 1440, "height": 1000})
            for name in ("independent-v02", "toolshop-v02"):
                project = Project(Path("projects") / name)
                report(project, "json")
                html_path = Path(report(project, "html"))
                for snapshot in (project.root / "artifacts").glob("*/qa-report.html"):
                    text = snapshot.read_text(encoding="utf-8")
                    snapshot.write_text(
                        re.sub(r'href="\.\./(?!\.\./)', 'href="../../', text), encoding="utf-8"
                    )
                page.goto(html_path.as_uri(), wait_until="load")
                preview = project.root / "artifacts/report-preview-v02.png"
                page.screenshot(path=str(preview), full_page=True)
                print(f"Rendered {name}: {html_path}; preview {preview}")
        finally:
            browser.close()


if __name__ == "__main__":
    main()
