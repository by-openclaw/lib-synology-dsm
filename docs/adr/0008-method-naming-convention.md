# ADR-0008: Method Naming Convention

**Status:** Accepted
**Date:** 2026-03-31
**Deciders:** @yboujraf

## Context

As the library grows (9 managers in v1, BaseManager ABC planned for v2), method names must be consistent and predictable. Without a convention, managers diverge — some use `list()`, others `get_all()`, some use `set_permission()`, others `update_permissions()`. This creates cognitive load for consumers and makes the Ansible collection wrapper harder to build.

The v2 PoC design document (`docs/design-v2-poc.md` §5) proposed a naming table. This ADR canonicalizes that table as the binding convention for all current and future managers.

## Decision

### Primary entity methods — verb only

The manager class name is the namespace. The primary entity does not repeat in the method name.

| Verb | Contract | Idempotent? |
|---|---|---|
| `list()` | Returns `list[dict]`, read-only | N/A |
| `get(name)` | Returns `dict \| None`, single item | N/A |
| `create(name, ...)` | Creates, raises if already exists | No |
| `update(name, ...)` | Modifies, raises if not found | No |
| `delete(name, ...)` | Removes | No |
| `ensure(name, state, dry_run, ...)` | Upsert — state-driven, returns `EnsureResult` / `{"changed": bool, "action": str}` | **Yes** |

**Example:** `UserManager.list()`, `UserManager.get("bob")`, `UserManager.ensure("bob", state="present")`.

### Sub-entity methods — verb_entity

When a manager operates on a secondary resource (e.g., group membership, share permissions), the entity suffix disambiguates.

| Pattern | Example |
|---|---|
| `verb_entity()` | `UserManager.list_groups()`, `ShareManager.set_permission()` |
| `add_entity()` / `remove_entity()` | `GroupManager.add_member()`, `GroupManager.remove_member()` |

### Load/save — Unit of Work pattern

Managers that batch-read and batch-write (e.g., TrafficControlManager) use `load()` / `save()` instead of per-item CRUD. This is the documented exception to the verb-only rule.

| Verb | Contract |
|---|---|
| `load()` | Fetch full state from DSM into local buffer (read) |
| `save()` | Push local buffer to DSM (write, returns `{"changed": bool, "action": str}`) |

### Verb semantics

| Verb | Contract |
|---|---|
| `set_*()` | Replace/overwrite (permissions, rules) — idempotent |
| `add_*/remove_*()` | Membership operations — idempotent |
| `enable_*/disable_*()` | Toggle state — idempotent |

## Consequences

**Positive:**
- Consumers can predict method names without reading docs — `Manager.list()`, `.get()`, `.ensure()` are always available
- Ansible collection wrapper maps 1:1: module param `state: present` → `manager.ensure(state=State.PRESENT)`
- New managers follow the convention automatically via `BaseManager` ABC enforcement (v2)
- Sub-entity pattern (`verb_entity`) avoids method name collisions when a manager handles multiple resource types

**Negative:**
- Existing v1 managers have minor deviations (e.g., `BandwidthManager.ensure_user()` / `ensure_group()` use sub-entity form for the primary entity). These will be aligned in the v1→v2 migration — no retroactive rename in v1.
- `load()`/`save()` is an exception to the standard CRUD verbs. Documented here to prevent future debate.

## Compliance

- **ISO A.14.2.1** (secure development policy) — consistent API surface reduces integration errors
- **ISO A.12.1.1** (documented operating procedures) — naming convention is explicit and auditable

## Notes

- Source: `docs/design-v2-poc.md` §5 (method naming table)
- v2 `BaseManager` ABC will enforce `ensure()`, `list()`, `get()` at the type level — `TypeError` at instantiation if missing
- This ADR covers method naming only. Return value contract is ADR-0007. Ensure pattern semantics are ADR-0002.
