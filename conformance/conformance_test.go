// SPDX-License-Identifier: MIT

// Package conformance_test checks every template the module ships with the
// openEHR SDK for Go: each reads and compiles strictly, every instance the
// SDK generates from it validates against it, each refuses what it promises
// to keep out (refusals_test.go, item_tree_test.go), the patient template
// accepts a party whose elements are masked (masked_test.go), and each
// stored example instance is current and validates (examples_test.go).
package conformance_test

import (
	"bytes"
	"errors"
	"fmt"
	"math/rand/v2"
	"sync"
	"testing"
	"time"

	reference "github.com/cadasto/openehr-reference-content"
	"github.com/cadasto/openehr-sdk-go/openehr/aom/aom14"
	"github.com/cadasto/openehr-sdk-go/openehr/instance"
	"github.com/cadasto/openehr-sdk-go/openehr/rm"
	"github.com/cadasto/openehr-sdk-go/openehr/serialize/canxml"
	"github.com/cadasto/openehr-sdk-go/openehr/templatecompile"
	"github.com/cadasto/openehr-sdk-go/openehr/validation"
)

// roots is each template's root: its RM type and archetype id.
var roots = map[string]struct{ rmType, archetypeID string }{
	reference.EHRStatusTemplateID:    {"EHR_STATUS", "openEHR-EHR-EHR_STATUS.generic.v1"},
	reference.FolderTemplateID:       {"FOLDER", "openEHR-EHR-FOLDER.generic.v1"},
	reference.PatientTemplateID:      {"PERSON", "openEHR-DEMOGRAPHIC-PERSON.generic_person.v1"},
	reference.CareProviderTemplateID: {"PERSON", "openEHR-DEMOGRAPHIC-PERSON.generic_person.v1"},
	reference.RoleTemplateID:         {"ROLE", "openEHR-DEMOGRAPHIC-ROLE.generic_role.v1"},
	reference.AgentTemplateID:        {"AGENT", "openEHR-DEMOGRAPHIC-AGENT.generic_agent.v1"},
	reference.CareTeamTemplateID:     {"GROUP", "openEHR-DEMOGRAPHIC-GROUP.care_team.v1"},
	reference.OrganisationTemplateID: {"ORGANISATION", "openEHR-DEMOGRAPHIC-ORGANISATION.generic_organisation.v1"},
	reference.GroupTemplateID:        {"GROUP", "openEHR-DEMOGRAPHIC-GROUP.generic_group.v1"},
}

// newRoot is an empty value of the RM class rmType, for
// validation.ValidateJSON to decode a document into.
func newRoot(t *testing.T, rmType string) any {
	t.Helper()
	switch rmType {
	case "EHR_STATUS":
		return &rm.EHRStatus{}
	case "FOLDER":
		return &rm.Folder{}
	case "PERSON":
		return &rm.Person{}
	case "ROLE":
		return &rm.Role{}
	case "AGENT":
		return &rm.Agent{}
	case "GROUP":
		return &rm.Group{}
	case "ORGANISATION":
		return &rm.Organisation{}
	}
	t.Fatalf("newRoot(%q): no value for this RM class: add it", rmType)
	return nil
}

func document(t *testing.T, id string) []byte {
	t.Helper()
	doc, ok := reference.OPT(id)
	if !ok {
		t.Fatalf("OPT(%q) reported false, want the document", id)
	}
	return doc
}

// readStrict reads a document as the checks below do, under
// canxml.WithStrict.
func readStrict(doc []byte) (*aom14.OperationalTemplate, error) {
	return aom14.ReadOperationalTemplate(bytes.NewReader(doc), canxml.WithStrict())
}

// compileStrict compiles a template as the checks below do, under
// templatecompile.WithStrict.
func compileStrict(opt *aom14.OperationalTemplate) (*templatecompile.Compiled, error) {
	return templatecompile.Compile(opt, templatecompile.WithStrict())
}

var (
	compiledMu sync.Mutex
	compiled   = map[string]*templatecompile.Compiled{}
)

// mustTemplate returns the template id compiled strictly, compiling it once
// for every test of the package.
func mustTemplate(t *testing.T, id string) *templatecompile.Compiled {
	t.Helper()
	compiledMu.Lock()
	defer compiledMu.Unlock()
	if c, ok := compiled[id]; ok {
		return c
	}
	opt, err := readStrict(document(t, id))
	if err != nil {
		t.Fatalf("ReadOperationalTemplate(%s, WithStrict) = %v, want no error", id, err)
	}
	c, err := compileStrict(opt)
	if err != nil {
		t.Fatalf("Compile(%s, WithStrict) = %v, want no error", id, err)
	}
	compiled[id] = c
	return c
}

