# ANOX Model / Provider Policy

**Status:** B027-A FOUNDATION  
**Authority:** `docs/authority/B027_AI_WORKFORCE_GOVERNANCE.md`  

This policy defines the relationship between `ROLE` and `MODEL` / `PROVIDER` in the B-027 workforce.

---

## A. Role defines authority; model defines execution

- `ROLE` is a stable identity/responsibility in the workforce.
- `MODEL` or `PROVIDER` is a replaceable execution choice.
- `MODEL` has **no** authority.

For example:

- `ROLE-008` is the `AppSec / Pentest` role.
- The model assigned to execute a ROLE-008 task may be Devin SWE-1.7, Claude, or another approved provider.
- Changing the model does not change ROLE-008's authority, allowed paths, or review requirements.

---

## B. Model / provider is replaceable

- No role is permanently bound to a single provider or model.
- The project must not hardcode a dependency on any single provider.
- Preferred model for this task is Devin SWE-1.7, but B-027 does not require it.

---

## C. Task Package defines work; Role Contract defines responsibility

- The Task Package defines the work to be done, allowed paths, and stop conditions.
- The Role Contract defines who is responsible and what authority they hold.
- The model/provider selection is execution metadata recorded in the Agent Run record.

---

## D. Model cannot grant itself permissions

A model cannot:

- convert `remote_permission = NONE` into write access;
- elevate a data-egress class from D0–D3 to D4;
- bypass the one-active-writer rule;
- bypass the writer/reviewer independence rule;
- authorize a Derived Work Candidate;
- grant itself additional permissions not in the Task Package.

---

## E. Provider selection is execution metadata

The Agent Run schema records:

- `model_provider` — the provider name (e.g., `devin`, `anthropic`, `openai`);
- `model_name` — the model identifier (e.g., `swe-1.7`, `claude-sonnet-4`).

These values are descriptive, not authoritative.  
They do not appear in the Role Registry.

---

## F. No D4 access

A model cannot access D4-class material, regardless of provider or role assignment.  
D4 includes production signing keys, production credentials, service-role credentials, break-glass secrets, user plaintext, and highly sensitive production secrets.

---

## G. Model references in documents

Documents may recommend or prefer a model for a task, but they must not:

- conflate a model name with a role identifier;
- grant authority based on the model identity;
- hardcode a permanent dependency on a single provider.

---

## H. References

- B027 Authority: `docs/authority/B027_AI_WORKFORCE_GOVERNANCE.md`
- Runtime contract: `docs/workforce/ANOX_WORKFORCE_RUNTIME_INTEGRATION_CONTRACT.md`
- Role registry: `docs/workforce/registries/roles.json`
- Agent Run schema: `docs/workforce/schemas/run.schema.json`
