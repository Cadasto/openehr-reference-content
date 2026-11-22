// SPDX-License-Identifier: MIT

package conformance_test

// The generic EHR_STATUS and FOLDER templates accept any ITEM_STRUCTURE as
// the one attribute they constrain, plain or archetyped.

import (
	"encoding/json"
	"math/rand/v2"
	"strings"
	"testing"
	"time"

	"github.com/cadasto/openehr-sdk-go/openehr/instance"
	"github.com/cadasto/openehr-sdk-go/openehr/rm"
	"github.com/cadasto/openehr-sdk-go/openehr/serialize/canjson"
	"github.com/cadasto/openehr-sdk-go/openehr/templatecompile"
	"github.com/cadasto/openehr-sdk-go/openehr/validation"

	reference "github.com/cadasto/openehr-reference-content"
)

// genericTemplates are the two templates, each with the attribute it
// constrains and a value of its root class to validate into.
var genericTemplates = []struct {
	id   string
	attr string
	root func() any
}{
	{reference.EHRStatusTemplateID, "other_details", func() any { return &rm.EHRStatus{} }},
	{reference.FolderTemplateID, "details", func() any { return &rm.Folder{} }},
}

// requiredOnly is the instance the SDK generates from c with only its
// required parts, as a canonical JSON object.
func requiredOnly(t *testing.T, c *templatecompile.Compiled) map[string]any {
	t.Helper()
	v, err := instance.Generate(t.Context(), c, instance.Options{
		Policy:    instance.Required,
		Now:       time.Date(2026, 11, 22, 12, 0, 0, 0, time.UTC),
		UIDSource: instance.UIDsFrom(rand.NewPCG(1, 2)),
	})
	if err != nil {
		t.Fatalf("Generate(%s, Required): %v", c.TemplateID(), err)
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

func dvText(v string) map[string]any { return map[string]any{"_type": "DV_TEXT", "value": v} }

func element(nodeID string) map[string]any {
	return map[string]any{"_type": "ELEMENT", "name": dvText("Note"), "archetype_node_id": nodeID, "value": dvText("A note.")}
}

// itemStructure is an instance of rmType whose archetype_node_id is nodeID,
// holding one element. A nodeID that is an archetype id makes it an
// archetype root, with archetype_details naming that archetype.
func itemStructure(rmType, nodeID string) map[string]any {
	s := map[string]any{"_type": rmType, "name": dvText("Details"), "archetype_node_id": nodeID}
	switch rmType {
	case "ITEM_TREE", "ITEM_LIST":
		s["items"] = []any{element("at0101")}
	case "ITEM_SINGLE":
		s["item"] = element("at0101")
	case "ITEM_TABLE":
		s["rows"] = []any{map[string]any{
			"_type": "CLUSTER", "name": dvText("Row"), "archetype_node_id": "at0102",
			"items": []any{element("at0101")},
		}}
	}
	if strings.HasPrefix(nodeID, "openEHR-") {
		s["archetype_details"] = map[string]any{
			"_type":        "ARCHETYPED",
			"archetype_id": map[string]any{"_type": "ARCHETYPE_ID", "value": nodeID},
			"rm_version":   "1.2.0",
		}
	}
	return s
}

func TestGenericTemplatesAcceptAnyItemStructure(t *testing.T) {
	t.Parallel()
	tests := []struct {
		name    string
		rmType  string
		nodeID  string
		refused bool
	}{
		{name: "plain tree", rmType: "ITEM_TREE", nodeID: "at0001"},
		{name: "archetyped tree", rmType: "ITEM_TREE", nodeID: "openEHR-EHR-ITEM_TREE.example.v1"},
		{name: "plain list", rmType: "ITEM_LIST", nodeID: "at0003"},
		{name: "archetyped list", rmType: "ITEM_LIST", nodeID: "openEHR-EHR-ITEM_LIST.example.v1"},
		{name: "plain single item", rmType: "ITEM_SINGLE", nodeID: "at0005"},
		{name: "archetyped single item", rmType: "ITEM_SINGLE", nodeID: "openEHR-EHR-ITEM_SINGLE.example.v1"},
		{name: "plain table", rmType: "ITEM_TABLE", nodeID: "at0007"},
		{name: "archetyped table", rmType: "ITEM_TABLE", nodeID: "openEHR-EHR-ITEM_TABLE.example.v1"},
		// An archetype id that names another class matches no slot of the
		// value's class, nor the at-code of its plain node.
		{name: "list under a tree archetype", rmType: "ITEM_LIST", nodeID: "openEHR-EHR-ITEM_TREE.example.v1", refused: true},
		{name: "tree under a list archetype", rmType: "ITEM_TREE", nodeID: "openEHR-EHR-ITEM_LIST.example.v1", refused: true},
	}
	for _, tmpl := range genericTemplates {
		c := mustTemplate(t, tmpl.id)
		for _, tc := range tests {
			t.Run(tmpl.id+"/"+tc.name, func(t *testing.T) {
				t.Parallel()
				doc := requiredOnly(t, c)
				doc[tmpl.attr] = itemStructure(tc.rmType, tc.nodeID)
				b, err := json.Marshal(doc)
				if err != nil {
					t.Fatal(err)
				}
				res := validation.ValidateJSON(b, tmpl.root(), c)
				if !tc.refused {
					if !res.OK {
						t.Errorf("ValidateJSON(%s with %s %s as %s) refused it: %v", tmpl.id, tc.rmType, tc.nodeID, tmpl.attr, res.Issues)
					}
					return
				}
				if !res.OK {
					for _, is := range res.Issues {
						if strings.HasPrefix(is.Path, "/"+tmpl.attr) {
							return
						}
					}
				}
				t.Errorf("ValidateJSON(%s with %s %s as %s): want it refused at /%s, got OK=%v issues %v",
					tmpl.id, tc.rmType, tc.nodeID, tmpl.attr, tmpl.attr, res.OK, res.Issues)
			})
		}
	}
}

// TestGenericTemplatesGenerateNoDetailsByDefault holds the attribute
// optional: an instance generated with only its required parts leaves it
// out, as it did when the templates allowed a plain tree alone.
func TestGenericTemplatesGenerateNoDetailsByDefault(t *testing.T) {
	t.Parallel()
	for _, tmpl := range genericTemplates {
		doc := requiredOnly(t, mustTemplate(t, tmpl.id))
		if v, ok := doc[tmpl.attr]; ok {
			t.Errorf("Generate(%s, Required) holds %s = %v, want it left out", tmpl.id, tmpl.attr, v)
		}
	}
}
