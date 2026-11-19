# AGENTS.md

Instructions for coding agents and contributors. [README.md](README.md) says what the repository holds; this file says how to change it.

## What this is

A reference set of openEHR archetypes (ADL 1.4) and operational templates (OPT 1.4 XML), English (British spelling), aligned with HL7 FHIR R4.
Every archetype and template is **generated** from one Python definition, [`tools/generator/content.py`](tools/generator/content.py).
A standard-library-only Go package (`reference`, the root module) embeds the templates; a second Go module, [`conformance/`](conformance/), checks them with openehr-sdk-go.

## Commands

```sh
make generate   # write models/local/archetypes/** and tech/templates/*/opt/*.opt from content.py
make check      # fail when a generated file differs from content.py, or a CKM file from its MANIFEST pin
make ci         # check + gofmt + go vet + go test of both modules: what CI runs
make sync       # re-fetch the pinned CKM clusters (network); review the diff, then make generate
cd conformance && go test -run TestDemographicTemplatesRefuseWhatTheyKeepOut ./...   # one check
```

## Layout

| Path | What | Edit by hand? |
|---|---|---|
| `tools/generator/content.py` | Every archetype and template, defined once | Yes: the source |
| `tools/generator/aom.py` | AOM 1.4 model, ADL and OPT writers, CKM XML reader, template operations | Yes |
| `tools/generator/build.py` | Paths, metadata (`META`), CKM pins (`CKM_CLUSTERS`), `--check`, `--sync` | Yes |
| `models/local/archetypes/{class}/` | Generated ADL; `demographic/` for DEMOGRAPHIC archetypes, else the RM class (`ehr_status/`, `folder/`) | No |
| `models/remote/org.openehr/` | CKM exports, pinned by sha256 in `MANIFEST.txt` | No: `make sync` |
| `tech/templates/{id}/opt/{id}.opt` | Generated OPTs, one folder per template id | No |
| `reference.go`, `doc.go` | The Go package: id constants, `TemplateIDs`, `OPT` | Yes |
| `reference_test.go` | sha256 pin of every template | Yes, with every template change |
| `conformance/` | SDK checks: strict compile, generate and validate, refusals | Yes |

## Rules

- **Never edit generated or vendored files.** Change `content.py` and run `make generate`; `make check` fails on any hand edit.
- **A template id never starts refusing an instance it accepted.** A narrowing change ships under a new id (`.v2`) beside the old one, which stays. Any change to a template's bytes moves its pin in `reference_test.go` and adds a line to `CHANGELOG.md` under `[Unreleased]`.
- **Archetype paths are stable.** Never renumber or reuse an at-code; removing a node or narrowing a constraint needs a new major version (`.v2`).
- **Templates only narrow.** Use the operations in `aom.py` (`drop`, `occurrences`, `existence`, `fill`, `date_pattern`); `occurrences` refuses a widening, and `close_slots` closes every slot a template leaves unfilled.
- **A new template** needs: an entry in `content.TEMPLATES` with a fresh uuid4, a constant in `reference.go`, a pin in `reference_test.go`, its root in `roots` in `conformance/conformance_test.go`, a row in the README's table, and a CHANGELOG line. The tests fail until the constant, the pin and the root are there; the README row and the CHANGELOG line are yours to add.
- **A new CKM archetype** goes in `CKM_CLUSTERS` in `build.py`, then `make sync` writes it and its pin; credit it in `ATTRIBUTION.md`.
- **Demographic modelling** follows [`docs/design/demographic-model.md`](docs/design/demographic-model.md): names are PARTY_IDENTITYs, identifiers go in details as DV_IDENTIFIER, a relationship is held by its source (the smaller party), its archetype id is its type and its PARTY_REF type list constrains the target, a GROUP is only ever a target.
- **Coded lists** mirror an HL7 FHIR R4 value set one to one as local codes, with the FHIR code in each code's description; each element's comment names the FHIR element it corresponds to.
- **The root Go module imports only the standard library.** Never add the SDK to the root `go.mod`; it belongs to `conformance/`, which reaches the root module through `replace ../`. Move the SDK pin with `cd conformance && go get github.com/cadasto/openehr-sdk-go@<ref> && go mod tidy`.
- **Each `tech/templates/{id}/` holds exactly `opt/{id}.opt`**, which the `go:embed` pattern and `TestTemplateIDsListEveryFolder` rely on.

## Platform floor

Contributors work on macOS (arm64, BSD tools) and Debian 13 (amd64, GNU tools); CI runs Ubuntu.

- Python: 3.9, standard library only: no `match`, no `X | Y` type unions at runtime, `pathlib` paths, output written with `newline="\n"`. On macOS, `/usr/bin/python3` is 3.9: run `make check PYTHON=/usr/bin/python3` to test the floor.
- Make: GNU Make 3.81; recipes are POSIX sh, which dash runs on Debian and CI.
- Go: 1.27, the `go` directive at the minor's `.0`.

## Licences and public content

- Archetypes, templates and docs: CC-BY-SA 4.0 ([LICENSE](LICENSE)). Go, Python, Makefile and workflows: MIT ([LICENSE-MIT](LICENSE-MIT)), each code file starting with `SPDX-License-Identifier: MIT`.
- Third-party content (CKM, FHIR, LOINC) is credited in [ATTRIBUTION.md](ATTRIBUTION.md); add a section for any new source.
- The repository is public: never name private downstream projects, customers or people in files, commits or pull requests. Describe what a consumer needs, not who it is.

## Commits

[Conventional Commits](https://www.conventionalcommits.org/), scoped to the area (`templates`, `archetypes`, `generator`, `go`, `docs`, `ci`).
An AI-assisted commit ends with the trailer `Assisted-by: <tool> (<model>)`, never `Co-Authored-By`.

## Before a release

`make ci` does not run the ITS-XML schema or an independent ADL parser. Before tagging, validate every OPT with `xmllint --schema` against ITS-XML `AM/Release-1.4/Template.xsd` (the schema declares the `http://schemas.openehr.org/v2` namespace, so rewrite `v1` to `v2` in a temporary copy) and every archetype with archie (`ADL14Parser`, `ADL14Converter`, `ArchetypeValidator`), and upload the changed templates to a CDR.
