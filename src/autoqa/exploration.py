"""Single-browser bounded discovery and evidence-grounded workflow extraction."""

import time
from collections import deque
from urllib.parse import urljoin

from playwright.sync_api import Error, sync_playwright

from autoqa.core import Discovery, EvidenceReference, PageEvidence, Project, Workflow, save_json
from autoqa.observation import functional_kinds, observe_elements
from autoqa.readiness import observe_readiness
from autoqa.security import Scope, canonical

EXTRACT = """() => {
 const visible = e => !!(e.getClientRects().length) && getComputedStyle(e).visibility !== 'hidden';
 const name = e => (e.getAttribute('aria-label') || (e.labels && [...e.labels].map(l=>l.innerText).join(' ')) || e.innerText || e.getAttribute('placeholder') || e.getAttribute('name') || '').trim().slice(0,200);
 return {
 headings: [...document.querySelectorAll('h1,h2,h3,[role=heading]')].filter(visible).slice(0,50).map(e=>e.innerText.trim().slice(0,200)),
 elements: [...document.querySelectorAll('a[href],button,input:not([type=hidden]),select,textarea,[role=button],[role=search],[role=navigation]')].filter(visible).slice(0,200).map(e=>({kind:e.tagName.toLowerCase(),name:name(e),href:e.tagName==='A'?e.href:null,input_type:e.getAttribute('type'),required:e.required || false}))
 };
}"""


def extract_workflows(discovery: Discovery) -> list[Workflow]:
    workflows = []
    for page in discovery.pages:
        workflows.append(
            Workflow(
                id=f"WF-{len(workflows) + 1:03}",
                name=f"View {page.headings[0] if page.headings else page.title}",
                page_url=page.url,
                elements=page.headings,
                evidence=[page.screenshot],
                steps=[f"Open {page.url}", "Inspect visible page content"],
                status="OBSERVED",
            )
        )
        fields = [e.name for e in page.elements if e.kind in {"input", "select", "textarea"}]
        if fields:
            workflows.append(
                Workflow(
                    id=f"WF-{len(workflows) + 1:03}",
                    name="Potential form or search workflow",
                    page_url=page.url,
                    elements=fields,
                    evidence=[page.screenshot],
                    steps=["Review intended form behavior before interacting"],
                    status="INFERRED",
                )
            )
        for kind, controls in functional_kinds(page.elements).items():
            workflows.append(
                Workflow(
                    id=f"WF-{len(workflows) + 1:03}",
                    name=f"Potential {kind} workflow",
                    page_url=page.url,
                    elements=[e.name for e in controls],
                    evidence=[page.screenshot],
                    steps=[
                        f"Review {kind} interaction data and observable outcome",
                        "Approve a behavior contract before interaction",
                    ],
                    status="INFERRED",
                    kind=kind,
                    element_ids=[e.id for e in controls],
                    risk="Medium" if kind == "form" else "Low",
                )
            )
    return workflows


