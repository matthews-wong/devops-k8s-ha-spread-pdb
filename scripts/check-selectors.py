#!/usr/bin/env python3
"""Fail if the Service or PodDisruptionBudget selects no Deployment pods.

A selector that matches nothing is valid YAML, so schema validation passes
while the PDB protects nothing and the Service has no endpoints.
"""
import pathlib
import sys

import yaml

MANIFEST_DIR = pathlib.Path(__file__).resolve().parent.parent / "manifests"


def load(kind):
    for path in sorted(MANIFEST_DIR.glob("*.yaml")):
        for doc in yaml.safe_load_all(path.read_text()):
            if doc and doc.get("kind") == kind:
                yield path.name, doc


def selects(selector, labels):
    return all(labels.get(k) == v for k, v in selector.items())


def main():
    errors = []
    pods = [d["spec"]["template"]["metadata"]["labels"] for _, d in load("Deployment")]
    if not pods:
        sys.exit("no Deployment found in manifests/")

    checks = [
        ("Service", lambda d: d["spec"]["selector"]),
        ("PodDisruptionBudget", lambda d: d["spec"]["selector"]["matchLabels"]),
    ]
    for kind, get_selector in checks:
        for file, doc in load(kind):
            selector = get_selector(doc)
            if not any(selects(selector, labels) for labels in pods):
                errors.append(
                    f"{file}: {kind} {doc['metadata']['name']!r} selector "
                    f"{selector} matches no Deployment pod template"
                )

    for file, dep in load("Deployment"):
        name = dep["metadata"]["name"]
        labels = dep["spec"]["template"]["metadata"]["labels"]
        if not selects(dep["spec"]["selector"]["matchLabels"], labels):
            errors.append(f"{file}: Deployment {name!r} selector does not match its own pod labels")
        for tsc in dep["spec"]["template"]["spec"].get("topologySpreadConstraints", []):
            if not selects(tsc["labelSelector"]["matchLabels"], labels):
                errors.append(
                    f"{file}: spread constraint on {tsc['topologyKey']} "
                    f"does not match the pod labels of {name!r}"
                )

    for error in errors:
        print(error, file=sys.stderr)
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
