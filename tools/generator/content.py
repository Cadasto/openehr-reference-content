# SPDX-License-Identifier: MIT
"""The reference archetypes and the operational templates built from them."""
from aom import (A, ITEMS, C, CODED, DV, E, SLOT, CKM_SLOT, PARTY_REF, STAR, Archetype,
                 begin_terms, end_terms, instantiate, drop, occurrences, existence,
                 fill, date_pattern, keep_open)

REL = r"openEHR-DEMOGRAPHIC-PARTY_RELATIONSHIP\.%s(-[a-zA-Z0-9_]+)*\.v1"
ANY_CLUSTER = r".*"

def fhir(what):
    return "the HL7 FHIR R4 (4.0.1) %s (https://hl7.org/fhir/R4/)" % what


CKM_V0 = ("the openEHR CKM demographic drafts (openEHR-DEMOGRAPHIC-PERSON.person.v0, "
          "PERSON.person-patient.v0, PARTY_IDENTITY.person_name.v0, ROLE.individual_provider.v0, "
          "CAPABILITY.individual_credentials.v0)")


def archetype(archetype_id, uid, build, description, bindings=None):
    begin_terms()
    definition = build()
    return Archetype(archetype_id, definition, end_terms(), uid=uid,
                     description=description, bindings=bindings)


def electronic_contact(code_contact, code_address, code_tree, code_slot, coded_use=False):
    """A CONTACT that holds electronic addresses, each a CKM electronic communication cluster."""
    attrs = []
    if coded_use:
        attrs.append(A("name", _contact_use() + [DV("DV_TEXT")]))
    attrs.append(A("addresses", [
        C("ADDRESS", code_address, "Electronic communication",
          "An electronic address, such as a telephone number, an email address or a URL.", [
              A("details", [C("ITEM_TREE", code_tree, "Electronic communication details",
                              "The structure that holds the electronic address.", [
                                  ITEMS(SLOT("CLUSTER", code_slot, "Electronic communication",
                                             "The electronic address.",
                                             [CKM_SLOT("electronic_communication")], occ=(1, 1)),
                                        card=(1, 1, False, False))])])],
          occ=(0, STAR))], card=(1, STAR, False, False)))
    return C("CONTACT", code_contact, "Contact",
             "A group of addresses at which the party can be reached for one purpose, with the period in which they are valid.",
             attrs, occ=(0, STAR))


def _contact_use():
    return [CODED(
        ("at0047", "Home", "The addresses of the party's home. Corresponds to FHIR use home."),
        ("at0048", "Work", "The addresses at which the party works. Corresponds to FHIR use work."),
        ("at0049", "Temporary", "Addresses in use for a limited period. Corresponds to FHIR use temp."),
        ("at0050", "Old", "Addresses that are no longer in use. Corresponds to FHIR use old."),
        ("at0051", "Billing", "Addresses for invoices and payment. Corresponds to FHIR AddressUse billing."),
    )]


def postal_and_electronic_contact(code, description, uses, comment, postal, electronic):
    """A CONTACT named by its use that holds postal addresses, each a CKM address cluster, and
    electronic addresses, each a CKM electronic communication cluster. postal and electronic
    are the codes of the ADDRESS, its ITEM_TREE and its slot."""
    return C("CONTACT", code, "Contact", description, [
        A("name", uses + [DV("DV_TEXT")]),
        A("addresses", [
            C("ADDRESS", postal[0], "Postal address", "A physical or postal address.", [
                A("details", [C("ITEM_TREE", postal[1], "Postal address details",
                                "The structure that holds the address.", [
                    ITEMS(SLOT("CLUSTER", postal[2], "Address", "The address.",
                               [CKM_SLOT("address")], occ=(1, 1)), card=(1, 1, False, False))])])],
              occ=(0, STAR)),
            C("ADDRESS", electronic[0], "Electronic communication",
              "An electronic address, such as a telephone number or an email address.", [
                A("details", [C("ITEM_TREE", electronic[1], "Electronic communication details",
                                "The structure that holds the electronic address.", [
                    ITEMS(SLOT("CLUSTER", electronic[2], "Electronic communication", "The electronic address.",
                               [CKM_SLOT("electronic_communication")], occ=(1, 1)),
                          card=(1, 1, False, False))])])],
              occ=(0, STAR))], card=(1, STAR, False, False))],
        occ=(0, STAR), comment=comment)


# ---------------------------------------------------------------- EHR_STATUS and FOLDER

_GENERIC_REFERENCES = ("CKM publishes no archetype for this class. The archetype id is the one EHRbase gives an "
                       "instance of it by default, so a template on it validates what a CDR creates.")


# Each ITEM_STRUCTURE class, its open node's code, its slot's code, and what it holds.
_ITEM_STRUCTURES = [
    ("ITEM_TREE", "tree", "at0001", "at0002", "a tree of items"),
    ("ITEM_LIST", "list", "at0003", "at0004", "a list of elements"),
    ("ITEM_SINGLE", "single item", "at0005", "at0006", "a single element"),
    ("ITEM_TABLE", "table", "at0007", "at0008", "a table of rows"),
]
ITEM_STRUCTURE_SLOTS = [s[3] for s in _ITEM_STRUCTURES]


def _any_item_structure(text, about):
    """Any ITEM_STRUCTURE, the RM type of EHR_STATUS.other_details and FOLDER.details: each
    of its four classes as an open node, and as a slot for the class's archetypes."""
    nodes = []
    for rm, name, plain, slot, holds in _ITEM_STRUCTURES:
        nodes.append(C(rm, plain, text if rm == "ITEM_TREE" else "%s %s" % (text, name),
                       "Further details about the %s, as %s." % (about, holds), occ=(0, 1)))
        nodes.append(SLOT(rm, slot, "Archetyped %s %s" % (text.lower(), name),
                          "Further details about the %s, as %s that an archetype defines." % (about, holds),
                          [r"openEHR-EHR-%s\..+" % rm]))
    return nodes


def _ehr_status():
    return C("EHR_STATUS", "at0000", "EHR Status",
             "The status of an EHR: its subject, whether it may be queried and modified, and other details.", [
        A("other_details", _any_item_structure("Other details", "EHR status"), existence=(0, 1)),
    ])


EHR_STATUS = archetype("openEHR-EHR-EHR_STATUS.generic.v1", "f06767d8-6671-404e-b273-73728ea33e96", _ehr_status, {
    "purpose": "To give an EHR_STATUS the archetype id a CDR gives it by default, with any item structure as its other details: a tree, a list, a single item or a table, plain or defined by an archetype.",
    "use": "Use for the EHR_STATUS of an EHR that needs no structure beyond the Reference Model's: its subject, whether it is queryable and modifiable, and other details left open.",
    "misuse": "Not for data about the patient: record clinical data in compositions and who the patient is in a demographic service. Not where the other details must follow one structure: fill a slot with that structure's archetype in a template, or specialise this archetype.",
    "keywords": ["EHR status", "subject", "queryable", "modifiable"],
    "references": _GENERIC_REFERENCES,
})


def _folder():
    return C("FOLDER", "at0000", "Folder",
             "A folder that groups versioned items of an EHR, and further folders.", [
        A("details", _any_item_structure("Details", "folder"), existence=(0, 1)),
    ])


FOLDER = archetype("openEHR-EHR-FOLDER.generic.v1", "335b7782-4722-4d80-bb13-259da8f06eea", _folder, {
    "purpose": "To give a FOLDER the archetype id a CDR gives it by default, with any item structure as its details, plain or defined by an archetype, and any sub-folders and items.",
    "use": "Use for a folder of an EHR's directory, or of a demographic service's, that needs no structure beyond the Reference Model's.",
    "misuse": "Not where a folder's details must follow one structure: fill a slot with that structure's archetype in a template, or specialise this archetype. Not where its sub-folders or items have a structure of their own: specialise this archetype or author another.",
    "keywords": ["folder", "directory", "episode", "grouping"],
    "references": _GENERIC_REFERENCES,
})


# ---------------------------------------------------------------- PERSON

