// SPDX-License-Identifier: MIT

package conformance_test

// Each demographic template refuses a party that holds what it keeps out.

import (
	"encoding/json"
	"math/rand/v2"
	"strings"
	"testing"
	"time"

	reference "github.com/cadasto/openehr-reference-content"
	"github.com/cadasto/openehr-sdk-go/openehr/instance"
	"github.com/cadasto/openehr-sdk-go/openehr/rm"
	"github.com/cadasto/openehr-sdk-go/openehr/serialize/canjson"
	"github.com/cadasto/openehr-sdk-go/openehr/templatecompile"
	"github.com/cadasto/openehr-sdk-go/openehr/validation"
)

// Each template makes a promise about the parties it accepts: a patient that
// names no one, an identity that holds no relationship, relationships whose
// targets are of the right class. Each case below breaks one promise in a
// party the SDK generated from the template, which the template accepts
// unchanged, and expects the validator to refuse it at the node that breaks
// it.

// generatedParty is a party the SDK generates from the template under the
// Large policy, as a canonical JSON object to mutate.
func generatedParty(t *testing.T, c *templatecompile.Compiled) map[string]any {
	t.Helper()
	v, err := instance.Generate(t.Context(), c, instance.Options{
		Policy:    instance.Large,
		Now:       time.Date(2026, 11, 19, 12, 0, 0, 0, time.UTC),
		UIDSource: instance.UIDsFrom(rand.NewPCG(1, 2)),
	})
	if err != nil {
		t.Fatalf("Generate(%s): %v", c.TemplateID(), err)
	}
	b, err := canjson.Marshal(v)
	if err != nil {
		t.Fatalf("canjson.Marshal(%s): %v", c.TemplateID(), err)
	}
	var m map[string]any
	if err := json.Unmarshal(b, &m); err != nil {
		t.Fatalf("json.Unmarshal(%s): %v", c.TemplateID(), err)
	}
	return m
}

func detailItems(t *testing.T, party map[string]any) []any {
	t.Helper()
	d, ok := party["details"].(map[string]any)
	if !ok {
		t.Fatalf("generated %v has no details", party["_type"])
	}
	items, _ := d["items"].([]any)
	return items
}

func detailElement(t *testing.T, party map[string]any, nodeID string) map[string]any {
	t.Helper()
	for _, it := range detailItems(t, party) {
		if e := it.(map[string]any); e["archetype_node_id"] == nodeID {
			return e
		}
	}
	t.Fatalf("generated %v has no details item %s", party["_type"], nodeID)
	return nil
}

func relationshipOf(t *testing.T, party map[string]any, archetypeID string) map[string]any {
	t.Helper()
	rels, _ := party["relationships"].([]any)
	for _, r := range rels {
		if rel := r.(map[string]any); rel["archetype_node_id"] == archetypeID {
			return rel
		}
	}
	t.Fatalf("generated %v has no relationship %s", party["_type"], archetypeID)
	return nil
}

