// SPDX-License-Identifier: MIT

package reference_test

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/xml"
	"fmt"
	"os"
	"path/filepath"
	"slices"
	"testing"

	reference "github.com/cadasto/openehr-reference-content"
)

// shipped pins each template the module ships: its constant and the SHA-256
// digest of its document. A change to a document fails
// TestDocumentDigestIsPinned until the same change moves the pin.
var shipped = []struct {
	constant string
	sha256   string
}{
	{reference.AgentTemplateID, "b9bfc86c832a7bd6c807efe3ab49c57a092fd2f5c7b0635949f2bdfc23176497"},
	{reference.CareTeamTemplateID, "e0ed7ec18bdb9c87d7b76eecd380d7b9a0b9f573f0423f45f9a786de50a7e25d"},
	{reference.GroupTemplateID, "e19c6c5419a8cc692991f6bf8b930b09bafa08cbbbb8033c7327e5ae22e96a6b"},
	{reference.OrganisationTemplateID, "09a41c892a923569895b77e6448148d62b6a56f08305924e30b09cfef5139a30"},
	{reference.CareProviderTemplateID, "9f268c346f4013680de431d90357d8818bbea5dfea4da0801021c99639c4f4a7"},
	{reference.PatientTemplateID, "42ab2e4debe97ff4a05a34deebcd846bbee1f950dd832d8d197c2ef8223904e7"},
	{reference.PatientIdentityTemplateID, "160a3f76da5885996c7d6d03399f7acfddd0d2c21a401ed18e27da36443bb945"},
	{reference.RoleTemplateID, "6f3008d019d2d3963aefd73a8135ee85e9ed2ad8b78f03ee6246869eb77aa41a"},
	{reference.EHRStatusTemplateID, "4bbcaa6944a382424bf87df07b67f7ad509328e098decc42ca79b252d52e0ccb"},
	{reference.FolderTemplateID, "ff87664de7c39ec07a62e5536aa32d28c35a85f748630d9af303fbfdc21d5839"},
}

// TestTemplateIDsListEveryFolder holds TemplateIDs to the constants and to
// the folders under tech/templates, so a folder added without its constant,
// or a constant without its folder, fails here.
func TestTemplateIDsListEveryFolder(t *testing.T) {
	t.Parallel()
	var want []string
	for _, s := range shipped {
		want = append(want, s.constant)
	}
	slices.Sort(want)

	got := reference.TemplateIDs()
	if !slices.Equal(got, want) {
		t.Errorf("TemplateIDs() = %q, want the constants %q", got, want)
	}

	entries, err := os.ReadDir(filepath.Join("tech", "templates"))
	if err != nil {
		t.Fatal(err)
	}
	var folders []string
	for _, e := range entries {
		if e.Name() == "README.md" {
			continue
		}
		if !e.IsDir() {
			t.Errorf("tech/templates holds the file %s, want only its README.md and one folder per template", e.Name())
			continue
		}
		folders = append(folders, e.Name())
		opts, err := filepath.Glob(filepath.Join("tech", "templates", e.Name(), "opt", "*.opt"))
		if err != nil {
			t.Fatal(err)
		}
		if want := []string{filepath.Join("tech", "templates", e.Name(), "opt", e.Name()+".opt")}; !slices.Equal(opts, want) {
			t.Errorf("tech/templates/%s/opt holds %q, want %q", e.Name(), opts, want)
		}
	}
	if !slices.Equal(folders, want) {
		t.Errorf("tech/templates holds the folders %q, want one for each of %q", folders, want)
	}

	got[0] = "changed"
	if again := reference.TemplateIDs(); again[0] != want[0] {
		t.Errorf("changing one TemplateIDs result changed the next to %q: the calls share their slice", again)
	}
}

func TestOPTIsTheFileInANewSlice(t *testing.T) {
	t.Parallel()
	for _, s := range shipped {
		t.Run(s.constant, func(t *testing.T) {
			t.Parallel()
			want, err := os.ReadFile(filepath.Join("tech", "templates", s.constant, "opt", s.constant+".opt"))
			if err != nil {
				t.Fatal(err)
			}
			first, ok := reference.OPT(s.constant)
			if !ok || !bytes.Equal(first, want) {
				t.Fatalf("OPT(%q) = %d bytes, %t, want the %d bytes of its file, true", s.constant, len(first), ok, len(want))
			}
			clear(first)
			if next, _ := reference.OPT(s.constant); !bytes.Equal(next, want) {
				t.Errorf("clearing one OPT(%q) result changed the next: the calls share their bytes", s.constant)
			}
		})
	}
}

func TestOPTRefusesAnIDItDoesNotShip(t *testing.T) {
	t.Parallel()
	for _, id := range []string{"", "PERSON-Patient.v1.opt", "person-patient.v1", "PERSON-Patient.v2", "../PERSON-Patient.v1", "*"} {
		if b, ok := reference.OPT(id); ok || b != nil {
			t.Errorf("OPT(%q) = %d bytes, %t, want nil, false", id, len(b), ok)
		}
	}
}

// TestDocumentNamesItsFolder holds each document's template id to the
// folder, the file and the constant that name it.
func TestDocumentNamesItsFolder(t *testing.T) {
	t.Parallel()
	for _, s := range shipped {
		doc, _ := reference.OPT(s.constant)
		var header struct {
			TemplateID string `xml:"template_id>value"`
		}
		if err := xml.Unmarshal(doc, &header); err != nil {
			t.Errorf("OPT(%q): %v", s.constant, err)
			continue
		}
		if header.TemplateID != s.constant {
			t.Errorf("OPT(%q) holds the template id %q, want %q", s.constant, header.TemplateID, s.constant)
		}
	}
}

func TestDocumentDigestIsPinned(t *testing.T) {
	t.Parallel()
	for _, s := range shipped {
		doc, _ := reference.OPT(s.constant)
		sum := sha256.Sum256(doc)
		if got := hex.EncodeToString(sum[:]); got != s.sha256 {
			t.Errorf("%s changed: its SHA-256 is %s, the pin is %s.\n"+
				"A server stores the template, with the instances written against it, so:\n"+
				"  - a change must not refuse an instance the template under the same id accepted before;\n"+
				"    a change that would ships under a new id (the next version), and the old id's template stays;\n"+
				"  - CHANGELOG.md records the change, under the release that ships it.\n"+
				"When the change keeps both rules, move this pin to %s in the same change.",
				s.constant, got, s.sha256, got)
		}
	}
}

// The templates the module ships, by template id.
func ExampleTemplateIDs() {
	for _, id := range reference.TemplateIDs() {
		fmt.Println(id)
	}
	// Output:
	// AGENT-generic-agent.v1
	// GROUP-CareTeam.v1
	// GROUP-generic.v1
	// ORGANISATION-generic.v1
	// PERSON-CareProvider.v1
	// PERSON-Patient.v1
	// PERSON-PatientIdentity.v1
	// ROLE-generic-role.v1
	// generic_ehr_status.v1
	// generic_folder.v1
}

// A template's document, for upload to a server.
func ExampleOPT() {
	doc, ok := reference.OPT(reference.PatientTemplateID)
	fmt.Println(ok, bytes.HasPrefix(doc, []byte("<?xml")))
	// Output:
	// true true
}
