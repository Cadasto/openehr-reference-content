// SPDX-License-Identifier: MIT

package conformance_test

// The generic EHR_STATUS and FOLDER templates accept any ITEM_STRUCTURE as
// the one attribute they constrain, plain or archetyped.

import (
	"encoding/json"
	"slices"
	"strings"
	"testing"

	reference "github.com/cadasto/openehr-reference-content"
	"github.com/cadasto/openehr-sdk-go/openehr/instance"
	"github.com/cadasto/openehr-sdk-go/openehr/rm"
	"github.com/cadasto/openehr-sdk-go/openehr/validation"
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

// itemStructureClasses are the four ITEM_STRUCTURE classes, each with the
// at-code of its plain node in both templates.
var itemStructureClasses = []struct{ rmType, atCode string }{
	{"ITEM_TREE", "at0001"},
	{"ITEM_LIST", "at0003"},
	{"ITEM_SINGLE", "at0005"},
	{"ITEM_TABLE", "at0007"},
}

func exampleArchetypeID(rmType string) string { return "openEHR-EHR-" + rmType + ".example.v1" }

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

// refusedIdentity are the issue codes that refuse a value for its node
// identity: its archetype id matches neither the at-code of its class's
// plain node (node_id_mismatch) nor the include pattern of its class's slot
// (slot_fill). The SDK reports the one or the other.
var refusedIdentity = []string{"node_id_mismatch", "slot_fill"}

func TestGenericTemplatesAcceptAnyItemStructure(t *testing.T) {
	t.Parallel()
	type itemCase struct {
		name    string
		rmType  string
		nodeID  string
		refused bool
	}
	// Each class plain and archetyped, and under the archetype id of the
	// next class, which its slot must refuse.
	var tests []itemCase
	for i, cls := range itemStructureClasses {
		other := itemStructureClasses[(i+1)%len(itemStructureClasses)].rmType
		tests = append(tests,
			itemCase{name: cls.rmType + " plain", rmType: cls.rmType, nodeID: cls.atCode},
			itemCase{name: cls.rmType + " archetyped", rmType: cls.rmType, nodeID: exampleArchetypeID(cls.rmType)},
			itemCase{name: cls.rmType + " under an " + other + " archetype", rmType: cls.rmType, nodeID: exampleArchetypeID(other), refused: true},
		)
	}
	for _, tmpl := range genericTemplates {
		c := mustTemplate(t, tmpl.id)
		for _, tc := range tests {
			t.Run(tmpl.id+"/"+tc.name, func(t *testing.T) {
				t.Parallel()
				doc := generatedJSON(t, c, instance.Required)
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
						if strings.HasPrefix(is.Path, "/"+tmpl.attr) && slices.Contains(refusedIdentity, is.Code) {
							return
						}
					}
				}
				t.Errorf("ValidateJSON(%s with %s %s as %s): want a %v issue at /%s, got OK=%v issues %v",
					tmpl.id, tc.rmType, tc.nodeID, tmpl.attr, refusedIdentity, tmpl.attr, res.OK, res.Issues)
			})
		}
	}
}

// TestGenericTemplatesRequiredInstanceLeavesDetailsOut holds the attribute
// optional: an instance generated with only its required parts leaves it
// out.
func TestGenericTemplatesRequiredInstanceLeavesDetailsOut(t *testing.T) {
	t.Parallel()
	for _, tmpl := range genericTemplates {
		doc := generatedJSON(t, mustTemplate(t, tmpl.id), instance.Required)
		if v, ok := doc[tmpl.attr]; ok {
			t.Errorf("Generate(%s, Required) holds %s = %v, want it left out", tmpl.id, tmpl.attr, v)
		}
	}
}