func TestDemographicTemplatesRefuseWhatTheyKeepOut(t *testing.T) {
	t.Parallel()
	const (
		patient   = reference.PatientTemplateID
		identity  = reference.PatientIdentityTemplateID
		provider  = reference.CareProviderTemplateID
		role      = reference.RoleTemplateID
		agent     = reference.AgentTemplateID
		careTeam  = reference.CareTeamTemplateID
		org       = reference.OrganisationTemplateID
		group     = reference.GroupTemplateID
		careRel   = "openEHR-DEMOGRAPHIC-PARTY_RELATIONSHIP.care_relationship.v1"
		assignRel = "openEHR-DEMOGRAPHIC-PARTY_RELATIONSHIP.role_assignment.v1"
		partOfRel = "openEHR-DEMOGRAPHIC-PARTY_RELATIONSHIP.part_of.v1"
	)
	roots := map[string]func() any{
		patient: func() any { return &rm.Person{} }, identity: func() any { return &rm.Person{} },
		provider: func() any { return &rm.Person{} }, role: func() any { return &rm.Role{} },
		agent: func() any { return &rm.Agent{} }, careTeam: func() any { return &rm.Group{} },
		org: func() any { return &rm.Organisation{} }, group: func() any { return &rm.Group{} },
	}
	compiled := map[string]*templatecompile.Compiled{}
	for id := range roots {
		compiled[id] = mustTemplate(t, id)
	}
	// A fresh copy of each template's generated party, for one case to change.
	party := func(id string) map[string]any { return generatedParty(t, compiled[id]) }

	tests := []struct {
		name     string
		template string
		mutate   func(p map[string]any)
		wantPath string
		wantCode string
	}{
		{
			name: "patient with a full date of birth", template: patient,
			mutate: func(p map[string]any) {
				detailElement(t, p, "at0003")["value"].(map[string]any)["value"] = "2020-05-17"
			},
			wantPath: "/details/items[at0003]/value/value", wantCode: "primitive_pattern_mismatch",
		},
		{
			name: "patient with a name", template: patient,
			mutate: func(p map[string]any) {
				p["identities"] = append(p["identities"].([]any), party(identity)["identities"].([]any)[0])
			},
			wantPath: "/identities[at0031]", wantCode: "slot_fill",
		},
		{
			name: "patient with a contact", template: patient,
			mutate:   func(p map[string]any) { p["contacts"] = party(identity)["contacts"] },
			wantPath: "/contacts", wantCode: "prohibited",
		},
		{
			name: "patient with a marital status", template: patient,
			mutate: func(p map[string]any) {
				d := p["details"].(map[string]any)
				d["items"] = append(detailItems(t, p), detailElement(t, party(identity), "at0011"))
			},
			wantPath: "/details/items[at0011]", wantCode: "slot_fill",
		},
		{
			name: "patient without an identifier", template: patient,
			mutate: func(p map[string]any) {
				var keep []any
				for _, it := range detailItems(t, p) {
					if it.(map[string]any)["archetype_node_id"] != "at0002" {
						keep = append(keep, it)
					}
				}
				p["details"].(map[string]any)["items"] = keep
			},
			wantPath: "/details/items[at0002]", wantCode: "cardinality",
		},
		{
			name: "patient in the care of a role", template: patient,
			mutate: func(p map[string]any) {
				relationshipOf(t, p, careRel)["target"].(map[string]any)["type"] = "ROLE"
			},
			wantPath: "/target/type", wantCode: "primitive_not_in_list",
		},
		{
			name: "identity with a relationship", template: identity,
			mutate:   func(p map[string]any) { p["relationships"] = party(patient)["relationships"] },
			wantPath: "/relationships", wantCode: "prohibited",
		},
		{
			name: "identity with a pseudonym", template: identity,
			mutate: func(p map[string]any) {
				p["identities"] = append(p["identities"].([]any), party(patient)["identities"].([]any)[0])
			},
			wantPath: "/identities[at0043]", wantCode: "slot_fill",
		},
		{
			name: "care provider with a care relationship", template: provider,
			mutate: func(p map[string]any) {
				p["relationships"] = append(p["relationships"].([]any), relationshipOf(t, party(patient), careRel))
			},
			wantPath: "/relationships", wantCode: "slot_fill",
		},
		{
			name: "role with a relationship", template: role,
			mutate:   func(p map[string]any) { p["relationships"] = party(patient)["relationships"] },
			wantPath: "/relationships", wantCode: "prohibited",
		},
		{
			name: "agent assigned a person as its role", template: agent,
			mutate: func(p map[string]any) {
				relationshipOf(t, p, assignRel)["target"].(map[string]any)["type"] = "PERSON"
			},
			wantPath: "/target/type", wantCode: "primitive_not_in_list",
		},
		{
			name: "care team with a member list", template: careTeam,
			mutate:   func(p map[string]any) { p["relationships"] = party(provider)["relationships"] },
			wantPath: "/relationships", wantCode: "prohibited",
		},
		{
			name: "care team status outside its codes", template: careTeam,
			mutate: func(p map[string]any) {
				code := detailElement(t, p, "at0003")["value"].(map[string]any)["defining_code"].(map[string]any)
				code["code_string"] = "at0010"
			},
			wantPath: "/details/items[at0003]/value/defining_code", wantCode: "primitive_not_in_list",
		},
		{
			name: "organisation part of a person", template: org,
			mutate: func(p map[string]any) {
				relationshipOf(t, p, partOfRel)["target"].(map[string]any)["type"] = "PERSON"
			},
			wantPath: "/target/type", wantCode: "primitive_not_in_list",
		},
		{
			name: "organisation with a care relationship", template: org,
			mutate: func(p map[string]any) {
				p["relationships"] = append(p["relationships"].([]any), relationshipOf(t, party(patient), careRel))
			},
			wantPath: "/relationships", wantCode: "slot_fill",
		},
		{
			name: "group with a member list", template: group,
			mutate:   func(p map[string]any) { p["relationships"] = party(provider)["relationships"] },
			wantPath: "/relationships", wantCode: "prohibited",
		},
		{
			name: "group characteristic without a value", template: group,
			mutate: func(p map[string]any) {
				c := detailElement(t, p, "at0012")
				var keep []any
				for _, it := range c["items"].([]any) {
					if it.(map[string]any)["archetype_node_id"] != "at0014" {
						keep = append(keep, it)
					}
				}
				c["items"] = keep
			},
			wantPath: "/items[at0014]", wantCode: "cardinality",
		},
	}

	for id, root := range roots {
		t.Run("generated "+id+" is accepted", func(t *testing.T) {
			b, err := json.Marshal(party(id))
			if err != nil {
				t.Fatal(err)
			}
			if res := validation.ValidateJSON(b, root(), compiled[id]); !res.OK {
				t.Errorf("ValidateJSON(generated %s) refused it: %v", id, res.Issues)
			}
		})
	}
	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			p := party(tc.template)
			tc.mutate(p)
			b, err := json.Marshal(p)
			if err != nil {
				t.Fatal(err)
			}
			res := validation.ValidateJSON(b, roots[tc.template](), compiled[tc.template])
			for _, is := range res.Issues {
				if strings.Contains(is.Path, tc.wantPath) && is.Code == tc.wantCode {
					return
				}
			}
			t.Errorf("ValidateJSON(%s, %s): want a %s issue at %s, got OK=%v issues %v",
				tc.template, tc.name, tc.wantCode, tc.wantPath, res.OK, res.Issues)
		})
	}
}
