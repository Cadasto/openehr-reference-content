# SPDX-License-Identifier: MIT
#
# The one entry point for building and checking the reference content.
# Recipes are POSIX sh and the file keeps to GNU Make 3.81.

PYTHON ?= python3
GO ?= go
GENERATOR = PYTHONDONTWRITEBYTECODE=1 $(PYTHON) tools/generator/build.py

.PHONY: help generate examples check sync test vet fmt-check ci

help:
	@printf '%s\n' \
	  'make generate    write the archetypes and templates from tools/generator/content.py' \
	  'make examples    write the example instance of each template, generated with openehr-sdk-go,' \
	  '                 to tech/templates/{template-id}/instances/{template-id}.json' \
	  'make check       fail when a generated file differs from what the generator writes,' \
	  '                 or a vendored CKM file from its pin in models/remote/org.openehr/MANIFEST.txt' \
	  'make sync        fetch the pinned CKM clusters again and rewrite MANIFEST.txt (network)' \
	  'make test        the Go tests of the module and of conformance/ (the SDK checks)' \
	  'make vet         go vet both modules' \
	  'make fmt-check   fail when gofmt would change a Go file' \
	  'make ci          check, fmt-check, vet and test: the gate CI runs'

generate:
	@$(GENERATOR)

examples:
	cd conformance && $(GO) test -count=1 -run '^TestExampleInstancesAreCurrent$$' . -args -update

check:
	@$(GENERATOR) --check

sync:
	@$(GENERATOR) --sync

test:
	$(GO) test -count=1 ./...
	cd conformance && $(GO) test -count=1 ./...

vet:
	$(GO) vet ./...
	cd conformance && $(GO) vet ./...

fmt-check:
	@out="$$(gofmt -l .)"; if [ -n "$$out" ]; then printf 'gofmt would change:\n%s\n' "$$out"; exit 1; fi

ci: check fmt-check vet test