def _person():
    return C("PERSON", "at0000", "Person",
             "A human being recorded as a party in a demographic service, independent of any role the person plays.", [
        A("details", [C("ITEM_TREE", "at0001", "Details",
                        "Data about the person other than names and contacts.", [ITEMS(
            E("at0002", "Identifier",
              "An identifier issued for the person, such as a patient number, a pseudonym, a national person number, a passport number or a professional registration number.",
              [DV("DV_IDENTIFIER")], occ=(0, STAR),
              comment="Record the kind of identifier in type (for example a code of HL7 v2 table 0203: MR, PI, ANON, NI, PPN, DL, PRN, NPI, LN), the authority whose scheme it belongs to in issuer, and the organisation that assigned it in assigner. Corresponds to FHIR Patient.identifier and Practitioner.identifier."),
            E("at0003", "Date of birth", "The date on which the person was born.",
              [DV("DV_DATE")],
              comment="A partial date, such as the year alone, may be recorded. Corresponds to FHIR birthDate."),
            E("at0004", "Administrative gender",
              "The gender of the person used for administrative purposes.",
              [CODED(
                  ("at0005", "Male", "Male. FHIR AdministrativeGender code male."),
                  ("at0006", "Female", "Female. FHIR AdministrativeGender code female."),
                  ("at0007", "Other", "Other than male or female. FHIR AdministrativeGender code other."),
                  ("at0008", "Unknown", "The gender is not known. FHIR AdministrativeGender code unknown."))],
              comment="The four codes match FHIR AdministrativeGender one to one. It is not an observation of sex or of gender identity; those belong in the health record."),
            E("at0009", "Deceased", "Whether the person is known to have died.",
              [DV("DV_BOOLEAN")], comment="Corresponds to FHIR deceasedBoolean."),
            E("at0010", "Date and time of death", "When the person died, as precisely as it is known.",
              [DV("DV_DATE_TIME")], comment="Corresponds to FHIR deceasedDateTime."),
            E("at0011", "Marital status", "The person's marital or civil status.",
              [CODED(
                  ("at0012", "Annulled", "The marriage was declared never to have existed. HL7 v3 MaritalStatus code A."),
                  ("at0013", "Divorced", "The marriage was dissolved. HL7 v3 MaritalStatus code D."),
                  ("at0014", "Interlocutory", "A divorce is subject to a final decree. HL7 v3 MaritalStatus code I."),
                  ("at0015", "Legally separated", "Legally separated. HL7 v3 MaritalStatus code L."),
                  ("at0016", "Married", "A current marriage contract is active. HL7 v3 MaritalStatus code M."),
                  ("at0017", "Polygamous", "More than one current spouse. HL7 v3 MaritalStatus code P."),
                  ("at0018", "Never married", "No marriage contract has ever been entered. HL7 v3 MaritalStatus code S."),
                  ("at0019", "Domestic partner", "A person declares that a domestic partner relationship exists. HL7 v3 MaritalStatus code T."),
                  ("at0020", "Unmarried", "Currently not in a marriage contract. HL7 v3 MaritalStatus code U."),
                  ("at0021", "Widowed", "The spouse has died. HL7 v3 MaritalStatus code W.")),
               DV("DV_TEXT")],
              comment="The codes are those of the FHIR R4 marital-status value set. Corresponds to FHIR Patient.maritalStatus."),
            E("at0022", "Multiple birth",
              "Whether the person was born as part of a multiple birth, or the person's position in the birth order.",
              [DV("DV_BOOLEAN"), DV("DV_COUNT")],
              comment="Record a Boolean, or a count for the birth order. Corresponds to FHIR multipleBirth[x]."),
            SLOT("CLUSTER", "at0023", "Place of birth", "The place where the person was born.",
                 [CKM_SLOT("address")], comment="Corresponds to the FHIR patient-birthPlace extension."),
            C("CLUSTER", "at0024", "Qualification",
              "A qualification, licence or certification the person holds, such as a professional registration or an academic degree.", [
                  ITEMS(
                      E("at0025", "Qualification", "The name or code of the qualification.",
                        [DV("DV_TEXT")], occ=(1, 1),
                        comment="Coding is preferred, for example with HL7 v2 table 0360 or a national register's codes."),
                      E("at0026", "Qualification identifier", "An identifier of the qualification, such as a registration number.",
                        [DV("DV_IDENTIFIER")], occ=(0, STAR)),
                      E("at0027", "Issuer", "The organisation that issued the qualification.", [DV("DV_TEXT")]),
                      E("at0028", "Period of validity", "The period in which the qualification is valid.",
                        [DV("DV_INTERVAL<DV_DATE>")]))],
              occ=(0, STAR), comment="Corresponds to FHIR Practitioner.qualification."),
            SLOT("CLUSTER", "at0029", "Contact person",
                 "A person to contact about this person, such as next of kin or an emergency contact.",
                 [CKM_SLOT("person")], occ=(0, STAR),
                 comment="Record how the contact relates to this person in the cluster's Role element, for example with HL7 v2 table 0131 (C emergency contact, N next of kin). Corresponds to FHIR Patient.contact."),
            SLOT("CLUSTER", "at0030", "Additional details",
                 "Further details about the person that a particular use needs.",
                 [ANY_CLUSTER], occ=(0, STAR)))])], existence=(0, 1)),
        A("identities", [
            C("PARTY_IDENTITY", "at0031", "Person name", "A name by which the person is known.", [
                A("name", [CODED(
                    ("at0032", "Usual", "The name the person is usually known by. FHIR NameUse code usual."),
                    ("at0033", "Official", "The name registered officially, such as on a birth certificate or passport. FHIR NameUse code official."),
                    ("at0034", "Temporary", "A name used for a limited period. FHIR NameUse code temp."),
                    ("at0035", "Nickname", "An informal name the person uses. FHIR NameUse code nickname."),
                    ("at0036", "Anonymous", "A name used to keep the person anonymous. FHIR NameUse code anonymous."),
                    ("at0037", "Old", "A name no longer in use. FHIR NameUse code old."),
                    ("at0038", "Maiden", "A name used before marriage. FHIR NameUse code maiden.")),
                    DV("DV_TEXT")]),
                A("details", [C("ITEM_TREE", "at0039", "Name details", "The name and its parts.", [ITEMS(
                    E("at0040", "Full name", "The whole name, as it is displayed.", [DV("DV_TEXT")],
                      comment="Corresponds to FHIR HumanName.text."),
                    SLOT("CLUSTER", "at0041", "Structured name", "The name in its parts.",
                         [CKM_SLOT("structured_name")]),
                    E("at0042", "Period of use", "The period in which the name was or is in use.",
                      [DV("DV_INTERVAL<DV_DATE>")], comment="Corresponds to FHIR HumanName.period."))])])],
              occ=(0, STAR),
              comment="The name of the PARTY_IDENTITY is its purpose: the use of the name. The codes match FHIR NameUse."),
            C("PARTY_IDENTITY", "at0043", "Pseudonym",
              "A designation by which the person is known in place of a name.", [
                A("details", [C("ITEM_TREE", "at0044", "Pseudonym details", "The pseudonym.", [ITEMS(
                    E("at0045", "Pseudonym",
                      "A designation that does not by itself identify the person, such as a patient number or a randomly assigned label.",
                      [DV("DV_TEXT")], occ=(1, 1)))])])],
              occ=(0, STAR),
              comment="For a person whose name is held elsewhere, for example where the identity is kept apart from the health record.")],
          card=(1, STAR, False, False)),
        A("contacts", [postal_and_electronic_contact(
            "at0046", "A group of addresses at which the person can be reached for one purpose, with the period in which they are valid.",
            _contact_use(),
            "The name of the CONTACT is its purpose. The codes match FHIR AddressUse and ContactPointUse; the CONTACT's time_validity is the period of use.",
            ("at0052", "at0053", "at0054"), ("at0055", "at0056", "at0057"))],
          existence=(0, 1)),
        A("relationships", [SLOT("PARTY_RELATIONSHIP", "at0058", "Relationship",
                                 "A relationship the person holds to another party.",
                                 [REL % "care_relationship", REL % "party_membership",
                                  REL % "role_assignment", REL % "acting_on_behalf"], occ=(0, STAR))],
          existence=(0, 1)),
        A("languages", [DV("DV_TEXT")], existence=(0, 1), card=(0, STAR, True, False)),
    ])


