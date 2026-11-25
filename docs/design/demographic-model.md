# The demographic model

How the demographic archetypes and templates are shaped, and why.
The normative definitions are the openEHR Reference Model's demographic package, <https://specifications.openehr.org/releases/RM/latest/demographic.html>.

## One archetype per class, one template per use

`PERSON.generic_person` carries no role: identifiers, names, a pseudonym, birth and death, administrative gender, qualifications, contacts, contact persons, languages and relationships.
The two PERSON templates select from it what one use needs:

| Template | Use | Holds | Keeps out |
|---|---|---|---|
| `PERSON-Patient.v1` | A patient, the subject of an EHR | Identifiers (at least one, such as the patient number), names, a pseudonym, date of birth, gender, death, marital status, multiple birth, place of birth, addresses, telecom, languages, contact persons; care relationships and role assignments | Qualifications, additional details, memberships, acting on behalf, a second pseudonym |
| `PERSON-CareProvider.v1` | A member of staff who provides care | Names, identifiers, date of birth, gender, qualifications, contacts, languages; memberships and role assignments | Death and birth details, contact persons, pseudonyms, care relationships |

ROLE, AGENT, ORGANISATION and the two GROUPs each have an archetype and a template of their own.

## A patient is one party, whose identifying values can be masked

`PERSON-Patient.v1` is the one party that stands for a patient: the subject an EHR_STATUS references, and who the patient is.
A service that keeps identifying values apart from the record may store the party with them masked: each masked ELEMENT keeps its node, loses its value and carries the null flavour masked (openehr code 272).
So every ELEMENT of the template leaves its value optional and puts no constraint on its null flavour.
A masked name is still a PARTY_IDENTITY, so the party keeps the identity the Reference Model requires; the identifier stays mandatory, and the pseudonym is optional.

## Names, identifiers and contacts

- Names are PARTY_IDENTITYs. The identity's name is its purpose, the kind of name: FHIR NameUse for a person, DeviceNameType for an agent, the kinds of the CKM `organisation_name` draft for an organisation.
- Identifiers go in details, as DV_IDENTIFIER: the kind of identifier in `type` (for example a code of HL7 v2 table 0203: MR, PI, ANON, NI, PPN, XX), the scheme's authority in `issuer`, the organisation that assigned it in `assigner`. National numbers need no element of their own.
- A CONTACT is named by its purpose, FHIR AddressUse and ContactPointUse; its `time_validity` is the period of use. Postal addresses and electronic addresses are ADDRESSes holding the CKM `address` and `electronic_communication` clusters. An organisation's contacts leave out `home`, which FHIR does not allow for one.

## Relationships

A PARTY_RELATIONSHIP is held by its source party and versioned with it, as the Reference Model has it.
The source is always the smaller party:

| Relationship | Source | Target | Meaning |
|---|---|---|---|
| `care_relationship` | A patient | PERSON, GROUP or ORGANISATION | The patient is in the target's care, as primary or responsible care provider, care team, case manager or managing organisation |
| `party_membership` | A member | GROUP or ORGANISATION | The source is a member of the target, in a role |
| `role_assignment` | An actor | ROLE | The source holds the role |
| `acting_on_behalf` | An actor | ORGANISATION, PERSON or GROUP | The source acts for the target, on a stated basis |
| `part_of` | An organisation | ORGANISATION | The source is a part of the target, such as a ward of a hospital |

- The archetype id is the relationship's type, so a query or a rule selects relationships by archetype, and each archetype constrains the class of its target.
- A group is only ever a target. A care team's members and patients hold their relationships to it, so admitting a patient or adding a member writes the patient or the member, never the group. Neither GROUP template holds a relationship; FHIR's CareTeam.managingOrganization and Group.managingEntity have no place in them.
- The reverse side is read, not stored: a provider's patients, or a team's members, are the relationships that target it.

## ROLE

`ROLE.performer` is mandatory in the Reference Model, and the archetype keeps it so.
A role may then be held by one actor, named in its performer, or a service may keep one ROLE per function and record who holds it through `role_assignment` relationships, which departs from the model's own reading of `performer`.
Capabilities name what the role permits, such as access scopes, and what it requires.

## Coded lists and FHIR

Every coded list is local codes that match an HL7 FHIR R4 value set one to one, with the FHIR code in each code's description, and each element's comment names the FHIR element it corresponds to.
The care team categories are also bound to their LOINC codes.
Text is allowed beside the codes where FHIR's binding is extensible.

## Left out

- National elements, such as a name's prefix or a partner's name, or a house number's letter and addition. They belong in a national extension: a specialisation of these archetypes, or a template of its own.
- Clinical observations about a person, such as sex, gender identity, ethnicity or occupation: they belong in the health record.
- The location where care takes place, such as a room or a bed.
