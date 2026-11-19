"""Bounded UI-state evidence, without fixed sleeps or network-idle assumptions."""

import time
from datetime import UTC, datetime

from playwright.sync_api import TimeoutError as PlaywrightTimeout

INIT = """() => {
 const prior=window.__autoqaReadiness; if(prior?.observer)prior.observer.disconnect();
 const state={lastMutation:performance.now(),mutations:0};
 state.observer=new MutationObserver(()=>{state.lastMutation=performance.now();state.mutations++;});
 state.observer.observe(document.documentElement,{subtree:true,childList:true,attributes:true,characterData:true});
 window.__autoqaReadiness=state;
}"""

STATE = """() => {
 const visible=e=>!!e.getClientRects().length&&getComputedStyle(e).visibility!=='hidden';
 const content=e=>visible(e)&&!e.closest('nav,header,footer');
 const count=selector=>[...document.querySelectorAll(selector)].filter(content).length;
 const status=[...document.querySelectorAll('[role=status],[role=alert],[aria-live]')].filter(content).filter(e=>e.textContent.trim());
 const busy=count('[aria-busy=true],[role=progressbar],progress');
 const headings=count('h1,h2,h3,h4,h5,h6,[role=heading]');
 const items=count('article,li,tbody tr,[role=listitem],[role=row]');
 const controls=count('input:not([type=hidden]),select,textarea,button');
 const tracker=window.__autoqaReadiness;
 return {document_state:document.readyState,busy,headings,items,controls,status_regions:status.length,mutations:tracker?.mutations||0,quiet_ms:Math.max(0,Math.round(performance.now()-(tracker?.lastMutation||performance.now())))};
}"""

PREDICATE = (
    """quietWindow => {
 const sample=("""
    + STATE
    + """)();
 if(sample.document_state==='loading'||sample.busy||sample.quiet_ms<quietWindow)return false;
 if(sample.headings||sample.items||sample.controls)return {...sample,status:'CONTENT_STABLE'};
 if(sample.status_regions)return {...sample,status:'STATUS_STABLE'};
 return false;
}"""
)


def observe_readiness(page, timeout_ms: int, quiet_window_ms: int) -> dict:
    started = time.monotonic()
    page.evaluate(INIT)
    try:
        handle = page.wait_for_function(
            PREDICATE, arg=quiet_window_ms, polling="raf", timeout=timeout_ms
        )
        try:
            result = handle.json_value()
        finally:
            handle.dispose()
    except PlaywrightTimeout:
        result = {**page.evaluate(STATE), "status": "TIMEOUT"}
    finally:
        page.evaluate("() => {window.__autoqaReadiness?.observer?.disconnect();}")
    return {
        **result,
        "observed_at": datetime.now(UTC).isoformat(),
        "elapsed_ms": round((time.monotonic() - started) * 1000),
        "timeout_ms": timeout_ms,
        "quiet_window_ms": quiet_window_ms,
        "application_completeness": "UNVERIFIED",
    }
