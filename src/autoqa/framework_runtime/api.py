"""Bounded direct HTTP client: exact reviewed origin, pinned DNS, no redirects/proxies."""

import base64
import http.client
import ipaddress
import json
import os
import socket
import time
from urllib.parse import urlencode, urlsplit

from .contracts import APIResult, APIScenario, Authentication, substitute


class APIExecutionError(AssertionError):
    """Generic public message; raw transport/response/credential details are never persisted."""


def credentials(auth):
    def required(name):
        value = os.environ.get(name or "")
        if not value or len(value) > 8192 or any(ord(c) < 32 or ord(c) > 126 for c in value):
            raise APIExecutionError("Required test-application credential is missing or invalid")
        return value

    if auth.strategy == "none":
        return {}
    if auth.strategy == "basic":
        user, password = required(auth.username_env), required(auth.password_env)
        if ":" in user:
            raise APIExecutionError("Invalid Basic authentication username")
        value = base64.b64encode((user + ":" + password).encode()).decode()
        return {"Authorization": "Basic " + value}
    value = required(auth.token_env)
    if auth.strategy == "bearer":
        if any(c.isspace() for c in value):
            raise APIExecutionError("Invalid bearer credential")
        return {"Authorization": "Bearer " + value}
    if any(c in value for c in ';,"\\ '):
        raise APIExecutionError("Invalid cookie credential")
    return {"Cookie": auth.cookie_name + "=" + value}


def ui_auth(reference):
    if not reference:
        return Authentication()
    parts = reference.split(":")
    if len(parts) != 3 or parts[0] != "cookie":
        raise ValueError(
            "Authenticated framework export is unsupported except reviewed cookie:ENV:NAME references"
        )
    return Authentication(strategy="cookie", token_env=parts[1], cookie_name=parts[2])


def endpoint(environment):
    parsed = urlsplit(environment.origin)
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    addresses = socket.getaddrinfo(parsed.hostname, port, type=socket.SOCK_STREAM)
    if not addresses:
        raise APIExecutionError("API target DNS resolution failed")
    for item in addresses:
        address = ipaddress.ip_address(item[4][0])
        if not address.is_global and not (environment.allow_localhost and address.is_loopback):
            raise APIExecutionError("API target is outside the reviewed network boundary")
    if parsed.scheme != "https" and not all(
        ipaddress.ip_address(a[4][0]).is_loopback and environment.allow_localhost for a in addresses
    ):
        raise APIExecutionError("Remote API targets require HTTPS")
    pinned = next((a[4][0] for a in addresses if a[0] == socket.AF_INET), addresses[0][4][0])
    return parsed, port, pinned


def field(value, path):
    for part in path.split(".") if path else []:
        value = value[int(part)] if isinstance(value, list) and part.isdigit() else value[part]
    return value


def check_response(expected, status, headers, body, data):
    if status != expected.status:
        raise APIExecutionError("API status assertion failed")
    for key, value in expected.headers.items():
        if headers.get(key.lower()) != value:
            raise APIExecutionError("API response-header assertion failed")
    if expected.json_values or expected.json_types:
        decoded = json.loads(body)
        for path, value in substitute(expected.json_values, data).items():
            actual = field(decoded, path)
            if type(actual) is not type(value) or actual != value:
                raise APIExecutionError("API JSON value assertion failed")
        types = {
            "object": (dict,),
            "array": (list,),
            "string": (str,),
            "number": (int, float),
            "integer": (int,),
            "boolean": (bool,),
            "null": (type(None),),
        }
        for path, kind in expected.json_types.items():
            if type(field(decoded, path)) not in types[kind]:
                raise APIExecutionError("API JSON shape assertion failed")


class APIService:
    def __init__(self, evidence):
        self.evidence = evidence

    def execute(self, value, index=0):
        scenario = APIScenario.model_validate(value)
        selected = os.environ.get("AUTOQA_ENVIRONMENT", scenario.environment)
        environment = next((e for e in scenario.environments if e.name == selected), None)
        if environment is None:
            raise APIExecutionError("Environment is not in the reviewed API contract")
        data = scenario.data.materialize(index, environment)
        started, status, auth_headers = time.monotonic(), None, {}
        connection = None
        try:
            with self.evidence.step("action", "Send reviewed API request"):
                parsed, port, pinned = endpoint(environment)
                auth_headers = credentials(scenario.authentication)
                request = scenario.request
                timeout = request.timeout_seconds
                cls = (
                    http.client.HTTPSConnection
                    if parsed.scheme == "https"
                    else http.client.HTTPConnection
                )
                connection = cls(parsed.hostname, port, timeout=timeout)
                # Keep TLS verification/SNI bound to the reviewed hostname, but connect to
                # the already validated address. No second DNS resolution or proxy exists.
                connection._create_connection = (
                    lambda address, duration, source_address=None, **kw: socket.create_connection(
                        (pinned, port), duration, source_address
                    )
                )
                query = substitute(request.query, data)
                path = request.path + ("?" + urlencode(query) if query else "")
                headers = dict(request.headers) | auth_headers
                payload = substitute(request.json_body, data)
                body = None if payload is None else json.dumps(payload).encode()
                if body is not None:
                    headers["Content-Type"] = "application/json"
                deadline = time.monotonic() + timeout
                connection.request(request.method, path, body=body, headers=headers)
                response = connection.getresponse()
                status = response.status
                if 300 <= status < 400:
                    raise APIExecutionError("API redirects are prohibited")
                chunks, size = [], 0
                while True:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise APIExecutionError("API request timed out")
                    if connection.sock:
                        connection.sock.settimeout(remaining)
                    chunk = response.read1(min(65536, 1_048_577 - size))
                    size += len(chunk)
                    if size > 1_048_576:
                        raise APIExecutionError("API response exceeds bounded size")
                    if not chunk:
                        break
                    chunks.append(chunk)
                response_headers = {k.lower(): v for k, v in response.getheaders()}
            with self.evidence.step("assertion", "Verify reviewed API response"):
                check_response(scenario.expect, status, response_headers, b"".join(chunks), data)
        except Exception as error:
            # No original exception or data-bearing traceback is exposed in generated logs.
            message = (
                str(error)
                if isinstance(error, APIExecutionError)
                else "API operation failed; review transport or declared response expectations"
            )
            raise APIExecutionError(message) from None
        finally:
            if connection:
                connection.close()
            passed = bool(self.evidence.records) and all(
                r["status"] == "PASSED" for r in self.evidence.records
            )
            result = APIResult(
                run_id=self.evidence.run_id,
                test_id=self.evidence.test_id,
                operation_id=self.evidence.test_id + ":http",
                status="PASSED" if passed else "FAILED",
                status_code=status,
                duration=round(time.monotonic() - started, 6),
                masked_headers={
                    k.lower(): "[REDACTED]"
                    for k in {
                        *scenario.request.headers,
                        *auth_headers,
                        *scenario.evidence.sensitive_headers,
                    }
                },
                sensitive_fields=scenario.evidence.sensitive_fields,
            )
            if self.evidence.records:
                self.evidence.records[0]["api"] = result.model_dump()
                self.evidence.persist()