PERSON = archetype("openEHR-DEMOGRAPHIC-PERSON.generic_person.v1", "bed1d1ae-9a34-44ef-818d-cdea610c0d64", _person, {
    "purpose": "To record a person as a party in a demographic service: the person's identifiers, names, birth and death, administrative gender and contacts, and the relationships the person holds to other parties.",
    "use": "Use for any person a demographic service holds: a patient, a care provider, a contact person. The archetype carries no role: a template selects what a use needs, such as a patient record that names no one, a patient's identity, or a care provider. Names are PARTY_IDENTITYs; identifiers issued for the person go in details. A person's relationships to care providers, care teams, organisations and roles are PARTY_RELATIONSHIP archetypes in the relationships slot.",
    "misuse": "Not for clinical observations about the person, such as sex, gender identity, ethnicity or occupation: record those in the health record. Not for an organisation, a group or a device: use ORGANISATION, GROUP or AGENT archetypes.",
    "keywords": ["person", "patient", "care provider", "name", "identifier", "date of birth", "gender", "contact", "demographics"],
    "references": "Structure derived from %s. Names, addresses, telecom and contact persons use the published CKM clusters openEHR-EHR-CLUSTER.structured_name.v1, address.v1, electronic_communication.v1 and person.v1. Aligned with %s." % (CKM_V0, fhir("resources Patient, Practitioner and RelatedPerson")),
})


# ---------------------------------------------------------------- ROLE

def _role():
    return C("ROLE", "at0000", "Role",
             "A function that actors perform, such as care provider, patient or administrator, with the capabilities that come with it.", [
        A("details", [C("ITEM_TREE", "at0001", "Details", "Data about the role.", [ITEMS(
            E("at0002", "Role code", "A code or name for the function.", [DV("DV_TEXT")], occ=(0, STAR),
              comment="Coding is preferred, for example with the FHIR practitioner-role codes, a SNOMED CT occupation or a local code. Corresponds to FHIR PractitionerRole.code."),
            E("at0003", "Specialty", "A specialty within the function.", [DV("DV_TEXT")], occ=(0, STAR),
              comment="Corresponds to FHIR PractitionerRole.specialty."),
            E("at0004", "Description", "A description of the function.", [DV("DV_TEXT")]),
            E("at0005", "Identifier", "An identifier of the role, such as its code in another system.",
              [DV("DV_IDENTIFIER")], occ=(0, STAR)),
            E("at0006", "Active", "Whether the role is in use.", [DV("DV_BOOLEAN")],
              comment="Corresponds to FHIR PractitionerRole.active. The period of validity is the ROLE's time_validity."),
            SLOT("CLUSTER", "at0007", "Additional details", "Further details about the role that a particular use needs.",
                 [ANY_CLUSTER], occ=(0, STAR)))])], existence=(0, 1)),
        A("identities", [C("PARTY_IDENTITY", "at0008", "Role name", "The name by which the role is known.", [
            A("details", [C("ITEM_TREE", "at0009", "Name details", "The name.", [ITEMS(
                E("at0010", "Name", "The name of the role, as it is displayed.", [DV("DV_TEXT")], occ=(1, 1)))])])],
            occ=(1, STAR))], card=(1, STAR, False, False)),
        A("capabilities", [C("CAPABILITY", "at0011", "Capability",
                             "Something an actor in the role is permitted or able to do.", [
            A("credentials", [C("ITEM_TREE", "at0012", "Credentials", "What the capability grants and requires.", [ITEMS(
                E("at0013", "Permission", "A permission the capability grants, such as an access scope.",
                  [DV("DV_TEXT")], occ=(0, STAR),
                  comment="For example a SMART on openEHR scope, or a local permission code."),
                E("at0014", "Required qualification", "A qualification an actor needs to exercise the capability.",
                  [DV("DV_TEXT")], occ=(0, STAR)),
                E("at0015", "Description", "A description of the capability.", [DV("DV_TEXT")]))])])],
            occ=(0, STAR),
            comment="The name of the CAPABILITY is the capability. Its time_validity is the period in which it holds.")],
          existence=(0, 1)),
        A("contacts", [electronic_contact("at0016", "at0017", "at0018", "at0019")], existence=(0, 1)),
    ])


ROLE = archetype("openEHR-DEMOGRAPHIC-ROLE.generic_role.v1", "0bc0d565-be8b-4093-abcd-8af2a3e60e36", _role, {
    "purpose": "To record a function that actors perform, such as care provider, patient or administrator, with the capabilities it brings and the period in which it holds.",
    "use": "Use for a role in a demographic service. A role may be held by one actor, named in its performer, or be shared: a service may keep one ROLE per function and record who holds it as a role assignment relationship from the actor. Capabilities name what the role permits, such as access scopes, and what it requires.",
    "misuse": "Not for a person's own qualifications or registrations: record those on the PERSON. Not for the relationship between a patient and a care provider: use a care relationship.",
    "keywords": ["role", "function", "capability", "permission", "practitioner role", "demographics"],
    "references": "Derived from the CKM drafts openEHR-DEMOGRAPHIC-ROLE.individual_provider.v0 and CAPABILITY.individual_credentials.v0. Aligned with %s." % fhir("resource PractitionerRole"),
})


# ---------------------------------------------------------------- AGENT

def _agent():
    return C("AGENT", "at0000", "Agent",
             "A non-human actor, such as a software application, a device or a service, that takes part in care or in the exchange of records.", [
        A("details", [C("ITEM_TREE", "at0001", "Details", "Data about the agent.", [ITEMS(
            E("at0002", "Identifier",
              "An identifier of the agent, such as a client id, a serial number or a unique device identifier.",
              [DV("DV_IDENTIFIER")], occ=(0, STAR), comment="Corresponds to FHIR Device.identifier."),
            E("at0003", "Agent type", "The kind of agent.",
              [CODED(("at0004", "Software application", "A program that acts, such as a clinical application or an integration engine."),
                     ("at0005", "Device", "A physical device, such as a medical device or a monitor."),
                     ("at0006", "Service", "A service that acts on its own, such as a scheduled job or a remote system.")),
               DV("DV_TEXT")], comment="Corresponds to FHIR Device.type."),
            E("at0007", "Description", "A description of the agent.", [DV("DV_TEXT")]),
            E("at0008", "Manufacturer", "The organisation that makes or publishes the agent.", [DV("DV_TEXT")],
              comment="Corresponds to FHIR Device.manufacturer."),
            E("at0009", "Model", "The model or product name.", [DV("DV_TEXT")],
              comment="Corresponds to FHIR Device.modelNumber."),
            E("at0010", "Version", "A version of the agent or of one of its components.", [DV("DV_TEXT")],
              occ=(0, STAR), comment="Corresponds to FHIR Device.version."),
            E("at0011", "Status", "Whether the agent is in use.",
              [CODED(("at0012", "Active", "The agent is in use. FHIR FHIRDeviceStatus code active."),
                     ("at0013", "Inactive", "The agent is not in use. FHIR FHIRDeviceStatus code inactive."),
                     ("at0014", "Entered in error", "The agent was recorded in error. FHIR FHIRDeviceStatus code entered-in-error."),
                     ("at0015", "Unknown", "It is not known whether the agent is in use. FHIR FHIRDeviceStatus code unknown."))],
              comment="The codes match FHIR R4 FHIRDeviceStatus."),
            SLOT("CLUSTER", "at0016", "Device details", "Details of the medical device, when the agent is one.",
                 [CKM_SLOT("device")]),
            SLOT("CLUSTER", "at0017", "Additional details", "Further details about the agent that a particular use needs.",
                 [ANY_CLUSTER], occ=(0, STAR)))])], existence=(0, 1)),
        A("identities", [C("PARTY_IDENTITY", "at0018", "Agent name", "A name by which the agent is known.", [
            A("name", [CODED(
                ("at0019", "User-friendly name", "The name users know the agent by. FHIR DeviceNameType code user-friendly-name."),
                ("at0020", "Manufacturer name", "The name the manufacturer gives the agent. FHIR DeviceNameType code manufacturer-name."),
                ("at0021", "Model name", "The name of the model. FHIR DeviceNameType code model-name."),
                ("at0022", "Other", "Another kind of name. FHIR DeviceNameType code other.")),
                DV("DV_TEXT")]),
            A("details", [C("ITEM_TREE", "at0023", "Name details", "The name.", [ITEMS(
                E("at0024", "Name", "The name of the agent, as it is displayed.", [DV("DV_TEXT")], occ=(1, 1)))])])],
            occ=(1, STAR), comment="The name of the PARTY_IDENTITY is the kind of name. The codes match FHIR R4 DeviceNameType.")],
          card=(1, STAR, False, False)),
        A("contacts", [electronic_contact("at0025", "at0026", "at0027", "at0028")], existence=(0, 1)),
        A("relationships", [SLOT("PARTY_RELATIONSHIP", "at0029", "Relationship",
                                 "A relationship the agent holds to another party.",
                                 [REL % "acting_on_behalf", REL % "party_membership", REL % "role_assignment"],
                                 occ=(0, STAR))], existence=(0, 1)),
    ])


