# Design: v2 Pattern PoC — BaseManager, Typed Results, Error Handling

> **Scope:** `src/synology_dsm_v2/` — isolated proof-of-concept, same repo
> **Date:** 2026-03-31
> **Author:** Claude Opus (design session with @yboujraf)
> **Status:** APPROVED for agent execution
> **Rule:** Do NOT touch `src/synology_dsm/` or `tests/unit/`. v1 stays untouched.

---

## Goal

Prove that proper design patterns (ABC, enums, typed results, properties, error handling) work for this library — using ONE manager as the reference implementation. When proven, the pattern replaces v1 in a single migration PR.

---

## Folder structure

```
lib-synology-dsm/
  src/synology_dsm/            ← v1 (DO NOT TOUCH)
  src/synology_dsm_v2/         ← PoC (NEW)
    __init__.py
    base.py                    ← BaseManager ABC, EnsureResult, State, Action
    client.py                  ← DSMClient with @property, __repr__, context manager
    exceptions.py              ← Full hierarchy, __repr__, error code map
    users.py                   ← ONE manager — full pattern implementation
  tests/unit/                  ← v1 tests (DO NOT TOUCH)
  tests/unit_v2/               ← PoC tests (NEW)
    test_base.py               ← ABC enforcement tests
    test_client.py             ← Properties, context manager, error mapping
    test_exceptions.py         ← Every error code maps, __repr__, no crash
    test_users.py              ← ensure(), CRUD, dry_run, error handling
```

---

## 1. Design patterns

### 1.1 BaseManager ABC

```python
from abc import ABC, abstractmethod

class BaseManager(ABC):
    """Contract: every manager has ensure(), __repr__, and a client."""

    def __init__(self, client: DSMClient) -> None:
        self._client = client

    @abstractmethod
    def ensure(
        self,
        name: str,
        state: State = State.PRESENT,
        dry_run: bool = False,
        **kwargs,
    ) -> EnsureResult:
        ...

    @abstractmethod
    def list(self) -> list[dict]:
        ...

    @abstractmethod
    def get(self, name: str) -> dict | None:
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(base_url={self._client.base_url!r})"
```

**What this enforces:**
- Every manager has `ensure()`, `list()`, `get()` — or Python raises `TypeError` at instantiation
- Every manager has `__repr__` for debugging
- Every manager receives `DSMClient` via dependency injection

**Test: `test_base.py`**
```python
def test_cannot_instantiate_without_ensure():
    class BadManager(BaseManager):
        def list(self): return []
        def get(self, name): return None
        # missing ensure() → should crash

    with pytest.raises(TypeError):
        BadManager(mock_client)
```

### 1.2 State enum

```python
from enum import StrEnum

class State(StrEnum):
    PRESENT = "present"
    ABSENT = "absent"
```

**Why:** `State.PRESENT` not `"present"` — typo `"pressent"` is caught by IDE, not by a runtime bug 3 weeks later.

### 1.3 Action enum

```python
class Action(StrEnum):
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    NOOP = "noop"
    WOULD_CREATE = "would_create"
    WOULD_UPDATE = "would_update"
    WOULD_DELETE = "would_delete"
```

### 1.4 EnsureResult dataclass

```python
@dataclass(frozen=True)
class EnsureResult:
    changed: bool
    action: Action
    before: dict | None = None
    after: dict | None = None
    dry_run: bool = False
```

**Why:** `result.changed` not `result["changed"]` — IDE autocompletion, type safety, immutable (frozen).

**Backward compatibility:** Add a `.to_dict()` method so Ansible wrappers can call `result.to_dict()` to get the familiar `{"changed": True, "action": "created"}` format.

```python
def to_dict(self) -> dict:
    d = {"changed": self.changed, "action": self.action.value}
    if self.before is not None:
        d["before"] = self.before
    if self.after is not None:
        d["after"] = self.after
    if self.dry_run:
        d["dry_run"] = True
    return d
```

---

## 2. DSMClient with properties

