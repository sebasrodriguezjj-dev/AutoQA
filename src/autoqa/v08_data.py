"""Bounded synthetic data aliases and execution-only credential references."""

import csv
import hashlib
import io
import json
import re

from autoqa.authorization import require_authorization
from autoqa.core import TestCase
from autoqa.domain import artifact_reference
from autoqa.framework_runtime.contracts import APIScenario, DataFixture, nonsecret
from autoqa.planning import save_cases, verify_approval_binding
from autoqa.v08_contracts import (
    TestDataDefinition,
    TestDataInventory,
    ValidationResult,
    canonical,
    digest,
)
from autoqa.v08_io import MAX_BYTES, checked_root, read_bytes, read_json

INVENTORY = "test-cases/test-data-v08.json"
BINDINGS = "test-cases/test-data-bindings-v08.json"
ENV_REFERENCE = re.compile(r"AUTOQA_SECRET_[A-Z0-9_]{1,64}")


def _normalize(value):
    data = value.model_dump(mode="json")
    for definition in data["definitions"]:
        definition["environments"] = sorted(definition["environments"])
    data["definitions"].sort(key=lambda item: item["alias"])
    return TestDataInventory.model_validate(data)


def _inventory_digest(value):
    return digest(["autoqa-test-data-inventory-v1", value.model_dump(mode="json")])


def _bounded_serialization(value):
    if len(canonical(value).encode("utf-8")) > MAX_BYTES:
        raise ValueError("Test-data output exceeds bounds")


def _rows(value):
    # Reuse the strict synthetic-value and existing API fixture constraints, not a
    # permissive CSV/JSON interpretation with a second execution representation.
    checked = TestDataDefinition(
        alias="validation.rows",
        kind="value",
        environments=["validation"],
        sensitivity="SYNTHETIC",
        values=value,
    )
    nonsecret(checked.values)
    return DataFixture(name="v08", rows=checked.values).rows


def _file_rows(definition, raw):
    if definition.kind == "json":
        # Parse bytes using the same duplicate/nonfinite rules as source JSON.
        def pairs(items):
            result = {}
            for key, item in items:
                if key in result:
                    raise ValueError("Duplicate dataset field")
                result[key] = item
            return result

        def constant(_):
            raise ValueError("Nonfinite dataset value")

        value = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=constant)
    elif definition.kind == "csv":
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8"), newline=""))
        fields = reader.fieldnames
        if not fields or len(set(fields)) != len(fields) or len(fields) > 30:
            raise ValueError("Invalid CSV header")
        value = []
        for row in reader:
            if len(value) >= 30 or None in row or any(item is None for item in row.values()):
                raise ValueError("Invalid CSV row")
            value.append(row)
    else:
        raise ValueError("File alias is not an API-row dataset")
    return _rows(value)


def _binding_digest(value):
    return digest(
        [
            "autoqa-test-data-bindings-v1",
            {key: item for key, item in value.items() if key != "digest"},
        ]
    )


