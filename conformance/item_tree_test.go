// SPDX-License-Identifier: MIT

package conformance_test

// The generic EHR_STATUS and FOLDER templates accept an ITEM_TREE as the one
// attribute they constrain, plain or archetyped, and no other item structure.

import (
	"encoding/json"
	"slices"
	"strings"
	"testing"

	reference "github.com/cadasto/openehr-reference-content"
	"github.com/cadasto/openehr-sdk-go/openehr/instance"
	"github.com/cadasto/openehr-sdk-go/openehr/validation"
)

// genericTemplates are the two templates, each with the attribute it
// constrains.
var genericTemplates = []struct{ id, attr string }{
	{reference.EHRStatusTemplateID, "other_details"},
	{reference.FolderTemplateID, "details"},
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

// The issue codes that refuse a value at the attribute. byIdentity: the
// value's archetype id matches neither the at-code of the plain node nor the
// slot's include pattern; the SDK reports the one or the other. byType: the
// value is of a class no node of the attribute allows; the SDK reports
// alternative_mismatch where the attribute has several nodes and
// rm_type_mismatch where it has one, as in v0.1.0.
var (
	byIdentity = []string{"node_id_mismatch", "slot_fill"}
	byType     = []string{"alternative_mismatch", "rm_type_mismatch"}
)

func TestGenericTemplatesAcceptOnlyAnItemTree(t *testing.T) {
	t.Parallel()
	tests := []struct {
		name      string
		rmType    string
		nodeID    string
		refusedBy []string // nil: the template accepts it
	}{
		{name: "plain ITEM_TREE", rmType: "ITEM_TREE", nodeID: "at0001"},
		{name: "archetyped ITEM_TREE", rmType: "ITEM_TREE", nodeID: "openEHR-EHR-ITEM_TREE.example.v1"},
		// The slot admits an ITEM_TREE archetype of the EHR namespace only.
		{name: "ITEM_TREE under an ITEM_LIST archetype", rmType: "ITEM_TREE", nodeID: "openEHR-EHR-ITEM_LIST.example.v1", refusedBy: byIdentity},
		{name: "ITEM_TREE under a demographic archetype", rmType: "ITEM_TREE", nodeID: "openEHR-DEMOGRAPHIC-ITEM_TREE.example.v1", refusedBy: byIdentity},
		{name: "plain ITEM_LIST", rmType: "ITEM_LIST", nodeID: "at0001", refusedBy: byType},
		{name: "archetyped ITEM_LIST", rmType: "ITEM_LIST", nodeID: "openEHR-EHR-ITEM_LIST.example.v1", refusedBy: byType},
		{name: "plain ITEM_SINGLE", rmType: "ITEM_SINGLE", nodeID: "at0001", refusedBy: byType},
		{name: "archetyped ITEM_SINGLE", rmType: "ITEM_SINGLE", nodeID: "openEHR-EHR-ITEM_SINGLE.example.v1", refusedBy: byType},
		{name: "plain ITEM_TABLE", rmType: "ITEM_TABLE", nodeID: "at0001", refusedBy: byType},
		{name: "archetyped ITEM_TABLE", rmType: "ITEM_TABLE", nodeID: "openEHR-EHR-ITEM_TABLE.example.v1", refusedBy: byType},
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
				res := validation.ValidateJSON(b, newRoot(t, roots[tmpl.id].rmType), c)
				if tc.refusedBy == nil {
					if !res.OK {
						t.Errorf("ValidateJSON(%s with %s %s as %s) refused it: %v", tmpl.id, tc.rmType, tc.nodeID, tmpl.attr, res.Issues)
					}
					return
				}
				if !res.OK {
					for _, is := range res.Issues {
						if strings.HasPrefix(is.Path, "/"+tmpl.attr) && slices.Contains(tc.refusedBy, is.Code) {
							return
						}
					}
				}
				t.Errorf("ValidateJSON(%s with %s %s as %s): want a %v issue at /%s, got OK=%v issues %v",
					tmpl.id, tc.rmType, tc.nodeID, tmpl.attr, tc.refusedBy, tmpl.attr, res.OK, res.Issues)
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
