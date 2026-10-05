# k8s-ha-spread-pdb

A small set of plain Kubernetes manifests for a stateless web service that
should survive node drains and a zone outage: a multi-replica Deployment with
topology spread constraints, a PodDisruptionBudget, and a hardened pod spec.

## Layout

| File | Purpose |
| --- | --- |
| `manifests/namespace.yaml` | Namespace with the restricted Pod Security profile enforced |
| `manifests/serviceaccount.yaml` | Dedicated account, API token not mounted |
| `manifests/deployment.yaml` | 3 replicas, zone + node spread, probes, limits, hardening |
| `manifests/service.yaml` | ClusterIP in front of the pods |
| `manifests/pdb.yaml` | Keeps at least 2 pods up during voluntary disruptions |
| `scripts/check-selectors.py` | Verifies Service and PDB selectors match the pod labels |

## Design notes

- **Spread:** `topologySpreadConstraints` with `maxSkew: 1` across
  `topology.kubernetes.io/zone` (soft, `ScheduleAnyway`) and
  `kubernetes.io/hostname` (hard, `DoNotSchedule`). Zones are soft so a
  single-zone cluster still schedules.
- **PDB:** `minAvailable: 2` with 3 replicas allows one pod to be evicted at a
  time. A PDB whose selector matches nothing is silently useless, hence the
  selector check script.
- **Rollouts:** `maxUnavailable: 0` so a rolling update never dips below the
  PDB floor.

## Validate

```sh
make validate
```

Runs `kubeconform` (strict) and the selector check. See the Makefile.

## Caveats

- `kubeconform` checks the schema only; the spread and PDB behaviour needs a
  real multi-node cluster. Not exercised here.
- The hard hostname constraint leaves a pod `Pending` on a cluster with fewer
  than two schedulable nodes.
- `PyYAML` is required for the selector check (`pip install pyyaml`).
