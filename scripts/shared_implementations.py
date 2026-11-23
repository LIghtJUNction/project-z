"""Bounded migration regression rules used by project_z.validate.

This checks reviewed provider routes and known removed bodies. It does not infer
semantic equivalence, compile Rust, or prove that a reference is reachable.
"""
from __future__ import annotations

import json
from pathlib import Path, PurePosixPath, PureWindowsPath

from rust_source import functions, production_path, production_tokens

POLICY = Path(__file__).with_name("shared_implementations.json")


def load_policy():
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    if policy["schema_version"] != 1:
        raise ValueError("unsupported shared implementation policy schema")
    return policy


def _use_tree(values, prefix=()):
    """Flatten explicit Rust use trees; wildcard imports remain unsupported."""
    entries, current, depth = [], [], 0
    for value in values + [","]:
        if value == "," and depth == 0:
            if current:
                entries.append(current)
            current = []
        else:
            current.append(value)
            depth += (value == "{") - (value == "}")
    for entry in entries:
        if "{" in entry:
            start = entry.index("{")
            head = tuple(value for value in entry[:start] if value != ":")
            yield from _use_tree(entry[start + 1:-1], prefix + head)
            continue
        split = entry.index("as") if "as" in entry else len(entry)
        path = prefix + tuple(value for value in entry[:split] if value != ":")
        if path and path[-1] == "self":
            path = path[:-1]
        alias = entry[split + 1] if split < len(entry) else path[-1] if path else ""
        if path and alias not in ("", "_", "*"):
            yield alias, path


def provider_references(ts, crate):
    """Return explicit paths rooted at a dependency, outside import declarations.

    Crate aliases, nested use trees and explicit item aliases are supported.
    Local shadowing, re-exports through other files and macro expansion require
    review; this deliberately makes no whole-program/dataflow claim.
    """
    values = [token for token, _ in ts]
    bindings, imports, omitted = {crate: (crate,)}, [], set()
    index = 0
    while index < len(values):
        start = index
        if values[index] == "use":
            while index < len(values) and values[index] != ";":
                index += 1
            imports.extend(_use_tree(values[start + 1:index]))
            omitted.update(range(start, index + 1))
        elif values[index:index + 2] == ["extern", "crate"]:
            while index < len(values) and values[index] != ";":
                index += 1
            imports.extend(_use_tree(values[start + 2:index]))
            omitted.update(range(start, index + 1))
        index += 1
    for _ in range(len(imports) + 1):
        changed = False
        for alias, path in imports:
            if path[0] in bindings:
                resolved = bindings[path[0]] + path[1:]
                if bindings.get(alias) != resolved:
                    bindings[alias] = resolved
                    changed = True
        if not changed:
            break
    found = set()
    for index, value in enumerate(values):
        if index in omitted or value not in bindings:
            continue
        before = values[index - 1] if index else ""
        if before in (".", "fn", "mod", "struct", "enum", "type", "let"):
            continue
        # Do not mistake another namespace's terminal item for an import alias.
        if index >= 3 and values[index - 2:index] == [":", ":"] and values[index - 3].isidentifier():
            continue
        path, cursor = bindings[value], index + 1
        while cursor + 2 < len(values) and values[cursor:cursor + 2] == [":", ":"]:
            name = values[cursor + 2]
            if not name.isidentifier():
                break
            path += (name,)
            cursor += 3
        if len(path) > 1:
            found.add("::".join(path[1:]))
    return found


def _has_reference(found, entry):
    return any(path == entry or path.startswith(entry + "::") for path in found)


def historical_matches(text, policy, ts=None):
    indexed = {}
    for record in policy["historical_bodies"]:
        for field in ("body_sha256", "identifiers_sha256"):
            indexed.setdefault((field, record[field]), record)
    for function in functions(text, ts):
        for field in ("body_sha256", "identifiers_sha256"):
            record = indexed.get((field, function[field]))
            if record:
                yield function, record
                break


