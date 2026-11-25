// SPDX-License-Identifier: MIT

package reference

import (
	"embed"
	"io/fs"
	"path"
	"slices"
)

// The template ids of the operational templates the module ships.
const (
	// EHRStatusTemplateID is the template id of the generic EHR_STATUS
	// template.
	EHRStatusTemplateID = "generic_ehr_status.v1"
	// FolderTemplateID is the template id of the generic FOLDER template.
	FolderTemplateID = "generic_folder.v1"
	// PatientTemplateID is the template id of the patient template: the one
	// PERSON that stands for a patient.
	PatientTemplateID = "PERSON-Patient.v1"
	// CareProviderTemplateID is the template id of the care provider
	// template, a PERSON.
	CareProviderTemplateID = "PERSON-CareProvider.v1"
	// RoleTemplateID is the template id of the role template.
	RoleTemplateID = "ROLE-generic-role.v1"
	// AgentTemplateID is the template id of the agent template: a software
	// application, a device or a service.
	AgentTemplateID = "AGENT-generic-agent.v1"
	// CareTeamTemplateID is the template id of the care team template, a
	// GROUP.
	CareTeamTemplateID = "GROUP-CareTeam.v1"
	// OrganisationTemplateID is the template id of the organisation
	// template.
	OrganisationTemplateID = "ORGANISATION-generic.v1"
	// GroupTemplateID is the template id of the template of a group other
	// than a care team.
	GroupTemplateID = "GROUP-generic.v1"
)

// templates holds tech/templates/{template-id}/opt/{template-id}.opt for
// each template.
//
//go:embed tech/templates/*/opt/*.opt
var templates embed.FS

// templateIDs are the ids of the templates in the embedded tree, sorted.
var templateIDs = func() []string {
	dirs, err := fs.ReadDir(templates, "tech/templates")
	if err != nil {
		panic("reference: list the embedded templates: " + err.Error())
	}
	ids := make([]string, 0, len(dirs))
	for _, d := range dirs {
		ids = append(ids, d.Name())
	}
	slices.Sort(ids)
	return ids
}()

// TemplateIDs returns the template ids of the operational templates the
// module ships, sorted, in a new slice on each call.
func TemplateIDs() []string {
	return slices.Clone(templateIDs)
}

// OPT returns the XML document of the operational template whose template id
// is templateID, byte for byte as the module embeds it, for upload to a
// server or for compiling. Each call returns a new slice, so a caller may
// change it without changing any other result. OPT reports false for an id
// the module does not ship.
func OPT(templateID string) ([]byte, bool) {
	if _, found := slices.BinarySearch(templateIDs, templateID); !found {
		return nil, false
	}
	// embed.FS copies the file's bytes on each read.
	b, err := templates.ReadFile(path.Join("tech/templates", templateID, "opt", templateID+".opt"))
	if err != nil {
		return nil, false
	}
	return b, true
}
