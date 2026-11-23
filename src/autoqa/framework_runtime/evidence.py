"""Per-operation evidence without input values or raw assertion messages."""

import json
import time
from contextlib import contextmanager
from datetime import UTC, datetime


class StepRecorder:
    def __init__(self, page, output, test_id, run_id, policy):
        self.page, self.output = page, output
        self.test_id, self.run_id, self.policy = test_id, run_id, policy
        self.records = []

    def persist(self):
        path = self.output / (self.test_id + "-steps.json")
        temporary = path.with_suffix(".tmp")
        # Windows sharing scanners/readers can briefly deny atomic replacement.
        # Retry only persistence, never an assertion or an HTTP/browser operation.
        for attempt in range(3):
            try:
                temporary.write_text(json.dumps(self.records, indent=2), encoding="utf-8")
                temporary.replace(path)
                return
            except PermissionError:
                if attempt == 2:
                    raise
                time.sleep(0.025 * (attempt + 1))

    @contextmanager
    def step(self, kind, description):
        sequence = len(self.records) + 1
        record = {
            "run_id": self.run_id,
            "test_id": self.test_id,
            "step_id": f"{self.test_id}:step-{sequence}",
            "sequence": sequence,
            "kind": kind,
            "description": description,
            "timestamp": datetime.now(UTC).isoformat(),
            "status": "NOT_EXECUTED",
            "duration": 0,
            "error": "",
            "evidence": [],
            "evidence_error": "",
        }
        self.records.append(record)
        started = time.monotonic()
        try:
            yield
        except BaseException as error:
            name = type(error).__name__
            record["status"] = (
                "SKIPPED"
                if name == "Skipped"
                else "INTERRUPTED"
                if isinstance(error, (KeyboardInterrupt, SystemExit))
                else "FAILED"
            )
            record["error"] = f"{kind} did not complete ({name})"
            raise
        else:
            record["status"] = "PASSED"
        finally:
            record["duration"] = round(time.monotonic() - started, 6)
            if self.policy == "every_step" or (
                self.policy == "failures_only" and record["status"] == "FAILED"
            ):
                try:
                    if not self.page.is_closed():
                        name = f"{self.test_id}-step-{sequence}.png"
                        self.page.screenshot(path=str(self.output / name))
                        record["evidence"].append(name)
                except Exception as error:
                    record["evidence_error"] = f"Screenshot capture failed ({type(error).__name__})"
            self.persist()