def errors(data, root, *, command, relative, identity, policy=None):
    """Use the existing inventory and Git/path helpers; run no Cargo or network."""
    errors = []
    try:
        policy = load_policy() if policy is None else policy
        consumers = {identity(row["url"]): row for row in policy["consumers"]}
        provider_sources = policy["provider_sources"]
    except (OSError, ValueError, KeyError, TypeError) as error:
        return [f"shared implementations: cannot load reviewed policy: {error}"]
    for repo in data["repositories"]:
        consumer = consumers.get(identity(repo.get("url", "")))
        if consumer is None:
            continue
        label = repo["name"]
        try:
            source = (root / repo["path"]).resolve()
            relative(source, root)
            tracked = set(command(["git", "ls-files", "--cached", "-z", "--", "*.rs"], source).split("\0")) - {""}
            texts, tokenized = {}, {}
            generated = consumer["generated_paths"]
            for name in sorted(tracked):
                if not production_path(name, generated=generated):
                    continue
                path = source / name
                relative(path, source)
                text = path.read_text(encoding="utf-8")
                texts[name] = text
                tokenized[name] = production_tokens(text)
                for function, record in historical_matches(text, policy, tokenized[name]):
                    origin = record["source"]
                    errors.append(
                        f"{label}/{name}:{function['line']}: shared-implementation history: "
                        f"{function['name']} restores reviewed {record['capability']} body "
                        f"({origin['repository']}@{origin['commit']}:{origin['path']}:{origin['line']}, "
                        f"{origin['function']}); use its provider and retain only the contract adapter"
                    )
            for route in consumer["routes"]:
                name = route["path"]
                route_label = f"{label}/{name}"
                if name not in texts:
                    errors.append(f"{route_label}: shared-implementation route is missing, untracked or excluded; review the route policy")
                    continue
                reference_name = route.get("reference_path", name)
                if (not isinstance(reference_name, str) or not reference_name
                        or PurePosixPath(reference_name).is_absolute()
                        or PureWindowsPath(reference_name).drive
                        or "\\" in reference_name
                        or any(part in ("", ".", "..") for part in reference_name.split("/"))):
                    errors.append(f"{route_label}: shared-implementation reference path must be a canonical repository-relative path")
                    continue
                if (reference_name not in texts or (source / reference_name).is_symlink()
                        or ("reference_path" in route and not tokenized[reference_name])):
                    errors.append(f"{route_label}: shared-implementation reference source {reference_name} is missing, untracked, excluded, symlinked or test-only")
                    continue
                path = (source / name).resolve()
                owners = []
                for package in data["packages"]:
                    if package["repository"] != label:
                        continue
                    directory = (root / package["manifest"]).parent.resolve()
                    relative(directory, source)
                    if path.is_relative_to(directory):
                        owners.append((len(directory.parts), package))
                if not owners:
                    errors.append(f"{route_label}: shared-implementation route has no owning catalog package")
                    continue
                package = max(owners, key=lambda pair: pair[0])[1]
                for provider, entries in route["providers"].items():
                    normal = [dep for dep in package["dependencies"]
                              if dep["name"] == provider and dep["kind"] == "normal"]
                    accepted = [dep for dep in normal if dep["source"] == provider_sources[provider] and not dep["path"]]
                    if not accepted:
                        errors.append(f"{route_label}: shared-implementation provider {provider} requires a normal dependency "
                                      f"from {provider_sources[provider]} in {package['manifest']}; dev/build-only or replacement sources do not qualify")
                    # References must belong to an accepted source, not another
                    # same-name normal dependency with a different Cargo alias.
                    crates = {(dep.get("alias") or provider).replace("-", "_") for dep in accepted}
                    found = set().union(*(provider_references(tokenized[reference_name], crate) for crate in crates))
                    missing = [entry for entry in entries if not _has_reference(found, entry)]
                    if missing:
                        errors.append(f"{route_label}: shared-implementation provider reference missing: "
                                      f"{provider}::" + f", {provider}::".join(missing)
                                      + (f" in {reference_name}" if reference_name != name else "")
                                      + "; imports, comments, strings and test-only uses do not qualify")
        except (OSError, ValueError, RuntimeError) as error:
            errors.append(f"{label}: cannot inspect shared implementations: {error}")
    return errors