AGENT = archetype("openEHR-DEMOGRAPHIC-AGENT.generic_agent.v1", "a34ba558-6111-48f0-b29e-60625ceb908b", _agent, {
    "purpose": "To record a non-human actor, such as a software application, a device or a service, as a party in a demographic service.",
    "use": "Use for an actor that is not a person, an organisation or a group: an application that commits records, a device that records data, a service that exchanges records. Record the organisation the agent acts for as an acting on behalf relationship. For a medical device, add the CKM Medical device cluster.",
    "misuse": "Not for a person who uses a device or an application. Not for a device as clinical content about a patient, such as an implant: use the CKM Medical device cluster in the health record.",
    "keywords": ["agent", "software", "application", "device", "system", "service", "demographics"],
    "references": "Aligned with %s and the published CKM cluster openEHR-EHR-CLUSTER.device.v1." % fhir("resource Device"),
})


# ---------------------------------------------------------------- GROUP: care team

def _care_team():
    return C("GROUP", "at0000", "Care team",
             "A group of care providers, and possibly others, who plan and coordinate the care of one or more patients.", [
        A("details", [C("ITEM_TREE", "at0001", "Details", "Data about the care team.", [ITEMS(
            E("at0002", "Identifier", "An identifier of the care team.", [DV("DV_IDENTIFIER")], occ=(0, STAR),
              comment="Corresponds to FHIR CareTeam.identifier."),
            E("at0003", "Status", "The state of the care team.",
              [CODED(("at0004", "Proposed", "The team is planned but not yet active. FHIR CareTeamStatus code proposed."),
                     ("at0005", "Active", "The team is active. FHIR CareTeamStatus code active."),
                     ("at0006", "Suspended", "The team is paused. FHIR CareTeamStatus code suspended."),
                     ("at0007", "Inactive", "The team no longer acts. FHIR CareTeamStatus code inactive."),
                     ("at0008", "Entered in error", "The team was recorded in error. FHIR CareTeamStatus code entered-in-error."))],
              comment="The codes match FHIR R4 CareTeamStatus."),
            E("at0009", "Category", "The kind of care team.",
              [CODED(("at0010", "Event-focused care team", "A team for one event, such as a procedure."),
                     ("at0011", "Encounter-focused care team", "A team for one encounter."),
                     ("at0012", "Episode of care-focused care team", "A team for an episode of care."),
                     ("at0013", "Condition-focused care team", "A team for a condition, such as a chronic disease."),
                     ("at0014", "Longitudinal care-coordination focused care team", "A team that coordinates care over time."),
                     ("at0015", "Home and community based services (HCBS)-focused care team", "A team for home and community based services."),
                     ("at0016", "Clinical research-focused care team", "A team for a clinical research study."),
                     ("at0017", "Public health-focused care team", "A team for a public health purpose.")),
               DV("DV_TEXT")], occ=(0, STAR),
              comment="The codes are those of the FHIR R4 care-team-category value set, bound to LOINC."),
            E("at0018", "Period", "The period in which the team is or was active.", [DV("DV_INTERVAL<DV_DATE_TIME>")],
              comment="Corresponds to FHIR CareTeam.period."),
            E("at0019", "Reason", "Why the team exists, such as the condition it addresses.", [DV("DV_TEXT")],
              occ=(0, STAR), comment="Corresponds to FHIR CareTeam.reasonCode."),
            E("at0020", "Comment", "A note about the team.", [DV("DV_TEXT")], occ=(0, STAR),
              comment="Corresponds to FHIR CareTeam.note."),
            SLOT("CLUSTER", "at0021", "Additional details", "Further details about the team that a particular use needs.",
                 [ANY_CLUSTER], occ=(0, STAR)))])], existence=(0, 1)),
        A("identities", [C("PARTY_IDENTITY", "at0022", "Team name", "The name by which the team is known.", [
            A("details", [C("ITEM_TREE", "at0023", "Name details", "The name.", [ITEMS(
                E("at0024", "Name", "The name of the team, as it is displayed.", [DV("DV_TEXT")], occ=(1, 1)))])])],
            occ=(1, STAR))], card=(1, STAR, False, False)),
        A("contacts", [electronic_contact("at0025", "at0026", "at0027", "at0028")], existence=(0, 1)),
        A("relationships", [SLOT("PARTY_RELATIONSHIP", "at0029", "Relationship",
                                 "The team's membership of an organisation, such as the organisation that manages it.",
                                 [REL % "party_membership"], occ=(0, STAR),
                                 comment="Corresponds to FHIR CareTeam.managingOrganization. Members are not listed here: a member records its membership of the team as a relationship of its own.")],
          existence=(0, 1)),
    ])


CARE_TEAM = archetype("openEHR-DEMOGRAPHIC-GROUP.care_team.v1", "348477f1-b9d4-49e9-b7e1-81d144e12368", _care_team, {
    "purpose": "To record a care team: a group of care providers, and possibly others, who plan and coordinate the care of one or more patients.",
    "use": "Use for a care team as a party in a demographic service. The team's members and patients are not listed in the team: each member records a membership relationship to the team, and each patient a care relationship to it, so the team is the target of both.",
    "misuse": "Not for an organisation with a legal or administrative standing: use an ORGANISATION. Not for a household or another informal group of persons who are not organised around care.",
    "keywords": ["care team", "team", "group", "multidisciplinary team", "demographics"],
    "references": "Aligned with %s; the categories are its care-team-category codes, bound to LOINC." % fhir("resource CareTeam"),
}, bindings={"LOINC": {"at0010": "LA27975-4", "at0011": "LA27976-2", "at0012": "LA27977-0", "at0013": "LA27978-8",
                       "at0014": "LA28865-6", "at0015": "LA28866-4", "at0016": "LA27980-4", "at0017": "LA28867-2"}})


# ---------------------------------------------------------------- ORGANISATION