func TestEveryTemplateHasItsRoot(t *testing.T) {
	t.Parallel()
	for _, id := range reference.TemplateIDs() {
		want, ok := roots[id]
		if !ok {
			t.Errorf("template %s has no root in this test: add it", id)
			continue
		}
		c := mustTemplate(t, id)
		if got := c.TemplateID(); got != id {
			t.Errorf("Compile(%s): TemplateID() = %q", id, got)
		}
		if got := c.Root().RMTypeName(); got != want.rmType {
			t.Errorf("Compile(%s): root RM type = %q, want %q", id, got, want.rmType)
		}
		if got := c.Root().ArchetypeID(); got != want.archetypeID {
			t.Errorf("Compile(%s): root archetype id = %q, want %q", id, got, want.archetypeID)
		}
	}
}

// TestStrictChecksRefuseWhatTheDefaultAccepts proves readStrict and
// compileStrict run in strict mode: each control changes a template in one
// way the default read or compile accepts and strict mode refuses, so
// dropping WithStrict from either helper fails it.
func TestStrictChecksRefuseWhatTheDefaultAccepts(t *testing.T) {
	t.Parallel()
	const id = reference.PatientTemplateID
	const concept = "</concept>"
	doc := document(t, id)
	if n := bytes.Count(doc, []byte(concept)); n != 1 {
		t.Fatalf("%s holds %q %d times, want once", id, concept, n)
	}
	unknown := bytes.Replace(doc, []byte(concept), []byte(concept+"\n  <no_such_element>x</no_such_element>"), 1)
	if _, err := aom14.ReadOperationalTemplate(bytes.NewReader(unknown)); err != nil {
		t.Fatalf("ReadOperationalTemplate(%s with an unknown element) = %v, want no error by default", id, err)
	}
	if _, err := readStrict(unknown); !errors.Is(err, canxml.ErrUnknownElement) {
		t.Errorf("readStrict(%s with an unknown element) error = %v, want canxml.ErrUnknownElement", id, err)
	}

	model, err := readStrict(doc)
	if err != nil {
		t.Fatal(err)
	}
	if model.Constraints == nil {
		model.Constraints = &aom14.TConstraint{}
	}
	model.Constraints.Attributes = append(model.Constraints.Attributes, aom14.TAttribute{
		DifferentialPath: "[" + roots[id].archetypeID + "]/no_such_attribute",
		RMAttributeName:  "value",
		Children:         []aom14.TComplexObject{{RMTypeName: "DV_TEXT", DefaultValue: &rm.DVText{Value: "x"}}},
	})
	if _, err := templatecompile.Compile(model); err != nil {
		t.Fatalf("Compile(%s with a default value that addresses no node) = %v, want no error by default", id, err)
	}
	if _, err := compileStrict(model); !errors.Is(err, templatecompile.ErrInvalidInput) {
		t.Errorf("compileStrict(%s with a default value that addresses no node) error = %v, want templatecompile.ErrInvalidInput", id, err)
	}
}

// validate checks root against c with the validator for its class.
func validate(t *testing.T, root any, c *templatecompile.Compiled) validation.Result {
	t.Helper()
	switch v := root.(type) {
	case *rm.EHRStatus:
		return validation.ValidateEHRStatus(v, c)
	case *rm.Folder:
		return validation.ValidateFolder(v, c)
	case rm.Party:
		return validation.ValidateDemographic(v, c)
	}
	t.Fatalf("Generate(%s) returned %T, want an EHR_STATUS, a FOLDER or a party", c.TemplateID(), root)
	return validation.Result{}
}

func TestGeneratedInstancesValidate(t *testing.T) {
	t.Parallel()
	policies := []instance.Policy{instance.Required, instance.Medium, instance.Large}
	fills := []instance.ValueFill{instance.ExampleFill, instance.RandomFill}
	now := time.Date(2026, 11, 19, 9, 30, 0, 0, time.UTC)

	for _, id := range reference.TemplateIDs() {
		for _, policy := range policies {
			for _, fill := range fills {
				name := fmt.Sprintf("%s/%s/%s", id, policy, fill)
				t.Run(name, func(t *testing.T) {
					t.Parallel()
					c := mustTemplate(t, id)
					root, err := instance.Generate(t.Context(), c, instance.Options{
						Policy:      policy,
						ValueFill:   fill,
						Now:         now,
						ValueSource: rand.NewPCG(1, 2),
					})
					if err != nil {
						t.Fatalf("Generate(%s) = %v, want no error", name, err)
					}
					if res := validate(t, root, c); !res.OK {
						t.Errorf("Generate(%s) then validation: OK = false, want true; issues: %+v", name, res.Issues)
					}
				})
			}
		}
	}
}
