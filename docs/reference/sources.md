# Sources

What the archetypes and templates were built from and checked against.

## openEHR

- Reference Model, demographic package: <https://specifications.openehr.org/releases/RM/latest/demographic.html>
- Reference Model, EHR package (EHR_STATUS, FOLDER): <https://specifications.openehr.org/releases/RM/latest/ehr.html>
- ADL 1.4 and AOM 1.4: <https://specifications.openehr.org/releases/AM/latest/ADL1.4.html>
- Operational template XML schema, ITS-XML `AM/Release-1.4/Template.xsd`: <https://specifications.openehr.org/releases/ITS-XML/latest>
- CKM demographic drafts (in development, CKM project *Demographics RM archetypes*): `PERSON.person.v0`, `PERSON.person-patient.v0`, `PARTY_IDENTITY.person_name.v0`, `ROLE.individual_provider.v0`, `CAPABILITY.individual_credentials.v0`, `ORGANISATION.organisation.v0` (1013.1.475), `PARTY_IDENTITY.organisation_name.v0` (1013.1.476)
- CKM published clusters, embedded: see [ATTRIBUTION.md](../../ATTRIBUTION.md)
- CKM `openEHR-EHR-CLUSTER.organisation.v1` (1013.1.371) was considered and not used: its misuse section rules out a formal demographic register.

## HL7 FHIR R4 (4.0.1)

| Resource | Used for |
|---|---|
| [Patient](https://hl7.org/fhir/R4/patient.html) | PERSON-Patient.v1 |
| [Practitioner](https://hl7.org/fhir/R4/practitioner.html), [PractitionerRole](https://hl7.org/fhir/R4/practitionerrole.html) | PERSON-CareProvider.v1, ROLE-generic-role.v1, role_assignment |
| [RelatedPerson](https://hl7.org/fhir/R4/relatedperson.html) | Contact persons |
| [Device](https://hl7.org/fhir/R4/device.html) | AGENT-generic-agent.v1 |
| [CareTeam](https://hl7.org/fhir/R4/careteam.html) | GROUP-CareTeam.v1, party_membership, care_relationship |
| [Organization](https://hl7.org/fhir/R4/organization.html) | ORGANISATION-generic.v1, part_of |
| [Group](https://hl7.org/fhir/R4/group.html) | GROUP-generic.v1 |

## Checked with

- openehr-sdk-go: strict read and compile, generated instances validated, refusals (`conformance/`)
- archie 3.14.0: ADL 1.4 parse, conversion to ADL 2 and validation of every archetype
- xmllint against `Template.xsd` (Release-1.4)
- EHRbase 2.38.0 and FerroEHR 5.7.1-rc1: template upload; EHRbase Web Templates; FerroEHR stored generated parties with their relationships