def _organisation():
    return C("ORGANISATION", "at0000", "Organisation",
             "An organisation with a legal or administrative standing, such as a hospital, a practice, a department of either, an insurer or a public body.", [
        A("details", [C("ITEM_TREE", "at0001", "Details", "Data about the organisation other than names and contacts.", [ITEMS(
            E("at0002", "Identifier",
              "An identifier issued for the organisation, such as a national provider register number, a chamber of commerce number or a tax number.",
              [DV("DV_IDENTIFIER")], occ=(0, STAR),
              comment="Record the kind of identifier in type (for example HL7 v2 table 0203 code XX, organisation identifier), the authority whose scheme it belongs to in issuer, and the organisation that assigned it in assigner. Corresponds to FHIR Organization.identifier."),
            E("at0003", "Organisation type", "The kind of organisation.",
              [CODED(("at0004", "Healthcare provider", "An organisation that provides healthcare services. FHIR organization-type code prov."),
                     ("at0005", "Hospital department", "A department or ward within a hospital. FHIR organization-type code dept."),
                     ("at0006", "Organisational team", "A team of practitioners that performs a specific function within an organisation. FHIR organization-type code team."),
                     ("at0007", "Government", "A political body, such as a national, a regional or a local government. FHIR organization-type code govt."),
                     ("at0008", "Insurance company", "A company that provides insurance, which may include healthcare. FHIR organization-type code ins."),
                     ("at0009", "Payer", "An organisation that processes claims or pays providers on behalf of patients. FHIR organization-type code pay."),
                     ("at0010", "Educational institute", "An institution that provides education or research facilities. FHIR organization-type code edu."),
                     ("at0011", "Religious institution", "An organisation that is part of a religious institution. FHIR organization-type code reli."),
                     ("at0012", "Clinical research sponsor", "A pharmaceutical or clinical research sponsor. FHIR organization-type code crs."),
                     ("at0013", "Community group", "An unincorporated community group. FHIR organization-type code cg."),
                     ("at0014", "Non-healthcare business or corporation", "A registered business or corporation not of another type. FHIR organization-type code bus."),
                     ("at0015", "Other", "Another kind of organisation. FHIR organization-type code other.")),
               DV("DV_TEXT")], occ=(0, STAR),
              comment="The codes match the FHIR R4 organization-type value set. Corresponds to FHIR Organization.type."),
            E("at0016", "Active", "Whether the organisation's record is in use.", [DV("DV_BOOLEAN")],
              comment="Corresponds to FHIR Organization.active."),
            E("at0017", "Description", "A description of the organisation and what it does.", [DV("DV_TEXT")]),
            SLOT("CLUSTER", "at0018", "Contact person",
                 "A person to contact at the organisation, such as for billing or for administration.",
                 [CKM_SLOT("person")], occ=(0, STAR),
                 comment="Record the purpose of the contact in the cluster's Role element, for example with the FHIR contactentity-type codes (BILL, ADMIN, HR, PAYOR, PATINF, PRESS). Corresponds to FHIR Organization.contact."),
            SLOT("CLUSTER", "at0019", "Additional details",
                 "Further details about the organisation that a particular use needs.",
                 [ANY_CLUSTER], occ=(0, STAR)))])], existence=(0, 1)),
        A("identities", [C("PARTY_IDENTITY", "at0020", "Organisation name", "A name by which the organisation is known.", [
            A("name", [CODED(
                ("at0021", "Enterprise name", "The complete name of the organisation, usually the same as its registered name. Corresponds to FHIR Organization.name."),
                ("at0022", "Business name", "A name used for trading. Corresponds to FHIR Organization.alias."),
                ("at0023", "Locally used name", "A name the organisation is known by locally, other than its registered or business name. Corresponds to FHIR Organization.alias."),
                ("at0024", "Abbreviated name", "A short or abbreviated name. Corresponds to FHIR Organization.alias."),
                ("at0025", "Organisational unit/section/division name", "The name of a unit, a section or a division that has an identity of its own within the organisation."),
                ("at0026", "Service location name", "A name of which the location of a service is an important part, such as a mobile unit at a named site."),
                ("at0027", "Other", "A name that is none of the kinds above."),
                ("at0028", "Unknown", "A name of an unknown kind.")),
                DV("DV_TEXT")]),
            A("details", [C("ITEM_TREE", "at0029", "Name details", "The name.", [ITEMS(
                E("at0030", "Name", "The name of the organisation, as it is displayed.", [DV("DV_TEXT")], occ=(1, 1)))])])],
            occ=(1, STAR),
            comment="The name of the PARTY_IDENTITY is the kind of name. The kinds are those of the CKM draft openEHR-DEMOGRAPHIC-PARTY_IDENTITY.organisation_name.v0, from ISO/DTS 27527 provider identification.")],
          card=(1, STAR, False, False)),
        A("contacts", [postal_and_electronic_contact(
            "at0031", "A group of addresses at which the organisation can be reached for one purpose, with the period in which they are valid.",
            [CODED(("at0032", "Work", "The addresses at which the organisation works and can be reached. Corresponds to FHIR use work."),
                   ("at0033", "Temporary", "Addresses in use for a limited period. Corresponds to FHIR use temp."),
                   ("at0034", "Old", "Addresses that are no longer in use. Corresponds to FHIR use old."),
                   ("at0035", "Billing", "Addresses for invoices and payment. Corresponds to FHIR AddressUse billing."))],
            "The name of the CONTACT is its purpose. The codes match FHIR AddressUse and ContactPointUse, without home, which FHIR does not allow for an organisation; the CONTACT's time_validity is the period of use. Corresponds to FHIR Organization.address and Organization.telecom.",
            ("at0036", "at0037", "at0038"), ("at0039", "at0040", "at0041"))],
          existence=(0, 1)),
        A("relationships", [SLOT("PARTY_RELATIONSHIP", "at0042", "Relationship",
                                 "A relationship the organisation holds to another party, such as the organisation it is part of.",
                                 [REL % "part_of", REL % "party_membership", REL % "role_assignment"], occ=(0, STAR),
                                 comment="An organisation records the organisation it is part of, not its parts: a department holds its relationship to its hospital.")],
          existence=(0, 1)),
    ])


ORGANISATION = archetype("openEHR-DEMOGRAPHIC-ORGANISATION.generic_organisation.v1", "f98a21dc-0e98-427c-a5fc-a8512dd98e66", _organisation, {
    "purpose": "To record an organisation as a party in a demographic service: its identifiers, names, type, contacts and contact persons, and the relationships it holds to other parties, such as the organisation it is part of.",
    "use": "Use for any organisation with a legal or administrative standing that a demographic service holds: a hospital, a practice, a department or a ward, a laboratory, an insurer, a public body. Names are PARTY_IDENTITYs named by their kind; identifiers go in details. A part of an organisation records the organisation it is part of as a part of relationship, so a hierarchy is read from its smallest parts upwards.",
    "misuse": "Not for an informal or functional group of parties, such as a care team or a household: use a GROUP. Not for the location where care takes place, such as a room or a bed. Not for an organisation mentioned in clinical content: use the CKM Organisation cluster in the health record.",
    "keywords": ["organisation", "organization", "healthcare provider", "hospital", "department", "practice", "insurer", "demographics"],
    "references": "Structure derived from the openEHR CKM demographic drafts openEHR-DEMOGRAPHIC-ORGANISATION.organisation.v0 and PARTY_IDENTITY.organisation_name.v0, after ISO/DTS 27527:2007 Provider Identification. Addresses, telecom and contact persons use the published CKM clusters openEHR-EHR-CLUSTER.address.v1, electronic_communication.v1 and person.v1. Aligned with %s." % fhir("resource Organization"),
})


# ---------------------------------------------------------------- GROUP: generic

