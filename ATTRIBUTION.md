# Attribution

The archetypes and templates in this repository are licensed under [CC-BY-SA 4.0](LICENSE); the Go and Python code under [MIT](LICENSE-MIT).
They build on the work below.

## openEHR CKM clusters (vendored and embedded)

**Source:** the openEHR Clinical Knowledge Manager, <https://ckm.openehr.org/ckm/>, exported as ADL and XML from `https://ckm.openehr.org/ckm/rest/v1/archetypes/{cid}/{adl|xml}` on 2026-11-19.

| Archetype | CKM id | Revision |
|---|---|---|
| `openEHR-EHR-CLUSTER.structured_name.v1` | 1013.1.5359 | 1.0.3 |
| `openEHR-EHR-CLUSTER.address.v1` | 1013.1.273 | 1.1.3 |
| `openEHR-EHR-CLUSTER.electronic_communication.v1` | 1013.1.5356 | 1.0.4 |
| `openEHR-EHR-CLUSTER.person.v1` | 1013.1.5358 | 1.0.5 |
| `openEHR-EHR-CLUSTER.device.v1` | 1013.1.17 | 1.1.6 |

**Licence:** © openEHR Foundation, licensed under the Creative Commons Attribution-ShareAlike 4.0 International License.

**Vendored:** [`models/remote/org.openehr/`](models/remote/org.openehr/), unmodified CKM exports; the sha256 of each file is pinned in its `MANIFEST.txt`.
**Embedded:** the demographic templates under [`tech/templates/`](tech/templates/) embed these clusters where their slots are filled, so they are under the same terms.

## openEHR CKM demographic drafts (structure)

The local archetypes follow the structure of the CKM demographic drafts `openEHR-DEMOGRAPHIC-PERSON.person.v0`, `PERSON.person-patient.v0`, `PARTY_IDENTITY.person_name.v0`, `ROLE.individual_provider.v0`, `CAPABILITY.individual_credentials.v0`, `ORGANISATION.organisation.v0` and `PARTY_IDENTITY.organisation_name.v0`, © openEHR Foundation, licensed under Creative Commons Attribution-ShareAlike 3.0.
The organisation's kinds of name (`openEHR-DEMOGRAPHIC-ORGANISATION.generic_organisation.v1`, at0021 to at0028) are adapted from `organisation_name.v0`, which takes them from ISO/DTS 27527:2007 Provider Identification.
CC-BY-SA 3.0 lets an adaptation be licensed under a later version of the licence, as these archetypes are.

## HL7 FHIR R4 value sets

The coded lists mirror value sets of HL7 FHIR R4 (4.0.1), <https://hl7.org/fhir/R4/>: AdministrativeGender, NameUse, AddressUse, ContactPointUse, marital-status (HL7 v3 MaritalStatus), DeviceNameType, FHIRDeviceStatus, CareTeamStatus, care-team-category, organization-type and GroupType.
FHIR® is a registered trademark of Health Level Seven International.

## LOINC

The categories of `openEHR-DEMOGRAPHIC-GROUP.care_team.v1` are bound to LOINC answer codes (LA27975-4, LA27976-2, LA27977-0, LA27978-8, LA28865-6, LA28866-4, LA27980-4, LA28867-2), whose display names they use.
This material contains content from LOINC (<http://loinc.org>). LOINC is copyright © Regenstrief Institute, Inc. and the Logical Observation Identifiers Names and Codes (LOINC) Committee and is available at no cost under the license at <http://loinc.org/license>. LOINC® is a registered United States trademark of Regenstrief Institute, Inc.

## openehr-sdk-go

The generic EHR_STATUS and FOLDER templates, `generic_ehr_status.v1` and `generic_folder.v1`, and the generator under [`tools/generator/`](tools/generator/), were first published in [openehr-sdk-go](https://github.com/Cadasto/openehr-sdk-go) under the MIT License, © Sebastian Iancu.
The templates are relicensed here under CC-BY-SA 4.0 by their authors, with their template ids, uids and constraints unchanged; the generator stays MIT.