class TestDataService:
    def __init__(self, project, authorization=None):
        self.project, self.authorization = project, authorization

    def _inventory(self, input_path=None):
        path = input_path if input_path is not None else self.project.storage.path(INVENTORY)
        value = _normalize(TestDataInventory.model_validate(read_json(path)))
        if value.project_id != self.project.root.name:
            raise ValueError("Wrong data project")
        for definition in value.definitions:
            if definition.kind == "credential" and not ENV_REFERENCE.fullmatch(
                definition.reference or ""
            ):
                raise ValueError("Credentials require declared AUTOQA_SECRET environment names")
            if definition.kind == "value":
                _rows(definition.values)
        _bounded_serialization(value)
        return value

    def inspect(self, input_path=None):
        """Parse declared inventory; do not resolve files or credential values."""
        try:
            return self._inventory(input_path)
        except ValueError, TypeError, OSError, RecursionError, OverflowError:
            raise ValueError("Invalid bounded test-data inventory") from None

    def import_inventory(self, path, authorized_roots=()):
        require_authorization(self.authorization, self.project.root, "plan")
        try:
            inventory = self._inventory(path)
            if len(authorized_roots) > 20:
                raise ValueError("Too many authorized data roots")
            if any(str(root).startswith(("\\\\", "//")) for root in authorized_roots):
                raise ValueError("Remote data roots are unsupported")
            roots = [checked_root(root) for root in authorized_roots]
            identities = [str(root.resolve()).casefold() for root in roots]
            if len(set(identities)) != len(identities):
                raise ValueError("Duplicate authorized data root")
            definitions, aliases = [], {}
            for definition in inventory.definitions:
                updated = definition.model_dump(mode="json")
                if definition.kind in {"json", "csv", "file"}:
                    artifact_reference(definition.reference)
                    matches = []
                    for root in roots:
                        candidate = root / definition.reference
                        # Ancestor/entry links and regular-file checks occur before read.
                        if candidate.exists() or candidate.is_symlink() or candidate.is_junction():
                            raw = read_bytes(candidate)
                            if not candidate.resolve().is_relative_to(root.resolve()):
                                raise ValueError("File escapes authorized root")
                            matches.append((root, raw))
                    if len(matches) != 1:
                        raise ValueError("File requires exactly one explicit authorized root")
                    root, raw = matches[0]
                    fingerprint = hashlib.sha256(raw).hexdigest()
                    if definition.fingerprint is not None and definition.fingerprint != fingerprint:
                        raise ValueError("Declared data fingerprint changed")
                    if definition.kind in {"json", "csv"}:
                        _file_rows(definition, raw)
                    updated["fingerprint"] = fingerprint
                    aliases[definition.alias] = {
                        "root": str(root),
                        "root_binding": digest(str(root.resolve())),
                        "reference": definition.reference,
                        "fingerprint": fingerprint,
                    }
                elif definition.kind == "value":
                    fingerprint = digest(["autoqa-synthetic-rows-v1", definition.values])
                    if definition.fingerprint is not None and definition.fingerprint != fingerprint:
                        raise ValueError("Declared data fingerprint changed")
                    updated["fingerprint"] = fingerprint
                definitions.append(updated)
            imported = _normalize(
                TestDataInventory(project_id=inventory.project_id, definitions=definitions)
            )
            bindings = {
                "schema_version": "0.8",
                "project_id": inventory.project_id,
                "inventory_digest": _inventory_digest(imported),
                "aliases": aliases,
            }
            bindings["digest"] = _binding_digest(bindings)
            _bounded_serialization(imported)
            _bounded_serialization(bindings)
        except ValueError, TypeError, OSError, RecursionError, OverflowError, csv.Error:
            raise ValueError("Invalid or unauthorized test-data import") from None
        # Validate the complete transaction before any writes. Single-writer atomic
        # files are not an authenticated multi-file transaction or a credential vault.
        self.project.storage.write_json(INVENTORY, imported.model_dump(mode="json"))
        self.project.storage.write_json(BINDINGS, bindings)
        return imported

    def _current(self):
        inventory = self._inventory()
        bindings = read_json(self.project.storage.path(BINDINGS))
        if not isinstance(bindings, dict) or set(bindings) != {
            "schema_version",
            "project_id",
            "inventory_digest",
            "aliases",
            "digest",
        }:
            raise ValueError("Invalid data binding")
        if bindings["schema_version"] != "0.8" or bindings["project_id"] != inventory.project_id:
            raise ValueError("Invalid data binding")
        if bindings["inventory_digest"] != _inventory_digest(inventory) or bindings[
            "digest"
        ] != _binding_digest(bindings):
            raise ValueError("Stale data binding")
        if not isinstance(bindings["aliases"], dict) or len(bindings["aliases"]) > 100:
            raise ValueError("Invalid alias binding")
        expected = {
            item.alias for item in inventory.definitions if item.kind in {"json", "csv", "file"}
        }
        if set(bindings["aliases"]) != expected:
            raise ValueError("Conflicting alias binding")
        return inventory, bindings

    def _validate_alias(self, alias, environment):
        inventory, bindings = self._current()
        definition = next((item for item in inventory.definitions if item.alias == alias), None)
        if definition is None or environment not in definition.environments:
            raise ValueError("Unknown alias or environment")
        value = {"alias": definition.alias, "kind": definition.kind, "environment": environment}
        if definition.kind == "credential":
            value["reference"] = definition.reference
            findings = [
                "Credential reference declared; secret remains unresolved until authorized execution."
            ]
        elif definition.kind == "value":
            if definition.fingerprint != digest(["autoqa-synthetic-rows-v1", definition.values]):
                raise ValueError("Synthetic data identity changed")
            value["rows"] = _rows(definition.values)
            findings = [
                "Synthetic API fixture rows validated; no execution or approval was performed."
            ]
        else:
            bound = bindings["aliases"][alias]
            if not isinstance(bound, dict) or set(bound) != {
                "root",
                "root_binding",
                "reference",
                "fingerprint",
            }:
                raise ValueError("Invalid file binding")
            root = checked_root(bound["root"])
            if (
                bound["root_binding"] != digest(str(root.resolve()))
                or bound["reference"] != definition.reference
            ):
                raise ValueError("Changed authorized source binding")
            candidate = root / artifact_reference(definition.reference)
            raw = read_bytes(candidate)
            fingerprint = hashlib.sha256(raw).hexdigest()
            if (
                not candidate.resolve().is_relative_to(root.resolve())
                or fingerprint != bound["fingerprint"]
                or fingerprint != definition.fingerprint
            ):
                raise ValueError("Data source changed")
            value["reference"] = definition.reference
            value["fingerprint"] = fingerprint
            if definition.kind in {"json", "csv"}:
                value["rows"] = _file_rows(definition, raw)
            findings = [
                "Authorized regular-file identity matches imported data; source content is not emitted for file aliases."
            ]
        identity = digest(
            [
                "autoqa-test-data-validation-v1",
                _inventory_digest(inventory),
                definition.model_dump(),
                environment,
            ]
        )
        return ValidationResult(
            project_id=inventory.project_id,
            digest=identity,
            valid=True,
            findings=findings,
            value=value,
        )

    def validate_alias(self, alias, environment):
        try:
            return self._validate_alias(alias, environment)
        except ValueError, TypeError, KeyError, OSError, RecursionError, OverflowError, csv.Error:
            raise ValueError("Invalid, stale or unauthorized test-data reference") from None

    def bind_case(self, alias, case_id, environment):
        require_authorization(self.authorization, self.project.root, "maintain")
        require_authorization(self.authorization, self.project.root, "review")
        try:
            validation = self._validate_alias(alias, environment)
            matrix = read_json(self.project.storage.path("test-cases/test-matrix.json"))
            if not isinstance(matrix, list) or len(matrix) > 1000:
                raise ValueError("Invalid current case inventory")
            cases = [TestCase.model_validate(item) for item in matrix]
            if len({case.id for case in cases}) != len(cases):
                raise ValueError("Duplicate current case identity")
            original = next((case for case in cases if case.id == case_id), None)
            if original is None or original.kind != "api":
                raise ValueError("Only existing API cases support reusable data binding")
            if original.review_status == "rejected":
                raise ValueError("Rejected cases require renewed scenario review")
            if original.review_status == "approved":
                verify_approval_binding(self.project, original)
            scenario = APIScenario.model_validate(original.contract)
            if scenario.environment != environment:
                raise ValueError("Data binding cannot change approved environment")
            changed = scenario.model_dump()
            if validation.value["kind"] == "credential":
                if scenario.authentication.strategy not in {"bearer", "cookie"}:
                    raise ValueError(
                        "Credential binding requires an existing bearer or cookie strategy"
                    )
                changed["authentication"]["token_env"] = validation.value["reference"]
            elif "rows" in validation.value:
                changed["data"] = DataFixture(
                    name="v08", rows=validation.value["rows"]
                ).model_dump()
            else:
                raise ValueError("Raw file aliases cannot be executed as API fixture rows")
            approved_shape = {
                key: value
                for key, value in scenario.model_dump().items()
                if key not in {"data", "authentication"}
            }
            revised = APIScenario.model_validate(changed)
            if {
                key: value
                for key, value in revised.model_dump().items()
                if key not in {"data", "authentication"}
            } != approved_shape:
                raise ValueError("Data binding changed reviewed behavior")
            value = original.model_dump()
            value.update(contract=revised.model_dump(), review_status="pending")
            value["description"] = "V0.8 data binding " + alias + " revision " + validation.digest
            candidate = TestCase.model_validate(value)
            cases = [candidate if case.id == case_id else case for case in cases]
        except ValueError, TypeError, KeyError, OSError, RecursionError, OverflowError, csv.Error:
            raise ValueError("Unsupported, stale or invalid test-data case binding") from None
        save_cases(self.project, cases, authorization=self.authorization)
        return candidate