def _group():
    return C("GROUP", "at0000", "Group",
             "A group of parties that is formed for a purpose but has no legal or administrative standing of its own, such as a household, a patient cohort or a team.", [
        A("details", [C("ITEM_TREE", "at0001", "Details", "Data about the group.", [ITEMS(
            E("at0002", "Identifier", "An identifier of the group.", [DV("DV_IDENTIFIER")], occ=(0, STAR),
              comment="Corresponds to FHIR Group.identifier."),
            E("at0003", "Member type", "The kind of party the members of the group are.",
              [CODED(("at0004", "Person", "The members are persons, such as patients or relatives. FHIR GroupType code person."),
                     ("at0005", "Practitioner", "The members are care providers. FHIR GroupType code practitioner."),
                     ("at0006", "Device", "The members are devices or other agents. FHIR GroupType code device.")),
               DV("DV_TEXT")],
              comment="The codes are those of FHIR R4 GroupType whose members can be parties; animal, medication and substance are not. Record a group of mixed kinds as text. Corresponds to FHIR Group.type."),
            E("at0007", "Kind of group", "What the group is, such as a household, a ward team or a study cohort.",
              [DV("DV_TEXT")], comment="Coding is preferred, for example with SNOMED CT. Corresponds to FHIR Group.code."),
            E("at0008", "Actual", "Whether the group stands for particular parties (true) or describes by its characteristics the parties that may belong to it (false).",
              [DV("DV_BOOLEAN")], comment="Corresponds to FHIR Group.actual. Members of an actual group record their membership of it themselves."),
            E("at0009", "Active", "Whether the group's record is in use.", [DV("DV_BOOLEAN")],
              comment="Corresponds to FHIR Group.active."),
            E("at0010", "Description", "A description of the group and its purpose.", [DV("DV_TEXT")]),
            E("at0011", "Number of members", "How many members the group has, or had when this was recorded.",
              [DV("DV_COUNT")], comment="Corresponds to FHIR Group.quantity."),
            C("CLUSTER", "at0012", "Characteristic",
              "A trait that the members of the group share, or that no member has.", [
                  ITEMS(
                      E("at0013", "Characteristic", "The trait, such as an age band, a diagnosis or a place of residence.",
                        [DV("DV_TEXT")], occ=(1, 1), comment="Coding is preferred. Corresponds to FHIR Group.characteristic.code."),
                      E("at0014", "Value", "The value the members have for the trait.",
                        [DV("DV_TEXT"), DV("DV_BOOLEAN"), DV("DV_QUANTITY"), DV("DV_INTERVAL<DV_QUANTITY>")], occ=(1, 1),
                        comment="Corresponds to FHIR Group.characteristic.value[x], whose CodeableConcept is text here and whose Range is an interval of quantities."),
                      E("at0015", "Exclude", "Whether the group holds the parties that do not have the trait (true) rather than those that do (false).",
                        [DV("DV_BOOLEAN")], comment="Corresponds to FHIR Group.characteristic.exclude."),
                      E("at0016", "Period", "The period in which the trait applies.", [DV("DV_INTERVAL<DV_DATE_TIME>")],
                        comment="Corresponds to FHIR Group.characteristic.period."))],
              occ=(0, STAR), comment="Corresponds to FHIR Group.characteristic."),
            SLOT("CLUSTER", "at0017", "Additional details", "Further details about the group that a particular use needs.",
                 [ANY_CLUSTER], occ=(0, STAR)))])], existence=(0, 1)),
        A("identities", [C("PARTY_IDENTITY", "at0018", "Group name", "A name by which the group is known.", [
            A("details", [C("ITEM_TREE", "at0019", "Name details", "The name.", [ITEMS(
                E("at0020", "Name", "The name of the group, as it is displayed.", [DV("DV_TEXT")], occ=(1, 1)))])])],
            occ=(1, STAR), comment="Corresponds to FHIR Group.name.")], card=(1, STAR, False, False)),
        A("contacts", [electronic_contact("at0021", "at0022", "at0023", "at0024")], existence=(0, 1)),
        A("relationships", [SLOT("PARTY_RELATIONSHIP", "at0025", "Relationship",
                                 "The group's membership of an organisation or of another group, such as the organisation that manages it.",
                                 [REL % "party_membership"], occ=(0, STAR),
                                 comment="Corresponds to FHIR Group.managingEntity, where that is an organisation. Members are not listed here: a member records its membership of the group as a relationship of its own.")],
          existence=(0, 1)),
    ])


GROUP = archetype("openEHR-DEMOGRAPHIC-GROUP.generic_group.v1", "8db8d241-5add-4a8a-910f-d0ceb494fbbc", _group, {
    "purpose": "To record a group of parties as a party in a demographic service: its names, identifiers, the kind of members it has, the traits they share and its electronic contacts.",
    "use": "Use for a group that has no legal or administrative standing of its own: a household, a patient cohort, a team that is not a care team, a group of devices. The group's members are not listed in the group: each member records a membership relationship to it, so the group is the target. A group may instead describe its members by the traits they share, without listing any.",
    "misuse": "Not for an organisation or a department with a legal or administrative standing: use an ORGANISATION. Not for a care team: use the care team archetype.",
    "keywords": ["group", "household", "cohort", "team", "members", "demographics"],
    "references": "Aligned with %s." % fhir("resource Group"),
})


# ---------------------------------------------------------------- PARTY_RELATIONSHIPs

def _relationship(text, description, details, targets):
    def build():
        return C("PARTY_RELATIONSHIP", "at0000", text, description, [
            A("details", [C("ITEM_TREE", "at0001", "Details", "Data about the relationship.", [ITEMS(*details())])],
              existence=(0, 1)),
            A("target", [PARTY_REF(*targets)]),
        ])
    return build


def _care_details():
    return [
        E("at0002", "Care relationship type", "The part the target plays in the source party's care.",
          [CODED(("at0003", "Primary care provider", "The target is the source party's primary care provider, such as a general practitioner. Corresponds to FHIR Patient.generalPractitioner."),
                 ("at0004", "Responsible care provider", "The target is responsible for the source party's care."),
                 ("at0005", "Care team", "The target is a care team that cares for the source party. Corresponds to FHIR CareTeam.subject."),
                 ("at0006", "Case manager", "The target coordinates the source party's care across providers."),
                 ("at0007", "Managing organisation", "The target is the organisation that manages the source party's care and record. Corresponds to FHIR Patient.managingOrganization.")),
           DV("DV_TEXT")]),
        E("at0008", "Reason", "Why the care relationship exists, such as the condition or the referral it follows.",
          [DV("DV_TEXT")], occ=(0, STAR)),
        E("at0009", "Comment", "A note about the relationship.", [DV("DV_TEXT")]),
    ]


def _membership_details():
    return [
        E("at0002", "Member role", "The part the member plays in the group or organisation.", [DV("DV_TEXT")],
          occ=(0, STAR), comment="Coding is preferred, for example with SNOMED CT. Corresponds to FHIR CareTeam.participant.role."),
        E("at0003", "Comment", "A note about the membership.", [DV("DV_TEXT")]),
    ]


def _assignment_details():
    return [
        E("at0002", "Specialty", "The specialty in which the actor holds the role.", [DV("DV_TEXT")], occ=(0, STAR),
          comment="Corresponds to FHIR PractitionerRole.specialty."),
        E("at0003", "Comment", "A note about the assignment.", [DV("DV_TEXT")]),
    ]


def _behalf_details():
    return [
        E("at0002", "Basis", "What the authority to act rests on, such as a contract, a mandate or a legal guardianship.",
          [DV("DV_TEXT")]),
        E("at0003", "Comment", "A note about the relationship.", [DV("DV_TEXT")]),
    ]


_REL_USE = ("The relationship is held by its source party and versioned with it; its time_validity is the period in "
            "which it is active. The archetype id is the relationship's type.")

CARE_RELATIONSHIP = archetype(
    "openEHR-DEMOGRAPHIC-PARTY_RELATIONSHIP.care_relationship.v1", "c6b91a62-edd9-4921-b3da-f8f3a639873a",
    _relationship("Care relationship",
                  "The source party, usually a patient, is in the care of the target party: a care provider, a care team or an organisation.",
                  _care_details, ["PERSON", "GROUP", "ORGANISATION"]), {
        "purpose": "To record that a patient is in the care of a care provider, a care team or an organisation, and in which part.",
        "use": "Use in the patient's party, with the patient as source. " + _REL_USE + " Read from the target, the care relationships are a care provider's or a team's patients.",
        "misuse": "Not for a family or social relationship between persons. Not for a care provider's membership of a team: use a membership.",
        "keywords": ["care relationship", "caseload", "care team", "general practitioner", "patient"],
        "references": "Derived from the provider relationship of the CKM draft openEHR-DEMOGRAPHIC-PERSON.person-patient.v0. Aligned with %s." % fhir("elements Patient.generalPractitioner and Patient.managingOrganization and the resource CareTeam"),
    })