```python
class DSMClient:
    def __init__(
        self,
        host: str,
        port: int = 5001,
        https: bool = True,
        verify_ssl: bool = False,
        timeout: int = 30,
    ) -> None:
        self._host = host
        self._port = port
        self._https = https
        self._verify_ssl = verify_ssl
        self._timeout = timeout
        self._sid: str | None = None
        self._synotoken: str = ""

    @property
    def base_url(self) -> str:
        scheme = "https" if self._https else "http"
        return f"{scheme}://{self._host}:{self._port}/webapi"

    @property
    def sid(self) -> str | None:
        """Session ID — read-only. Set by login()."""
        return self._sid

    @property
    def synotoken(self) -> str:
        """X-SYNO-TOKEN — read-only. Set by login()."""
        return self._synotoken

    @property
    def timeout(self) -> int:
        return self._timeout

    @timeout.setter
    def timeout(self, value: int) -> None:
        if value < 1:
            raise ValueError("Timeout must be >= 1 second")
        self._timeout = value

    def __repr__(self) -> str:
        return f"DSMClient(host={self._host!r}, port={self._port}, sid={'***' if self._sid else None})"

    def __enter__(self) -> "DSMClient":
        return self

    def __exit__(self, *_) -> None:
        self.logout()
```

**What changed from v1:**
- `_sid` and `_synotoken` are read-only via `@property` — can't accidentally overwrite
- `base_url` computed from properties, not stored as mutable string
- `timeout` has a setter with validation
- `__repr__` shows useful info, masks session ID

---

## 3. Error handling — complete, no crash

### 3.1 Exception hierarchy (same as v1, add `__repr__`)

```python
class DSMError(Exception):
    def __init__(self, message: str, code: int | None = None) -> None:
        super().__init__(message)
        self.code = code

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(code={self.code}, message={self.args[0]!r})"
```

Every subclass inherits `__repr__`. When debugging: `DSMAuthError(code=400, message='Invalid credentials')` not `DSMAuthError('Invalid credentials')`.

### 3.2 Complete error code map

```python
_ERROR_MAP: dict[int, type[DSMError]] = {
    # Auth errors
    400: DSMAuthError,
    401: DSMAuthError,
    402: DSMAuthError,
    # Permission errors
    103: DSMPermissionError,
    403: DSMPermissionError,
    # Session errors
    105: DSMSessionError,
    106: DSMSessionError,
    119: DSMSessionError,
    # Not found
    104: DSMNotFoundError,
    408: DSMNotFoundError,
    # Invalid parameter
    100: DSMInvalidParameterError,
    101: DSMInvalidParameterError,
    102: DSMInvalidParameterError,
    120: DSMInvalidParameterError,
    1001: DSMInvalidParameterError,
    1009: DSMInvalidParameterError,
    1010: DSMInvalidParameterError,
    # Invalid operation
    117: DSMInvalidOperationError,
}
```

**Rule:** Unknown error code → `DSMAPIError(code=N, message=...)` — never swallowed, never crashes.

### 3.3 Tests for error handling

```python
# Every known code maps correctly
@pytest.mark.parametrize("code,expected", [
    (400, DSMAuthError),
    (402, DSMAuthError),
    (403, DSMPermissionError),
    (119, DSMSessionError),
    (999, DSMAPIError),  # unknown → generic fallback
])
def test_error_code_mapping(code, expected):
    ...

# Network failures → DSMConnectionError (never raw urllib)
def test_network_error_wrapped():
    ...

# __repr__ is useful
def test_exception_repr():
    err = DSMAuthError("Bad password", code=400)
    assert "400" in repr(err)
    assert "Bad password" in repr(err)
```

---

## 4. UserManager — full pattern

```python
class UserManager(BaseManager):
    """Synology DSM user management — CRUD + ensure."""

    def list(self) -> list[dict]:
        """List all local users."""
        ...

    def get(self, name: str) -> dict | None:
        """Get a single user by name. Returns None if not found."""
        ...

    def create(self, name: str, password: str, **kwargs) -> dict:
        """Create a user. Raises if already exists."""
        ...

    def update(self, name: str, **kwargs) -> dict:
        """Update a user. Raises if not found."""
        ...

    def delete(self, name: str, dry_run: bool = False) -> EnsureResult:
        """Delete a user."""
        ...

    def ensure(
        self,
        name: str,
        state: State = State.PRESENT,
        dry_run: bool = False,
        **kwargs,
    ) -> EnsureResult:
        """
        Idempotent user management.

        state=PRESENT: create if missing, update if drifted, noop if matches
        state=ABSENT: delete if exists, noop if already gone
        dry_run=True: compute diff, return what would happen, no API calls
        """
        current = self.get(name)

        if state == State.PRESENT:
            if current is None:
                if dry_run:
                    return EnsureResult(changed=False, action=Action.WOULD_CREATE, dry_run=True)
                created = self.create(name, **kwargs)
                return EnsureResult(changed=True, action=Action.CREATED, after=created)
            # ... diff logic, return UPDATED or NOOP
            ...

        elif state == State.ABSENT:
            if current is None:
                return EnsureResult(changed=False, action=Action.NOOP)
            if dry_run:
                return EnsureResult(changed=False, action=Action.WOULD_DELETE, before=current, dry_run=True)
            self.delete(name)
            return EnsureResult(changed=True, action=Action.DELETED, before=current)
```