def explore(project: Project, url: str) -> Discovery:
    config = project.config
    scope = Scope(url, config)
    discovery = Discovery()
    queue = deque([(scope.base, 0)])
    visited: set[str] = set()
    started = time.monotonic()
    stamp = str(time.time_ns())
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=config.headless, args=scope.chromium_args)
        try:
            context = browser.new_context(service_workers="block", accept_downloads=False)
            context.route("**/*", scope.guard)
            context.route_web_socket("**/*", lambda socket: socket.close())
            page = context.new_page()
            page.on("dialog", lambda dialog: dialog.dismiss())
            context.on("page", lambda popup: popup.close() if popup != page else None)
            while queue and len(visited) < config.max_pages:
                remaining = config.overall_timeout_seconds - (time.monotonic() - started)
                if remaining <= 0:
                    discovery.errors.append(
                        "Overall exploration timeout reached; discovery is partial."
                    )
                    break
                target, depth = queue.popleft()
                if target in visited or not scope.allows(target):
                    continue
                visited.add(target)
                try:
                    timeout = min(config.navigation_timeout_ms, int(remaining * 1000))
                    page.set_default_timeout(max(1, timeout))
                    response = page.goto(
                        target, wait_until="domcontentloaded", timeout=max(1, timeout)
                    )
                    if not response or response.status >= 400:
                        discovery.errors.append(f"HTTP navigation failure at {target}")
                        continue
                    scope.validate(page.url)
                    readiness_budget = min(
                        config.spa_readiness_timeout_ms,
                        max(
                            1,
                            int(
                                (config.overall_timeout_seconds - (time.monotonic() - started))
                                * 1000
                            ),
                        ),
                    )
                    readiness = observe_readiness(
                        page, readiness_budget, config.spa_quiet_window_ms
                    )
                    if readiness["status"] == "TIMEOUT":
                        discovery.errors.append(
                            f"SPA readiness timeout at {target}; UI observations may be incomplete."
                        )
                    data = page.evaluate(EXTRACT)
                    screenshot = f"screenshots/{stamp}-page-{len(discovery.pages) + 1:03}.png"
                    page.screenshot(path=str(project.root / screenshot), timeout=max(1, timeout))
                    evidence = PageEvidence(
                        url=canonical(page.url),
                        title=page.title()[:200],
                        headings=data["headings"],
                        elements=observe_elements(page, canonical(page.url), screenshot),
                        screenshot=screenshot,
                        depth=depth,
                        readiness=readiness,
                        dynamic_signals=[
                            e
                            for e in page.locator(
                                '[aria-live], [aria-busy], [role="status"], [role="alert"]'
                            ).all_text_contents()
                        ][:30],
                    )
                    discovery.pages.append(evidence)
                    discovery.evidence_records.append(
                        EvidenceReference(
                            id=f"EV-PAGE-{len(discovery.pages):03}",
                            category="OBSERVED",
                            description=f"Passive semantic observation of {evidence.url}",
                            page_url=evidence.url,
                            artifact=screenshot,
                        )
                    )
                    for element in evidence.elements:
                        discovery.evidence_records.append(
                            EvidenceReference(
                                id=element.id,
                                category="OBSERVED",
                                description=f"{element.kind} {element.name}; checked locator counts; no interaction performed",
                                page_url=evidence.url,
                                artifact=screenshot,
                            )
                        )
                    for element in evidence.elements:
                        if element.kind == "a" and element.href:
                            destination = canonical(urljoin(evidence.url, element.href))
                            if scope.allows(destination):
                                edge = (evidence.url, destination)
                                if edge not in discovery.edges:
                                    discovery.edges.append(edge)
                                if depth < config.max_depth and destination not in visited:
                                    # Queue growth bounded independently of visited page count.
                                    if len(queue) < config.max_pages * 20:
                                        queue.append((destination, depth + 1))
                except (Error, ValueError) as error:
                    discovery.errors.append(
                        f"Navigation/inspection failed at {target}: {type(error).__name__}"
                    )
        finally:
            discovery.blocked_requests = scope.blocked_requests
            browser.close()
    discovery.workflows = extract_workflows(discovery)
    save_json(project.root / "discovery/workflow-map.json", discovery.model_dump())
    lines = ["# Discovery", "", "Observed pages:"] + [
        f"- {p.url}: {', '.join(p.headings)}" for p in discovery.pages
    ]
    lines += ["", "Workflows:"] + [f"- {w.id} [{w.status}] {w.name}" for w in discovery.workflows]
    lines += [
        "",
        "Limitations: link-only discovery; no form submissions; inferred workflows need review.",
    ]
    lines += discovery.errors
    (project.root / "discovery/summary.md").write_text("\n".join(lines), encoding="utf-8")
    config.application_url = scope.base
    config.allowed_domains = [scope.origin[1]]
    project.save_config()
    project.audit(f"Explored {len(discovery.pages)} pages; {len(discovery.errors)} errors")
    return discovery