PARTY_MEMBERSHIP = archetype(
    "openEHR-DEMOGRAPHIC-PARTY_RELATIONSHIP.party_membership.v1", "6b5f2560-99b0-43f2-af31-7a22ae17c0f8",
    _relationship("Membership", "The source party is a member of the target party: a group, such as a care team, or an organisation.",
                  _membership_details, ["GROUP", "ORGANISATION"]), {
        "purpose": "To record that a party is a member of a group, such as a care team, or of an organisation, and in which part.",
        "use": "Use in the member's party, with the member as source. " + _REL_USE,
        "misuse": "Not for a patient in the care of a team: use a care relationship. Not for holding a role: use a role assignment.",
        "keywords": ["membership", "member", "care team", "employment", "affiliation"],
        "references": "Derived from the employment relationship of the CKM draft openEHR-DEMOGRAPHIC-ROLE.individual_provider.v0. Aligned with %s." % fhir("elements CareTeam.participant and PractitionerRole.organization"),
    })

ROLE_ASSIGNMENT = archetype(
    "openEHR-DEMOGRAPHIC-PARTY_RELATIONSHIP.role_assignment.v1", "c37cec06-3a25-4b3a-b811-3a7ed9ccdbd4",
    _relationship("Role assignment", "The source actor holds the target role.", _assignment_details, ["ROLE"]), {
        "purpose": "To record that an actor holds a role, such as care provider or patient, for a period.",
        "use": "Use in the actor's party, with the actor as source and a ROLE as target, where a service keeps one ROLE per function and records who holds it. " + _REL_USE,
        "misuse": "Not where each ROLE names its own performer: the ROLE's performer already says who holds it.",
        "keywords": ["role assignment", "role", "function", "practitioner role"],
        "references": "Aligned with %s." % fhir("resource PractitionerRole: its practitioner, code, specialty and period"),
    })

ACTING_ON_BEHALF = archetype(
    "openEHR-DEMOGRAPHIC-PARTY_RELATIONSHIP.acting_on_behalf.v1", "7069d50e-a169-473c-bbb4-023328060063",
    _relationship("Acting on behalf",
                  "The source actor acts on behalf of the target party, such as an agent operated by an organisation, or a person who represents another.",
                  _behalf_details, ["ORGANISATION", "PERSON", "GROUP"]), {
        "purpose": "To record that an actor acts on behalf of another party, and on what authority.",
        "use": "Use in the acting party, with the actor as source: a software agent and the organisation that operates it, a representative and the person represented. " + _REL_USE,
        "misuse": "Not for membership of a group or an organisation: use a membership.",
        "keywords": ["acting on behalf", "agent", "owner", "representative", "mandate", "guardian"],
        "references": "Aligned with %s." % fhir("elements Device.owner and Provenance.agent.onBehalfOf"),
    })

PART_OF = archetype(
    "openEHR-DEMOGRAPHIC-PARTY_RELATIONSHIP.part_of.v1", "3ea6edd4-fa71-4022-ad2e-8c2216d19c6e",
    _relationship("Part of",
                  "The source organisation is a part of the target organisation, such as a ward of a hospital or a subsidiary of a company.",
                  lambda: [E("at0002", "Comment", "A note about the relationship.", [DV("DV_TEXT")])],
                  ["ORGANISATION"]), {
        "purpose": "To record that an organisation is a part of another, such as a department of a hospital, a ward of a department or a subsidiary of a company.",
        "use": "Use in the part's party, with the part as source and the organisation it belongs to as target, so each part names its parent and the hierarchy is read upwards. " + _REL_USE,
        "misuse": "Not for membership of an organisation by a person, a group or an agent: use a membership. Not for a contract or an affiliation between independent organisations: use a membership of a group that stands for the network.",
        "keywords": ["part of", "hierarchy", "department", "subsidiary", "parent organisation"],
        "references": "Derived from the relationship between an organisation and its divisions in the CKM draft openEHR-DEMOGRAPHIC-ORGANISATION.organisation.v0. Aligned with %s." % fhir("element Organization.partOf"),
    })

LOCAL = [EHR_STATUS, FOLDER, PERSON, ROLE, AGENT, CARE_TEAM, ORGANISATION, GROUP,
         CARE_RELATIONSHIP, PARTY_MEMBERSHIP, ROLE_ASSIGNMENT, ACTING_ON_BEHALF, PART_OF]


# ---------------------------------------------------------------- templates

def _fill_name(t, base):
    fill(t, base + "/details[at0039]/items[at0041]", CKM["structured_name"])


def _fill_contacts(t, base="/contacts[at0046]", postal=("at0052", "at0053", "at0054"),
                   electronic=("at0055", "at0056", "at0057")):
    fill(t, base + "/addresses[%s]/details[%s]/items[%s]" % postal, CKM["address"])
    fill(t, base + "/addresses[%s]/details[%s]/items[%s]" % electronic, CKM["electronic_communication"])


def _fill_contact_person(t, slot):
    fill(t, slot, CKM["person"])
    cp = slot.rsplit("[", 1)[0] + "[openEHR-EHR-CLUSTER.person.v1]/items"
    fill(t, cp + "[at0002]", CKM["structured_name"])
    fill(t, cp + "[at0005]", CKM["address"])
    fill(t, cp + "[at0006]", CKM["electronic_communication"])


def _fill_electronic(t, contact, address, tree, slot):
    fill(t, "/contacts[%s]/addresses[%s]/details[%s]/items[%s]" % (contact, address, tree, slot),
         CKM["electronic_communication"])


def generic_ehr_status():
    t = instantiate(EHR_STATUS)
    keep_open(t, *("/other_details[%s]" % s for s in ITEM_STRUCTURE_SLOTS))
    return t


def generic_folder():
    t = instantiate(FOLDER)
    keep_open(t, *("/details[%s]" % s for s in ITEM_STRUCTURE_SLOTS))
    return t


def patient():
    t = instantiate(PERSON)
    d = "/details[at0001]/items"
    existence(t, "/", "details", 1, 1)
    occurrences(t, d + "[at0002]", 1, STAR)
    date_pattern(t, d + "[at0003]", "yyyy-XX-XX")
    drop(t, d + "[at0010]", d + "[at0011]", d + "[at0022]", d + "[at0023]", d + "[at0024]",
         d + "[at0029]", d + "[at0030]")
    drop(t, "/identities[at0031]")
    occurrences(t, "/identities[at0043]", 1, 1)
    existence(t, "/", "contacts", 0, 0)
    existence(t, "/", "languages", 0, 0)
    fill(t, "/relationships[at0058]", CARE_RELATIONSHIP, ROLE_ASSIGNMENT)
    return t


def patient_identity():
    t = instantiate(PERSON)
    d = "/details[at0001]/items"
    drop(t, d + "[at0024]", d + "[at0030]")
    fill(t, d + "[at0023]", CKM["address"])
    _fill_contact_person(t, d + "[at0029]")
    drop(t, "/identities[at0043]")
    occurrences(t, "/identities[at0031]", 1, STAR)
    _fill_name(t, "/identities[at0031]")
    _fill_contacts(t)
    existence(t, "/", "relationships", 0, 0)
    return t


def care_provider():
    t = instantiate(PERSON)
    d = "/details[at0001]/items"
    drop(t, d + "[at0009]", d + "[at0010]", d + "[at0011]", d + "[at0022]", d + "[at0023]",
         d + "[at0029]", d + "[at0030]")
    drop(t, "/identities[at0043]")
    occurrences(t, "/identities[at0031]", 1, STAR)
    _fill_name(t, "/identities[at0031]")
    _fill_contacts(t)
    fill(t, "/relationships[at0058]", PARTY_MEMBERSHIP, ROLE_ASSIGNMENT)
    return t


def generic_role():
    t = instantiate(ROLE)
    drop(t, "/details[at0001]/items[at0007]")
    _fill_electronic(t, "at0016", "at0017", "at0018", "at0019")
    existence(t, "/", "relationships", 0, 0)
    return t


def generic_agent():
    t = instantiate(AGENT)
    drop(t, "/details[at0001]/items[at0017]")
    fill(t, "/details[at0001]/items[at0016]", CKM["device"])
    _fill_electronic(t, "at0025", "at0026", "at0027", "at0028")
    fill(t, "/relationships[at0029]", ACTING_ON_BEHALF, PARTY_MEMBERSHIP, ROLE_ASSIGNMENT)
    return t


