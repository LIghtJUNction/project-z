# zgpui → zuse: native automation contract (proposal)

Generate one semantic descriptor per actionable built-in control from the same metadata that draws it: role, stable view key, localized label, enabled/visible flags, and supported actions with typed parameters. Neither pixels nor synthesized mouse movement is needed. Applications using stock controls get the default implementation; raw canvases/custom controls without semantics are reported unsupported unless they expose their own semantics.

## Discovery and dispatch

- Function key is deterministic from stable application/view/action keys (e.g. `preferences.appearance.set_theme`), not translated labels or transient widget order. Duplicate IDs are errors; IDs on virtualized/recycled rows include the model key.
- Generate the short description from role/action/label, with optional app-authored override. Expose just names/descriptions first; fetch the argument schema only for a selected function. Never expose passwords, form values, or hidden controls by default.
- Each session binds to an explicitly approved local application instance. Dispatch by instance, view generation, stable control ID and action ID. Verify the same generation, enabled state, and scope at dispatch on that app's UI thread; if the app replaced the control, return a stale-target error. Do not focus a window, move the system pointer, or fall back to generic input.
- Reuse the existing semantic/widget arena, use compact numeric IDs and static descriptors where possible, and stream bounded changes. Allocate no second scene tree; no observer work when unsubscribed. Local transport must authenticate callers and scope operations. Use separate app instances/sessions for parallel requests; serialize conflicting writes within one instance. Observe does not imply write permission.
- Measure cold catalog generation, incremental updates, steady-state dispatch and P95 application acknowledgement. Compare allocations and peak RSS against the same zgpui app with integration off; report the actual numbers, not a speed target as a result.

First fixture: built-in button, edit field, and panel switch; with another window foreground, generate a manifest, invoke each permitted control, reject disabled/stale and duplicate keys, and demonstrate no focus or cursor change. This document is a proposed contract, not a shipped zgpui implementation.
