# Changelog

All notable changes to this repository are recorded here, in the format of [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Every change to a template's document is listed under the release that ships it.
A template id never starts refusing an instance it accepted before: a change that would ships under a new id.

## [Unreleased]

### Added

- **Examples:** an example instance of each template in canonical JSON, `tech/templates/{template-id}/instances/{template-id}.json`, generated with openehr-sdk-go by `make examples` and checked against its template by `make ci`.

### Changed

- **Templates:** `generic_ehr_status.v1` and `generic_folder.v1` accept more: their other details and details may now be an ITEM_TREE defined by an archetype as well as a plain one, and they still accept every instance they accepted, so a consumer that stored a copy should replace it ([#1](https://github.com/Cadasto/openehr-reference-content/issues/1)).
- **Archetypes:** `EHR_STATUS.generic` and `FOLDER.generic` keep `ITEM_TREE[at0001]`, now `0..1`, and add the slot `ITEM_TREE[at0002]` for an `openEHR-EHR-ITEM_TREE` archetype.
- **Tooling:** a template can keep a slot open (`keep_open`), which the generator writes into the OPT as an `ARCHETYPE_SLOT`; the `conformance` module checks with openehr-sdk-go v0.52.0.

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
