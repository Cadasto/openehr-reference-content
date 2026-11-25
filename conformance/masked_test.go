// SPDX-License-Identifier: MIT

package conformance_test

// A service may keep a patient's identifying values apart and store the
// patient's PERSON with each of them masked: the ELEMENT stays, its value is
// emptied and its null flavour is masked (openehr code 272). The patient
// template accepts such a party, whichever of its elements are masked.

import (
	"bytes"
	"encoding/json"
	"strings"
	"testing"

	reference "github.com/cadasto/openehr-reference-content"
	"github.com/cadasto/openehr-sdk-go/openehr/instance"
	"github.com/cadasto/openehr-sdk-go/openehr/templatecompile"
	"github.com/cadasto/openehr-sdk-go/openehr/validation"
)

// maskElements empties every ELEMENT under v and gives it the null flavour
// masked, and returns how many it masked.
func maskElements(v any) int {
	n := 0
	switch x := v.(type) {
	case map[string]any:
		if x["_type"] == "ELEMENT" {
			delete(x, "value")
			x["null_flavour"] = map[string]any{
				"_type": "DV_CODED_TEXT",
				"value": "masked",
				"defining_code": map[string]any{
					"_type":          "CODE_PHRASE",
					"terminology_id": map[string]any{"_type": "TERMINOLOGY_ID", "value": "openehr"},
					"code_string":    "272",
				},
			}
			n++
		}
		for _, c := range x {
			n += maskElements(c)
		}
	case []any:
		for _, c := range x {
			n += maskElements(c)
		}
	}
	return n
}

// maskedPatient is the party the SDK generates from c under the Large
// policy, with every ELEMENT masked, as canonical JSON.
func maskedPatient(t *testing.T, c *templatecompile.Compiled) []byte {
	t.Helper()
	p := generatedJSON(t, c, instance.Large)
	if n := maskElements(p); n == 0 {
		t.Fatalf("generated %s holds no ELEMENT to mask", c.TemplateID())
	}
	b, err := json.Marshal(p)
	if err != nil {
		t.Fatal(err)
	}
	return b
}

func TestPatientAcceptsMaskedElements(t *testing.T) {
	t.Parallel()
	const id = reference.PatientTemplateID
	c := mustTemplate(t, id)
	if res := validation.ValidateJSON(maskedPatient(t, c), newRoot(t, roots[id].rmType), c); !res.OK {
		t.Errorf("ValidateJSON(%s with every ELEMENT masked): OK = false, want true; issues: %+v", id, res.Issues)
	}
}

// TestMaskedElementsRefusedWhereAValueIsMandatory is the control: with the
// value of its first ELEMENT, the identifier, made mandatory, the template
// refuses the masked party there, so TestPatientAcceptsMaskedElements fails
// for a template that makes any masked value mandatory.
func TestMaskedElementsRefusedWhereAValueIsMandatory(t *testing.T) {
	t.Parallel()
	const id = reference.PatientTemplateID
	doc := document(t, id)
	attr := bytes.Index(doc, []byte("<rm_attribute_name>value</rm_attribute_name>"))
	if attr < 0 {
		t.Fatalf("%s constrains no value attribute", id)
	}
	end := attr + bytes.Index(doc[attr:], []byte("</existence>"))
	existence := doc[attr:end]
	if bytes.Count(existence, []byte("<lower>0</lower>")) != 1 {
		t.Fatalf("%s: the first value attribute's existence is not optional: %s", id, existence)
	}
	changed := bytes.Join([][]byte{
		doc[:attr],
		bytes.Replace(existence, []byte("<lower>0</lower>"), []byte("<lower>1</lower>"), 1),
		doc[end:],
	}, nil)
	opt, err := readStrict(changed)
	if err != nil {
		t.Fatal(err)
	}
	c, err := compileStrict(opt)
	if err != nil {
		t.Fatal(err)
	}
	// The validator names an identifier by its position among the items.
	res := validation.ValidateJSON(maskedPatient(t, c), newRoot(t, roots[id].rmType), c)
	for _, is := range res.Issues {
		if is.Code == "required" && strings.HasPrefix(is.Path, "/details/items[") && strings.HasSuffix(is.Path, "]/value") {
			return
		}
	}
	t.Errorf("ValidateJSON(%s with every ELEMENT masked) against the template with a mandatory identifier value: want a required issue at /details/items[n]/value, got OK=%v issues %v",
		id, res.OK, res.Issues)
}