def care_team():
    t = instantiate(CARE_TEAM)
    drop(t, "/details[at0001]/items[at0021]")
    _fill_electronic(t, "at0025", "at0026", "at0027", "at0028")
    existence(t, "/", "relationships", 0, 0)
    return t


def generic_organisation():
    t = instantiate(ORGANISATION)
    d = "/details[at0001]/items"
    drop(t, d + "[at0019]")
    _fill_contact_person(t, d + "[at0018]")
    _fill_contacts(t, "/contacts[at0031]", ("at0036", "at0037", "at0038"), ("at0039", "at0040", "at0041"))
    fill(t, "/relationships[at0042]", PART_OF, PARTY_MEMBERSHIP, ROLE_ASSIGNMENT)
    return t


def generic_group():
    t = instantiate(GROUP)
    drop(t, "/details[at0001]/items[at0017]")
    _fill_electronic(t, "at0021", "at0022", "at0023", "at0024")
    existence(t, "/", "relationships", 0, 0)
    return t


CKM = {}  # name -> Archetype, loaded by the build

TEMPLATES = [
    ("generic_ehr_status.v1", "70c19cf1-96fe-40ea-ae17-e7effd31896b", "Generic EHR status", generic_ehr_status, {
        "purpose": "A generic EHR status: the archetype id openEHR-EHR-EHR_STATUS.generic.v1, which CDRs give an EHR_STATUS by default, with any item structure as its other details, plain or defined by an archetype.",
        "use": "Install it on a CDR whose EHRs carry a default EHR_STATUS, to build a default one, and to validate an EHR_STATUS that names it.",
        "misuse": "Not where the other details must follow one structure: use a template that constrains them.",
        "keywords": ["EHR status", "default"],
    }),
    ("generic_folder.v1", "be12920b-8f93-4839-a0aa-2d1efbb23035", "Generic folder", generic_folder, {
        "purpose": "A generic folder: the archetype id openEHR-EHR-FOLDER.generic.v1, with any item structure as its details, plain or defined by an archetype, and any sub-folders and items.",
        "use": "Install it on a CDR whose EHRs carry folders with no structure of their own, to build a default folder, and to validate a FOLDER that names it.",
        "misuse": "Not where a folder's details must follow one structure, or its sub-folders or items have a structure of their own: use a template that constrains them.",
        "keywords": ["folder", "directory", "default"],
    }),
    ("PERSON-Patient.v1", "1c86b6b3-ea97-4c33-9846-c38f16085e54", "Patient", patient, {
        "purpose": "A patient as a party beside the EHR, the party an EHR_STATUS subject references. It names no one: it holds the patient number or a pseudonym, the year of birth, the administrative gender and whether the patient has died, and the patient's relationships to care providers, care teams, organisations and roles.",
        "use": "Use for the party that stands for a patient in the clinical domain, where who the patient is is kept apart in a PERSON-PatientIdentity.v1 party. The identifier is the patient number or the pseudonym (DV_IDENTIFIER type MR, PI or ANON); the only identity is a pseudonym. A care relationship to a care provider, a care team or an organisation puts the patient in their care; a role assignment gives the patient a shared role.",
        "misuse": "Not for names, addresses, telecom, a full date of birth or a national person number: the template has no place for them, and they belong in PERSON-PatientIdentity.v1.",
        "keywords": ["patient", "pseudonym", "EHR subject", "care relationship"],
    }),
    ("PERSON-PatientIdentity.v1", "1dad7890-0985-4bb1-837b-5f17819ef32c", "Patient identity", patient_identity, {
        "purpose": "Who a patient is: the patient's names, identifiers such as a national person number or a passport number, date of birth, administrative gender, marital status, death, addresses, telecom, languages and contact persons.",
        "use": "Use for the person that identifies a patient, kept apart from the health record and linked to the patient's PERSON-Patient.v1 party outside both. It holds no relationships. Contact persons such as next of kin are recorded inline, as FHIR Patient.contact does.",
        "misuse": "Not as the subject of an EHR where the identity is to be kept apart from the record: use PERSON-Patient.v1. Not for clinical observations about the patient.",
        "keywords": ["patient identity", "person", "name", "identifier", "address", "contact person"],
    }),
    ("PERSON-CareProvider.v1", "b842cd17-68ca-4c45-b7ba-8357e9c9ff36", "Care provider", care_provider, {
        "purpose": "A care provider as a party: the person's names, identifiers such as professional registration numbers, administrative gender, qualifications, work contacts and languages, with memberships of care teams and organisations and the roles the person holds.",
        "use": "Use for a member of staff who provides care, such as a physician, a nurse or a therapist. A membership puts the person in a care team or an organisation; a role assignment gives the person a shared function role. Patients reach the person through their own care relationships.",
        "misuse": "Not for the patient side of a care provider who is also a patient: that is a separate PERSON-Patient.v1 party.",
        "keywords": ["care provider", "practitioner", "healthcare professional", "staff", "qualification"],
    }),
    ("ROLE-generic-role.v1", "6f1cec4f-ae23-4636-a0a6-283e9b34178d", "Role", generic_role, {
        "purpose": "A function that actors perform, such as care provider, patient or administrator, with its capabilities and its contacts.",
        "use": "Use for a role in a demographic service. Where a service keeps one ROLE per function, actors hold it through a role assignment relationship of their own; the ROLE then holds no relationships.",
        "misuse": "Not for a person's qualifications or registrations: record those on the person.",
        "keywords": ["role", "function", "capability", "permission"],
    }),
    ("AGENT-generic-agent.v1", "a1fe284d-d6aa-4819-9094-f3d66f94b243", "Agent", generic_agent, {
        "purpose": "A non-human actor, such as a software application, a device or a service, with its identifiers, type, maker, versions, status, electronic contacts and the parties it acts for.",
        "use": "Use for an application, a device or a service that acts in its own name. An acting on behalf relationship names the organisation or person it acts for; a membership or a role assignment places it in a group, an organisation or a role.",
        "misuse": "Not for a person who uses an application or a device.",
        "keywords": ["agent", "software", "application", "device", "service"],
    }),
    ("GROUP-CareTeam.v1", "b0e966ee-fe40-4d8e-9421-f9895ea7a2cb", "Care team", care_team, {
        "purpose": "A care team: its names, identifiers, status, categories, period, reasons and electronic contacts.",
        "use": "Use for a care team as a party. The team holds no relationships: members record a membership of the team, and patients a care relationship to it, in their own parties.",
        "misuse": "Not for an organisation or a department with a legal or administrative standing.",
        "keywords": ["care team", "team", "group"],
    }),
    ("ORGANISATION-generic.v1", "3f7d3fce-724b-4587-b4cf-2ee2b9b5e932", "Organisation", generic_organisation, {
        "purpose": "An organisation: its names by kind, identifiers, types, whether it is active, a description, contact persons, postal and electronic contacts, and the organisation it is part of, the groups and organisations it is a member of and the roles it holds.",
        "use": "Use for a hospital, a practice, a department, a ward, a laboratory, an insurer or another organisation with a legal or administrative standing. A part names the organisation it is part of through a part of relationship of its own; a care provider, a group or an agent records its membership of the organisation in its own party, and a patient a care relationship to it.",
        "misuse": "Not for a care team, a household or another group without a legal or administrative standing: use GROUP-CareTeam.v1 or GROUP-generic.v1.",
        "keywords": ["organisation", "healthcare provider", "hospital", "department", "practice"],
    }),
    ("GROUP-generic.v1", "27bf0e9d-d46f-466b-afd0-aa2962eb3f4f", "Group", generic_group, {
        "purpose": "A group of parties: its names, identifiers, member type, kind, whether it is actual and active, a description, the number of members, the traits its members share, and its electronic contacts.",
        "use": "Use for a household, a patient cohort, a team that is not a care team, or a group of devices. The group holds no relationships: members record a membership of the group, and patients a care relationship to it, in their own parties.",
        "misuse": "Not for an organisation or a department with a legal or administrative standing: use ORGANISATION-generic.v1. Not for a care team: use GROUP-CareTeam.v1.",
        "keywords": ["group", "household", "cohort", "team"],
    }),
]
