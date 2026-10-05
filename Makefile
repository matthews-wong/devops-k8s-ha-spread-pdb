KUBERNETES_VERSION ?= 1.31.0

.PHONY: validate schema selectors

validate: schema selectors

schema:
	kubeconform -strict -summary -kubernetes-version $(KUBERNETES_VERSION) manifests

selectors:
	python3 scripts/check-selectors.py
