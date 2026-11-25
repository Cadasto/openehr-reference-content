// SPDX-License-Identifier: MIT

// Package reference ships a reference set of openEHR operational templates
// (OPT 1.4, English) for the classes besides COMPOSITION whose instances name
// a template: the generic EHR_STATUS and FOLDER, and one template for each
// party a demographic service holds.
//
//   - generic_ehr_status.v1 ([EHRStatusTemplateID]) and generic_folder.v1
//     ([FolderTemplateID]): the archetype id a CDR gives an EHR_STATUS or a
//     FOLDER by default, with their details left open.
//   - PERSON-Patient.v1 ([PatientTemplateID]): the one party that stands for
//     a patient: identifiers, at least one, names and an optional pseudonym,
//     birth, gender, death, marital status, addresses, telecom, languages,
//     contact persons, care relationships and role assignments. Every element
//     leaves its value optional and accepts the null flavour masked, so a
//     service can store the party with its identifying values masked.
//   - PERSON-CareProvider.v1 ([CareProviderTemplateID]): a care provider,
//     with memberships of care teams and organisations and role assignments.
//   - ROLE-generic-role.v1 ([RoleTemplateID]): a function actors perform,
//     with its capabilities; no relationships.
//   - AGENT-generic-agent.v1 ([AgentTemplateID]): a software application, a
//     device or a service, with the parties it acts for.
//   - GROUP-CareTeam.v1 ([CareTeamTemplateID]): a care team; no
//     relationships.
//   - ORGANISATION-generic.v1 ([OrganisationTemplateID]): an organisation,
//     with the organisation it is part of, memberships and role assignments.
//   - GROUP-generic.v1 ([GroupTemplateID]): any other group, such as a
//     household or a cohort; no relationships.
//
// [OPT] returns a template's XML document and [TemplateIDs] lists the ids.
// The package depends on nothing outside the standard library: a program
// compiles a document with the openEHR SDK of its choice, for example
// github.com/cadasto/openehr-sdk-go's aom14.ReadOperationalTemplate and
// templatecompile.Compile.
//
// The archetypes the templates are built from, and the generator that writes
// both, are in the module's repository, not in the package.
//
// # Licence
//
// The templates are licensed under the Creative Commons
// Attribution-ShareAlike 4.0 International License: they embed published
// openEHR CKM archetypes, © openEHR Foundation, under the same terms. The Go
// and Python code is MIT. The repository's LICENSE, LICENSE-MIT and
// ATTRIBUTION.md files say which applies where.
//
// # Stability
//
// A server stores these templates, and the instances written against them,
// so the template under an id holds still. A template id never starts
// refusing an instance it accepted before: a change that would ships under a
// new id, such as PERSON-Patient.v2, and the module keeps the old id's
// template and constant. The CHANGELOG records any change to a document,
// under the release that ships it.
package reference
