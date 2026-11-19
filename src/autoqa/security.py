"""Explicit URL scope, DNS checks, and conservative read-only navigation."""

import ipaddress
import re
import socket
import time
from urllib.parse import parse_qsl, unquote, urljoin, urlsplit, urlunsplit

from autoqa.core import Config

SENSITIVE = re.compile(
    r"(?:logout|log-out|signout|sign-out|delete|remove|purchase|checkout|cart|subscribe|unsubscribe|activate|deactivate|destroy|confirm|reset|token|password|session)",
    re.I,
)


def canonical(url: str) -> str:
    parsed = urlsplit(url)
    return urlunsplit(
        (parsed.scheme.lower(), parsed.netloc.lower(), parsed.path or "/", parsed.query, "")
    )


class Scope:
    def __init__(self, base: str, config: Config):
        if "\\" in base or any(ord(c) < 33 for c in base):
            raise ValueError("URL contains unsafe whitespace or backslashes.")
        self.config = config
        self.last_request_at = 0.0
        self.request_count = 0
        self._redirect_sessions = {}
        self.blocked_requests: list[dict[str, str]] = []
        self.base = canonical(base)
        self.origin = self._origin(self.base)
        self.validate(self.base)
        addresses = socket.getaddrinfo(self.origin[1], self.origin[2], type=socket.SOCK_STREAM)
        self.pinned_address = next(
            (a[4][0] for a in addresses if a[0] == socket.AF_INET), addresses[0][4][0]
        )
        address = ipaddress.ip_address(self.pinned_address)
        if not address.is_global and not (config.allow_localhost and address.is_loopback):
            raise ValueError("DNS changed to an unsafe address.")
        self.api_scopes = {}
        for rule in config.api_resources:
            if not rule.enabled:
                continue
            origin = self._origin(rule.origin)
            if origin not in self.api_scopes:
                if origin == self.origin:
                    self.api_scopes[origin] = self
                else:
                    child_config = config.model_copy(
                        update={"api_resources": [], "allowed_domains": [origin[1]]}
                    )
                    child = Scope(rule.origin + "/", child_config)
                    # One validated pin per hostname, including rules on different ports.
                    existing = next(
                        (s for s in [self, *self.api_scopes.values()] if s.origin[1] == origin[1]),
                        None,
                    )
                    if existing:
                        child.pinned_address = existing.pinned_address
                    self.api_scopes[origin] = child

    @property
    def chromium_args(self) -> list[str]:
        pins = {s.origin[1]: s.pinned_address for s in [self, *self.api_scopes.values()]}
        rules = [
            f"MAP {host} {'[' + address + ']' if ':' in address else address}"
            for host, address in pins.items()
        ]
        return ["--host-resolver-rules=" + ", ".join(rules), "--no-proxy-server"]

    @staticmethod
    def _origin(url: str) -> tuple[str, str | None, int]:
        parsed = urlsplit(url)
        return (
            parsed.scheme,
            parsed.hostname,
            parsed.port if parsed.port is not None else (443 if parsed.scheme == "https" else 80),
        )

    def validate(self, url: str, *, navigation: bool = True) -> str:
        if "\\" in url or any(ord(c) < 33 for c in url):
            raise ValueError("URL contains unsafe whitespace or backslashes.")
        if len(url) > 4096:
            raise ValueError("URL exceeds length limit.")
        parsed = urlsplit(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("Only absolute HTTP(S) URLs are supported.")
        if parsed.port == 0:
            raise ValueError("Port zero is not a valid scope destination.")
        if parsed.username or parsed.password or parsed.query:
            raise ValueError("Credential-bearing and query URLs are excluded from v0 discovery.")
        if parsed.fragment:
            url = canonical(url)
        if navigation and self._origin(url) != self.origin:
            raise ValueError(
                "Navigation must remain on the authorized origin (scheme, host, port)."
            )
        if self.config.allowed_domains and parsed.hostname not in self.config.allowed_domains:
            raise ValueError("Hostname is not in allowed_domains.")
        decoded_path = parsed.path
        for _ in range(4):
            decoded_path = unquote(decoded_path)
        if any(decoded_path.startswith(prefix) for prefix in self.config.excluded_paths):
            raise ValueError("Path excluded by the project's reviewed scope policy.")
        if SENSITIVE.search(decoded_path) or "\\" in decoded_path:
            raise ValueError("Potentially modifying or credential-bearing route excluded.")
        addresses = socket.getaddrinfo(parsed.hostname, parsed.port or 80, type=socket.SOCK_STREAM)
        if not addresses:
            raise ValueError("Hostname did not resolve.")
        for item in addresses:
            address = ipaddress.ip_address(item[4][0])
            if not address.is_global:
                if not (self.config.allow_localhost and address.is_loopback):
                    raise ValueError(
                        "Non-public addresses require explicit localhost demo configuration."
                    )
        return canonical(url)

    def allows(self, url: str) -> bool:
        try:
            self.validate(url)
            return True
        except ValueError, OSError:
            return False

    @staticmethod
    def _audit_url(url: str) -> dict[str, str]:
        """Keep paths for non-sensitive routes; never retain query values or userinfo."""
        try:
            parsed = urlsplit(url)
            port = parsed.port
            origin = f"{parsed.scheme}://{parsed.hostname}"
            if port is not None and port != (443 if parsed.scheme == "https" else 80):
                origin += f":{port}"
            decoded = unquote(unquote(unquote(unquote(parsed.path))))
            sensitive = SENSITIVE.search(decoded) or re.search(
                r"/(?:auth|account|admin|users)(?:/|$)", decoded
            )
            return {
                "origin": origin,
                "path": "[redacted-sensitive-path]" if sensitive else parsed.path[:2048] or "/",
                "query_keys": ",".join(
                    sorted(
                        {
                            "[redacted]"
                            if re.search(r"token|secret|password|key|session|auth", key, re.I)
                            else key[:40]
                            for key, _ in parse_qsl(parsed.query)
                        }
                    )
                ),
            }
        except ValueError:
            return {"origin": "[invalid]", "path": "[invalid]", "query_keys": ""}

    def _record_block(self, url: str, method: str, reason: str, **details) -> None:
        if len(self.blocked_requests) < 100:
            self.blocked_requests.append(
                {**self._audit_url(url), "method": method, "reason": reason, **details}
            )

    def request_decision(self, request) -> tuple[bool, str]:
        """API permission is exact and resource-only. Navigation still uses validate()."""
        if self.request_count >= self.config.max_requests:
            return False, "request_budget_exhausted"
        if request.method not in {"GET", "HEAD"}:
            return False, "method_not_read_only"
        if request.is_navigation_request():
            try:
                self.validate(request.url)
                return True, "navigation_in_scope"
            except (ValueError, OSError) as error:
                return False, f"navigation_policy: {error}"
        try:
            if len(request.url) > 4096:
                return False, "url_length_exceeded"
            parsed = urlsplit(request.url)
            origin = self._origin(request.url)
            rules = [
                r
                for r in self.config.api_resources
                if r.enabled and self._origin(r.origin) == origin and r.path == parsed.path
            ]
            if rules:
                if request.resource_type not in {"fetch", "xhr"}:
                    return False, "api_resource_type_not_allowed"
                if self.config.auth_reference or request.post_data is not None:
                    return False, "api_authentication_or_body_forbidden"
                headers = request.all_headers()
                if any(
                    key.lower()
                    in {
                        "authorization",
                        "proxy-authorization",
                        "cookie",
                        "x-api-key",
                        "x-auth-token",
                    }
                    for key in headers
                ):
                    return False, "api_authentication_headers_forbidden"
                if (
                    parsed.username
                    or parsed.password
                    or parsed.fragment
                    or "\\" in request.url
                    or any(ord(c) < 33 for c in request.url)
                ):
                    return False, "api_unsafe_url"
                if re.search(
                    r"/(?:auth|account|admin|users|login|contact|payments?)(?:/|$)",
                    parsed.path,
                    re.I,
                ):
                    return False, "api_sensitive_path_forbidden"
                pairs = parse_qsl(parsed.query, keep_blank_values=True, strict_parsing=True)
                if len({k for k, _ in pairs}) != len(pairs):
                    return False, "api_duplicate_query_key"
                if not any(
                    request.method in r.methods
                    and all(k in r.query and v in r.query[k] for k, v in pairs)
                    for r in rules
                ):
                    return False, "api_method_or_query_not_allowlisted"
                self.api_scopes[origin].validate(
                    urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))
                )
                return True, "approved_api_resource"
            self.validate(request.url)
            return True, "same_origin_resource"
        except (ValueError, OSError) as error:
            return False, f"resource_policy: {error}"

    def _install_redirect_guard(self, page) -> None:
        """Chromium response interception prevents redirect follow before egress.

        Playwright routing alone does not guarantee interception of redirect hops.
        Fail closed on redirects; no APIRequestContext/route.fetch DNS bypass is used.
        """
        if page in self._redirect_sessions:
            return
        session = page.context.new_cdp_session(page)

        def response_paused(event):
            request_id = event["requestId"]
            if event.get("responseStatusCode") in {301, 302, 303, 307, 308}:
                request = event["request"]
                location = next(
                    (
                        h["value"]
                        for h in event.get("responseHeaders", [])
                        if h["name"].lower() == "location"
                    ),
                    "",
                )
                target = self._audit_url(urljoin(request["url"], location))
                self._record_block(
                    request["url"],
                    request["method"],
                    "redirect_blocked_before_follow",
                    redirect_origin=target["origin"],
                    redirect_path=target["path"],
                )
                session.send(
                    "Fetch.failRequest", {"requestId": request_id, "errorReason": "BlockedByClient"}
                )
            else:
                session.send("Fetch.continueResponse", {"requestId": request_id})

        session.on("Fetch.requestPaused", response_paused)
        session.send(
            "Fetch.enable", {"patterns": [{"urlPattern": "*", "requestStage": "Response"}]}
        )
        self._redirect_sessions[page] = session

    def guard(self, route) -> None:
        request = route.request
        allowed, reason = self.request_decision(request)
        if not allowed:
            self._record_block(request.url, request.method, reason)
            route.abort()
        else:
            try:
                self._install_redirect_guard(request.frame.page)
            except Exception:
                self._record_block(request.url, request.method, "redirect_guard_unavailable")
                route.abort()
                return
            delay = self.config.request_interval_ms / 1000 - (
                time.monotonic() - self.last_request_at
            )
            if delay > 0:
                time.sleep(delay)
            self.last_request_at = time.monotonic()
            self.request_count += 1
            route.continue_()
