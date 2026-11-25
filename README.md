# openehr-reference-content

A reference set of openEHR archetypes and operational templates for the classes besides COMPOSITION whose instances name a template: the generic EHR_STATUS and FOLDER, and one template for each party a demographic service holds.
The templates are OPT 1.4 XML, in English, aligned with HL7 FHIR R4, and built on published openEHR CKM archetypes where CKM has them.
A clinical data repository installs them to create, build and validate these instances.

## Get the templates

Each template is one XML file, [`tech/templates/{template-id}/opt/{template-id}.opt`](tech/templates/), ready to upload to a CDR through the openEHR REST API (`POST /definition/template/adl1.4`).
Beside it, `tech/templates/{template-id}/instances/{template-id}.json` is an example instance in canonical JSON, generated from the template with openehr-sdk-go, for reference.

A Go program can embed them instead, with no dependency outside the standard library:

```sh
go get github.com/cadasto/openehr-reference-content
```

```go
import reference "github.com/cadasto/openehr-reference-content"

doc, ok := reference.OPT(reference.PatientTemplateID) // the OPT's XML, for upload or for compiling
ids := reference.TemplateIDs()                        // every template id, sorted
```

Compile a document with the openEHR SDK of your choice, for example [openehr-sdk-go](https://github.com/Cadasto/openehr-sdk-go)'s `aom14.ReadOperationalTemplate` and `templatecompile.Compile`.

## Templates

| Template id | Root | What it holds |
|---|---|---|
| `generic_ehr_status.v1` | EHR_STATUS | The archetype id a CDR gives an EHR_STATUS by default, `openEHR-EHR-EHR_STATUS.generic.v1`, with an ITEM_TREE as other details, plain or defined by an archetype |
| `generic_folder.v1` | FOLDER | The default `openEHR-EHR-FOLDER.generic.v1`, with an ITEM_TREE as details, plain or defined by an archetype, and any sub-folders and items |
| `PERSON-Patient.v1` | PERSON | A patient, as one party: identifiers (at least one, such as the patient number), names, a pseudonym, date of birth, gender, death, marital status, addresses, telecom, languages, contact persons; care relationships and role assignments. Every element can be stored masked |
| `PERSON-CareProvider.v1` | PERSON | A care provider: names, identifiers, qualifications, contacts, languages; memberships and role assignments |
| `ROLE-generic-role.v1` | ROLE | A function actors perform, with its capabilities |
| `AGENT-generic-agent.v1` | AGENT | A software application, a device or a service, with the parties it acts for |
| `GROUP-CareTeam.v1` | GROUP | A care team: status, categories, period, reasons |
| `ORGANISATION-generic.v1` | ORGANISATION | An organisation: names by kind, identifiers, types, contacts, contact persons; the organisation it is part of |
| `GROUP-generic.v1` | GROUP | Any other group, such as a household or a cohort, with the traits its members share |

The demographic templates are built on thirteen local archetypes, under [`models/local/archetypes/`](models/local/archetypes/), and five published CKM clusters, under [`models/remote/org.openehr/`](models/remote/org.openehr/).
[`docs/design/demographic-model.md`](docs/design/demographic-model.md) explains their shape: why a patient is one party whose identifying values a service can mask, why each relationship type is an archetype held by its source party, and what each template keeps out.
[`docs/reference/sources.md`](docs/reference/sources.md) lists what they were built from and checked against.

## Stability

A server stores a template, and the instances written against it, so the template under an id holds still.
A template id never starts refusing an instance it accepted before: a change that would ships under a new id, such as `PERSON-Patient.v2`, and the old id's template stays.
[`CHANGELOG.md`](CHANGELOG.md) records every change to a template's document.
The content is at `in_development` (archetypes) and `Initial` (templates) and has had no clinical review.

## Layout

The layout follows the [freshEHR](https://github.com/freshehrteam/_-freshEHR-project-folder) and [Apperta](https://github.com/Apperta-CKM/ckm-project-template) project folders, with archetypes filed by class as in the openEHR CKM mirror.

| Path | Holds |
|---|---|
| `models/local/archetypes/{class}/` | The archetypes this repository authors, ADL 1.4 |
| `models/remote/org.openehr/` | Published CKM archetypes the templates embed, as CKM exports them, pinned by sha256 |
| `tech/templates/{template-id}/opt/` | The operational templates |
| `tech/templates/{template-id}/instances/` | An example instance of each template, generated with openehr-sdk-go |
| `docs/design/`, `docs/reference/` | Design notes and sources |
| `tools/generator/` | The generator that writes every archetype and template from one definition, `content.py` |
| `conformance/` | A Go module that checks every template with openehr-sdk-go |
| `*.go` | The Go package `reference`, which embeds the templates |

## Development

The archetypes and templates are generated: change [`tools/generator/content.py`](tools/generator/content.py), run `make generate`, then `make examples`, and never edit the files by hand.

```sh
make generate   # write the archetypes and templates
make examples   # write each template's example instance, with openehr-sdk-go
make ci         # what CI runs: generated files and CKM pins, gofmt, go vet, the tests of both modules
make sync       # fetch the pinned CKM clusters again (network)
```

The generator needs Python 3.9 or later with its standard library only; the Go modules need Go 1.27.
`make ci` runs on GNU Make 3.81 and later.
[`AGENTS.md`](AGENTS.md) holds the rules for changing the content.

## Licence

The archetypes and templates are licensed under the [Creative Commons Attribution-ShareAlike 4.0 International License](LICENSE), the licence of the CKM content they embed.
The Go and Python code, the Makefile and the CI workflow are [MIT](LICENSE-MIT).
[`ATTRIBUTION.md`](ATTRIBUTION.md) credits the openEHR CKM, HL7 FHIR and LOINC content they use.
