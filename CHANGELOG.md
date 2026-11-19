# Changelog

All notable changes to this repository are recorded here, in the format of [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Every change to a template's document is listed under the release that ships it.
A template id never starts refusing an instance it accepted before: a change that would ships under a new id.

## [Unreleased]

## [0.1.0] - 2026-11-20

### Added

- **Templates:** `generic_ehr_status.v1` and `generic_folder.v1`, the generic EHR_STATUS and FOLDER templates, with the template ids, uids and constraints they had in openehr-sdk-go, now generated from archetypes of their own.
- **Templates:** `PERSON-Patient.v1`, `PERSON-PatientIdentity.v1`, `PERSON-CareProvider.v1`, `ROLE-generic-role.v1`, `AGENT-generic-agent.v1`, `GROUP-CareTeam.v1`, `ORGANISATION-generic.v1` and `GROUP-generic.v1`, one for each party a demographic service holds.
- **Archetypes:** thirteen local ADL 1.4 archetypes: `EHR_STATUS.generic`, `FOLDER.generic`, `PERSON.generic_person`, `ROLE.generic_role`, `AGENT.generic_agent`, `GROUP.care_team`, `GROUP.generic_group`, `ORGANISATION.generic_organisation`, and the relationships `care_relationship`, `party_membership`, `role_assignment`, `acting_on_behalf` and `part_of`.
- **CKM clusters:** `structured_name.v1`, `address.v1`, `electronic_communication.v1`, `person.v1` and `device.v1`, vendored under `models/remote/org.openehr/` and pinned by sha256.
- **Go module:** package `reference` embeds the templates (`TemplateIDs`, `OPT`) with no dependency outside the standard library.
- **Tooling:** the generator under `tools/generator/`, `make generate`, `make check`, `make sync`, `make ci`, and the `conformance` module that checks every template with openehr-sdk-go.

[Unreleased]: https://github.com/Cadasto/openehr-reference-content/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Cadasto/openehr-reference-content/releases/tag/v0.1.0