---

## 5. Method naming convention

| Pattern | Rule | Example |
|---|---|---|
| Primary entity | `verb()` only — class is the namespace | `UserManager.list()`, `UserManager.get("bob")` |
| Sub-entity | `verb_entity()` | `UserManager.list_groups()`, `ShareManager.set_permission()` |
| Load/save (Unit of Work) | `load()` / `save()` | `TrafficControlManager.load()` / `.save()` — keep as-is |

**Verbs:**

| Verb | Contract | Idempotent? |
|---|---|---|
| `list()` | Returns `list[dict]`, read-only | N/A |
| `get()` | Returns `dict | None`, single item | N/A |
| `create()` | Creates, raises if exists | No |
| `update()` | Modifies, raises if not found | No |
| `delete()` | Removes | No |
| `ensure()` | Upsert — state-driven, returns `EnsureResult` | **Yes** |
| `set_*()` | Replace/overwrite (permissions, rules) | Yes |
| `add_*/remove_*()` | Membership operations | Yes |
| `load()/save()` | Unit of Work (traffic control) | load=read, save=write |

---

## 6. Generic transport — not HTTP-only

The `ensure()` pattern works for any protocol:

```
REST API (Synology DSM)  → DSMClient._post(url, data)
SNMP (Arista switches)   → SNMPClient.set(oid, value)
TCP (broadcast control)  → TCPClient.send(command)
gRPC (future services)   → GRPCClient.call(method, request)
```

The `BaseManager` contract doesn't care about transport:

```python
class ClientProtocol(Protocol):
    """Minimum interface any transport client must implement."""
    @property
    def base_url(self) -> str: ...
    def request(self, api: str, method: str, version: int = 1, **params) -> dict: ...

class BaseManager(ABC):
    def __init__(self, client: ClientProtocol) -> None:
        self._client = client

    @abstractmethod
    def ensure(self, name: str, state: State, dry_run: bool = False, **kwargs) -> EnsureResult:
        ...
```

**Note:** `ClientProtocol` keeps typing strict for DSM now (DSMClient implements it). When a Go CLI wrapper or SNMP client is added, it implements the same protocol — type checking still works. `Any` would disable all type checking on `self._client`.

When a Go lib or C++ lib is created, the same `ensure()` contract applies — different language, same interface. The Ansible/consumer wrapper reads `{changed, action}` regardless of language or transport.

---

## 7. Success criteria

The PoC is proven when:

- [ ] `BaseManager` ABC — `TypeError` raised if `ensure()` missing
- [ ] `State` + `Action` enums — IDE catches typos at write time
- [ ] `EnsureResult` dataclass — `.changed`, `.action`, `.to_dict()` all work
- [ ] `DSMClient` properties — `client.sid` is read-only, `client.timeout` validates
- [ ] `__repr__` — all classes print useful debug info
- [ ] Error code map — every known DSM code maps to typed exception
- [ ] Unknown error codes — `DSMAPIError` fallback, never crashes
- [ ] Network errors — wrapped as `DSMConnectionError`, never raw `urllib.error`
- [ ] `UserManager.ensure()` — present/absent/dry_run all tested
- [ ] `UserManager.ensure()` returns `EnsureResult` (not dict)
- [ ] `.to_dict()` produces `{"changed": True, "action": "created"}` for Ansible compatibility
- [ ] All tests pass, 100% coverage on v2 modules

**When all boxes are checked:** The pattern is proven. v1 → v2 migration can proceed as a tracked PR.

---

## 8. What the agent does

1. Create `src/synology_dsm_v2/` with the 4 files
2. Create `tests/unit_v2/` with the 4 test files
3. Run tests — all must pass
4. Do NOT modify anything in `src/synology_dsm/` or `tests/unit/`
5. Commit: `feat(v2-poc): BaseManager ABC, typed results, error handling`
6. Update `openclaw-status.md`

---

*This is a design doc, not code. The agent reads it and implements. You audit when done.*
