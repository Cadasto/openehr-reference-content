// SPDX-License-Identifier: MIT

package conformance_test

// Each template has an example instance, for a reader to see what it
// accepts: tech/templates/{id}/instances/{id}.json, in canonical JSON.
// make examples writes them; the test below fails when one is missing,
// differs from what it should hold, or does not validate.

import (
	"bytes"
	"encoding/json"
	"flag"
	"os"
	"path/filepath"
	"reflect"
	"testing"

	reference "github.com/cadasto/openehr-reference-content"
	"github.com/cadasto/openehr-sdk-go/openehr/instance"
	"github.com/cadasto/openehr-sdk-go/openehr/templatecompile"
	"github.com/cadasto/openehr-sdk-go/openehr/validation"
)

var update = flag.Bool("update", false, "write each template's example instance instead of comparing it (make examples)")

// examplePath is the example instance of the template id, from this
// module's folder.
func examplePath(id string) string {
	return filepath.Join("..", "tech", "templates", id, "instances", id+".json")
}

// example is what the example instance of the template id holds: the
// instance the SDK generates from it under the Medium policy, its default,
// with example values (generatedJSON), indented by two spaces, with two
// changes for a reader who copies it. The SDK leaves out an ITEM_TREE a
// template leaves open, so a generic template's example adds a plain one,
// named as its node at0001, as the details the template is about. And the
// example values make an EHR_STATUS neither queryable nor modifiable, so its
// example sets both to true, as a CDR's default EHR_STATUS has them.
func example(t *testing.T, id string, c *templatecompile.Compiled) []byte {
	t.Helper()
	doc := generatedJSON(t, c, instance.Medium)
	for _, g := range genericTemplates {
		if g.id != id {
			continue
		}
		term, ok := c.Root().Term("at0001", "")
		if !ok || term.Items["text"] == "" {
			t.Fatalf("%s has no text for at0001", id)
		}
		tree := itemStructure("ITEM_TREE", "at0001")
		tree["name"] = dvText(term.Items["text"])
		doc[g.attr] = tree
	}
	if doc["_type"] == "EHR_STATUS" {
		doc["is_queryable"], doc["is_modifiable"] = true, true
	}
	var buf bytes.Buffer
	enc := json.NewEncoder(&buf)
	enc.SetEscapeHTML(false)
	enc.SetIndent("", "  ")
	if err := enc.Encode(doc); err != nil {
		t.Fatalf("encode the example of %s: %v", id, err)
	}
	return buf.Bytes()
}

// sameJSON reports whether stored, the file at path, holds the same JSON
// value as want, whatever their layout.
func sameJSON(t *testing.T, path string, stored, want []byte) bool {
	t.Helper()
	var vs, vw any
	if err := json.Unmarshal(stored, &vs); err != nil {
		t.Fatalf("%s is not JSON: %v: run make examples", path, err)
	}
	if err := json.Unmarshal(want, &vw); err != nil {
		t.Fatalf("the example for %s is not JSON: %v", path, err)
	}
	return reflect.DeepEqual(vs, vw)
}

func TestExampleInstancesAreCurrent(t *testing.T) {
	t.Parallel()
	for _, id := range reference.TemplateIDs() {
		t.Run(id, func(t *testing.T) {
			t.Parallel()
			c := mustTemplate(t, id)
			want := example(t, id, c)
			path := examplePath(id)
			if *update {
				if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
					t.Fatal(err)
				}
				if err := os.WriteFile(path, want, 0o644); err != nil {
					t.Fatal(err)
				}
			}
			got, err := os.ReadFile(path)
			if err != nil {
				t.Fatalf("%v: run make examples", err)
			}
			if !sameJSON(t, path, got, want) {
				t.Errorf("%s differs from the example the SDK generates from %s: run make examples and review the diff", path, id)
			}
			if res := validation.ValidateJSON(got, newRoot(t, roots[id].rmType), c); !res.OK {
				t.Errorf("ValidateJSON(%s) against %s: OK = false, want true; issues: %+v", path, id, res.Issues)
			}
		})
	}
}
