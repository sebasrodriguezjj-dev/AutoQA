"""V0.5 declarative contracts, shared verbatim with standalone exports."""

import json
import random
import re
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, JsonValue, field_validator, model_validator

SENSITIVE = re.compile(r"authorization|cookie|token|password|secret|api.?key|session", re.I)


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    schema_version: Literal["0.5"] = "0.5"


def nonsecret(value):
    """Reject conventional sensitive keys; arbitrary operator data still requires review."""
    if isinstance(value, dict):
        if any(SENSITIVE.search(str(k)) for k in value):
            raise ValueError("Use environment references for sensitive values")
        for child in value.values():
            nonsecret(child)
    elif isinstance(value, list):
        for child in value:
            nonsecret(child)
    return value


def origin(value):
    parsed = urlsplit(value)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or not re.fullmatch(r"[a-zA-Z0-9.-]+", parsed.hostname)
        or parsed.username
        or parsed.password
        or parsed.path
        or parsed.query
        or parsed.fragment
        or parsed.port == 0
        or any(ord(c) < 33 for c in value)
    ):
        raise ValueError("Require an exact HTTP(S) origin without credentials/path/wildcards")
    return value.lower()


class Authentication(Contract):
    strategy: Literal["none", "bearer", "basic", "cookie"] = "none"
    token_env: str | None = None
    username_env: str | None = None
    password_env: str | None = None
    cookie_name: str | None = None

    @model_validator(mode="after")
    def references(self):
        for name in (self.token_env, self.username_env, self.password_env):
            if name is not None and not re.fullmatch(r"AUTOQA_SECRET_[A-Z0-9_]{1,64}", name):
                raise ValueError("Credentials require AUTOQA_SECRET_* environment references")
        needed = {
            "none": (),
            "bearer": (self.token_env,),
            "basic": (self.username_env, self.password_env),
            "cookie": (self.token_env, self.cookie_name),
        }[self.strategy]
        if any(not item for item in needed):
            raise ValueError("Missing authentication reference")
        if self.cookie_name and not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,63}", self.cookie_name):
            raise ValueError("Invalid cookie name")
        if self.strategy == "none" and any(
            (self.token_env, self.username_env, self.password_env, self.cookie_name)
        ):
            raise ValueError("Unused authentication references")
        return self


class Environment(Contract):
    name: str = Field(pattern=r"^[a-z][a-z0-9_-]{0,31}$")
    origin: str
    allow_localhost: bool = False
    values: dict[str, JsonValue] = Field(default_factory=dict)

    _origin = field_validator("origin")(origin)
    _values = field_validator("values")(nonsecret)


class DataFixture(Contract):
    name: str = Field(pattern=r"^[a-z][a-z0-9_-]{0,31}$")
    seed: int = Field(default=0, ge=0, le=2**32 - 1)
    rows: list[dict[str, JsonValue]] = Field(
        default_factory=lambda: [{}], min_length=1, max_length=30
    )

    _rows = field_validator("rows")(nonsecret)

    def materialize(self, index, environment):
        # No global RNG or clock dependency; one isolated mapping for each invocation.
        value = (
            dict(environment.values)
            | self.rows[index]
            | {"synthetic_id": random.Random(self.seed + index).randint(100000, 999999)}
        )
        return json.loads(json.dumps(value))


class Request(Contract):
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"] = "GET"
    path: str = Field(pattern=r"^/[A-Za-z0-9/_-]{0,199}$")
    query: dict[str, str] = Field(default_factory=dict)
    headers: dict[str, str] = Field(default_factory=dict)
    json_body: JsonValue = None
    timeout_seconds: float = Field(default=5, ge=0.1, le=30)
    mutation_review: str | None = Field(default=None, min_length=10, max_length=500)

    @model_validator(mode="after")
    def safe_request(self):
        if "//" in self.path:
            raise ValueError("Literal relative path required")
        if self.method != "GET" and not self.mutation_review:
            raise ValueError("Mutating operations require explicit reviewed scope and expectations")
        nonsecret(self.query)
        nonsecret(self.json_body)
        for key, value in self.headers.items():
            if (
                not re.fullmatch(r"[A-Za-z][A-Za-z0-9-]{0,63}", key)
                or key.lower()
                in {
                    "host",
                    "content-length",
                    "transfer-encoding",
                    "connection",
                    "proxy-authorization",
                }
                or SENSITIVE.search(key)
            ):
                raise ValueError("Reserved/sensitive headers require authentication references")
            if any(ord(c) < 32 or ord(c) > 126 for c in value):
                raise ValueError("Unsafe header value")
        if len(json.dumps(self.model_dump())) > 65536:
            raise ValueError("Request contract too large")
        return self


class ResponseAssertions(Contract):
    status: int = Field(ge=100, le=599)
    headers: dict[str, str] = Field(default_factory=dict)
    json_values: dict[str, JsonValue] = Field(default_factory=dict)
    json_types: dict[
        str, Literal["object", "array", "string", "number", "integer", "boolean", "null"]
    ] = Field(default_factory=dict)

    @model_validator(mode="after")
    def safe_expectations(self):
        nonsecret(self.headers)
        nonsecret(self.json_values)
        for path in [*self.json_values, *self.json_types]:
            if path and not re.fullmatch(r"[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+)*", path):
                raise ValueError("JSON field paths use dotted keys/array indices")
        return self


class EvidencePolicy(Contract):
    sensitive_headers: list[str] = Field(
        default_factory=lambda: ["authorization", "cookie", "set-cookie"]
    )
    sensitive_fields: list[str] = Field(default_factory=list)
    retention: Literal["summary_only"] = "summary_only"
    # Raw HTTP payloads and authenticated UI capture never reach persistent artifacts.


class APIScenario(Contract):
    id: str = Field(pattern=r"^TC-[A-Za-z0-9_-]{1,70}$")
    title: str = Field(min_length=1, max_length=200)
    request: Request
    expect: ResponseAssertions
    environments: list[Environment] = Field(min_length=1, max_length=10)
    environment: str
    authentication: Authentication = Field(default_factory=Authentication)
    data: DataFixture = Field(default_factory=lambda: DataFixture(name="default"))
    evidence: EvidencePolicy = Field(default_factory=EvidencePolicy)
    polarity: Literal["positive", "negative"] = "positive"

    @model_validator(mode="after")
    def relationships(self):
        names = [e.name for e in self.environments]
        if len(set(names)) != len(names) or self.environment not in names:
            raise ValueError("Select a unique declared environment")
        # Query/body fixture placeholders must resolve now, before approval/export.
        for env in self.environments:
            for i in range(len(self.data.rows)):
                substitute(self.request.query, self.data.materialize(i, env))
                substitute(self.request.json_body, self.data.materialize(i, env))
                substitute(self.expect.json_values, self.data.materialize(i, env))
        return self


class APIResult(Contract):
    run_id: str
    test_id: str
    operation_id: str
    status: Literal["PASSED", "FAILED", "ERROR"]
    status_code: int | None = None
    duration: float = Field(ge=0)
    masked_headers: dict[str, str] = Field(default_factory=dict)
    sensitive_fields: list[str] = Field(default_factory=list)


def substitute(value, data):
    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        name = value[2:-1]
        if name not in data:
            raise ValueError("Unknown fixture/environment value reference")
        return data[name]
    if isinstance(value, dict):
        return {k: substitute(v, data) for k, v in value.items()}
    if isinstance(value, list):
        return [substitute(v, data) for v in value]
    return value
