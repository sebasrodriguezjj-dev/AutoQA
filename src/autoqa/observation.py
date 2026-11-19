"""Passive semantic observations with browser-checked locator candidates."""

import hashlib
from datetime import UTC, datetime

from autoqa.core import Element, LocatorCandidate

SEMANTICS = """() => {
 const name=e=>(e.getAttribute('aria-label') || (e.getAttribute('aria-labelledby')||'').split(' ').map(id=>document.getElementById(id)?.textContent||'').join(' ').trim() || (e.labels && [...e.labels].map(l=>l.innerText).join(' ')) || e.innerText || e.getAttribute('placeholder') || '').trim().slice(0,200);
 const visible=e=>!!e.getClientRects().length && getComputedStyle(e).visibility!=='hidden';
 const roles={A:'link',BUTTON:'button',SELECT:'combobox',TEXTAREA:'textbox',NAV:'navigation',FORM:'form',ARTICLE:'article',LI:'listitem',H1:'heading',H2:'heading',H3:'heading'};
 const nodes=[...document.querySelectorAll('a[href],button,input:not([type=hidden]),select,textarea,nav,form,article,li,h1,h2,h3,[role],[data-testid]')].slice(0,350);
 return nodes.map(e=>{
 const attrs={}; for(const key of ['id','name','placeholder','aria-label','data-testid','min','max','minlength','maxlength','pattern','type','aria-live','aria-busy']) {if(e.hasAttribute(key))attrs[key]=e.getAttribute(key).slice(0,200);}
 attrs.visible=String(visible(e));
 const role=e.getAttribute('role') || (e.tagName==='INPUT'?({checkbox:'checkbox',radio:'radio',search:'searchbox',submit:'button',button:'button',number:'spinbutton'}[e.type] || 'textbox'):roles[e.tagName]||'');
 return {kind:e.tagName.toLowerCase(),name:name(e),href:e.tagName==='A'?e.href:null,input_type:e.getAttribute('type'),required:e.required||false,role,attributes:attrs,options:e.tagName==='SELECT'?[...e.options].map(o=>({value:o.value,label:o.textContent.trim()})).slice(0,100):[],form:e.form?.id || (e.form?'unnamed-form':null)};
 });
}"""


def observe_elements(page, url: str, screenshot: str) -> list[Element]:
    data = page.evaluate(SEMANTICS)
    elements = []
    stamp = datetime.now(UTC).isoformat()
    for index, item in enumerate(data):
        element = Element.model_validate(item)
        element.id = (
            "EL-"
            + hashlib.sha256(f"{url}|{index}|{element.kind}|{element.name}".encode()).hexdigest()[
                :12
            ]
        )
        element.discovered_at = stamp
        element.evidence = [screenshot]
        name = element.name.lower()
        if element.input_type == "search" or (element.kind == "input" and "search" in name):
            element.components.append("search-field")
        if element.kind == "button" and "search" in name:
            element.components.append("search-button")
        if element.kind == "form":
            element.components.append("form")
        if element.required:
            element.components.append("required-field")
        if element.role in {"navigation", "checkbox", "radio", "combobox"}:
            element.components.append(element.role)
        if element.role == "article":
            element.components.append("content-card")
        if any(
            word in name for word in ("no results", "no supplies", "nothing found", "no products")
        ):
            element.components.append("empty-state-candidate")
        if element.role == "alert":
            element.components.append("error-or-validation-message")
        if element.role == "progressbar" or element.attributes.get("aria-busy") == "true":
            element.components.append("loading-indicator")
        if element.attributes.get("aria-live") or element.role == "status":
            element.components.append("dynamic-content")
        if element.role == "navigation" and any(word in name for word in ("page", "pagination")):
            element.components.append("pagination")
        candidates = []
        if element.name and element.role:
            candidates.append(
                (
                    "role",
                    element.role,
                    element.name,
                    page.get_by_role(element.role, name=element.name, exact=True),
                )
            )
        if element.kind in {"input", "select", "textarea"} and element.name:
            candidates.append(
                ("label", element.name, "", page.get_by_label(element.name, exact=True))
            )
        if element.attributes.get("placeholder"):
            value = element.attributes["placeholder"]
            candidates.append(
                ("placeholder", value, "", page.get_by_placeholder(value, exact=True))
            )
        if element.attributes.get("data-testid"):
            value = element.attributes["data-testid"]
            candidates.append(("test_id", value, "", page.get_by_test_id(value)))
        if element.role:
            candidates.append(("role", element.role, "", page.get_by_role(element.role)))
        for strategy, value, name, locator in candidates:
            count = locator.count()
            if count:
                element.locators.append(
                    LocatorCandidate(strategy=strategy, value=value, name=name, count=count)
                )
        elements.append(element)
    return elements


def functional_kinds(elements: list[Element]) -> dict[str, list[Element]]:
    groups: dict[str, list[Element]] = {}
    for element in elements:
        name = element.name.lower()
        kind = None
        if element.input_type == "search" or (element.kind == "input" and "search" in name):
            kind = "search"
        elif element.kind == "form" or element.required:
            kind = "form"
        elif element.kind == "select" and any(w in name for w in ("sort", "order")):
            kind = "sorting"
        elif element.role in {"checkbox", "radio", "combobox"} and any(
            w in name for w in ("category", "filter", "brand")
        ):
            kind = "filter"
        elif element.role == "article":
            kind = "product"
        if kind:
            groups.setdefault(kind, []).append(element)
    return groups
