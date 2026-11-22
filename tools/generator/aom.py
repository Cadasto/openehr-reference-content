# SPDX-License-Identifier: MIT
"""A small AOM 1.4 model with an ADL 1.4 writer, an OPT 1.4 XML writer, a reader for
CKM's ARCHETYPE XML export, and the template operations that flatten archetypes into an
operational template.

Python 3.9, standard library only.
"""
import copy
import re
import xml.etree.ElementTree as ET

OPENEHR_NS = "http://schemas.openehr.org/v1"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
XSD_NS = "http://www.w3.org/2001/XMLSchema"
XSI_TYPE = "{%s}type" % XSI_NS
STAR = None  # an unbounded upper limit

# RM attributes that hold a list: they are C_MULTIPLE_ATTRIBUTEs and carry a cardinality.
MULTIPLE = {"items", "identities", "contacts", "relationships", "addresses",
            "capabilities", "languages", "roles", "reverse_relationships"}


class Obj:
    """A C_OBJECT. kind is complex, root, slot, code_phrase, primitive or raw."""

    def __init__(self, rm, node_id="", occ=(1, 1), attrs=None, kind="complex"):
        self.rm = rm
        self.node_id = node_id
        self.occ = occ
        self.attrs = list(attrs or [])
        self.kind = kind
        self.include = []        # slot: include patterns, without the slashes
        self.open = False        # slot: a template keeps it (keep_open)
        self.archetype = None    # root: the archetype it embeds
        self.terminology = None  # code_phrase
        self.codes = []          # code_phrase
        self.prim = None         # primitive: (xsi type, [(tag, text)])
        self.raw = None          # raw: the C_OBJECT element as CKM wrote it

    def attr(self, name):
        for a in self.attrs:
            if a.name == name:
                return a
        return None

    def key(self):
        if self.kind == "root":
            return self.archetype.archetype_id
        return self.node_id


class Attr:
    def __init__(self, name, children, existence=(1, 1), card=None):
        self.name = name
        self.children = list(children)
        self.existence = existence
        # card: (lower, upper, ordered, unique), for a list attribute only
        if card is None and name in MULTIPLE:
            card = (0, STAR, False, False)
        self.card = card


class Archetype:
    def __init__(self, archetype_id, definition, terms, uid=None, description=None,
                 bindings=None, source="local"):
        self.archetype_id = archetype_id
        self.definition = definition
        self.terms = terms          # code -> (text, description, comment or None)
        self.uid = uid
        self.description = description or {}
        self.bindings = bindings or {}  # terminology -> {code: target code}
        self.source = source

    @property
    def rm_type(self):
        return self.archetype_id.split("-")[2].split(".")[0]


# ---------------------------------------------------------------- authoring helpers

_terms = None


def begin_terms():
    global _terms
    _terms = {}


def end_terms():
    global _terms
    t, _terms = _terms, None
    return t


def term(code, text, description, comment=None):
    if code in _terms:
        raise ValueError("term %s defined twice" % code)
    _terms[code] = (text, description, comment)
    return code


def C(rm, code, text, description, attrs=(), occ=(1, 1), comment=None):
    term(code, text, description, comment)
    return Obj(rm, code, occ, attrs)


def A(name, children, existence=(1, 1), card=None):
    return Attr(name, children, existence, card)


def ITEMS(*children, card=(1, STAR, False, False)):
    return Attr("items", list(children), (1, 1), card)


def DV(rm):
    return Obj(rm, "", (1, 1))


def CODED(*codes, terminology="local"):
    """A DV_CODED_TEXT over local codes, each given as (code, text, description)."""
    for c in codes:
        term(*c)
    cp = Obj("CODE_PHRASE", kind="code_phrase")
    cp.terminology = terminology
    cp.codes = [c[0] for c in codes]
    return Obj("DV_CODED_TEXT", attrs=[Attr("defining_code", [cp])])


def DATE(pattern):
    p = Obj("DATE", kind="primitive")
    p.prim = ("C_DATE", [("pattern", pattern)])
    return Obj("DV_DATE", attrs=[Attr("value", [p])])


def PARTY_REF(*types):
    p = Obj("STRING", kind="primitive")
    p.prim = ("C_STRING", [("list", t) for t in types])
    return Obj("PARTY_REF", attrs=[Attr("type", [p])])


def E(code, text, description, values, occ=(0, 1), comment=None):
    return C("ELEMENT", code, text, description, [Attr("value", values, (0, 1))], occ, comment)


def SLOT(rm, code, text, description, includes, occ=(0, 1), comment=None):
    term(code, text, description, comment)
    o = Obj(rm, code, occ, kind="slot")
    o.include = list(includes)
    return o


def CKM_SLOT(name):
    return r"openEHR-EHR-CLUSTER\.%s(-[a-zA-Z0-9_]+)*\.v1" % name


# ---------------------------------------------------------------- reading CKM XML

def _strip(el):
    """Drop the openEHR namespace from tags, keep xsi:type as a plain attribute."""
    for e in el.iter():
        if e.tag.startswith("{"):
            e.tag = e.tag.split("}", 1)[1]
        t = e.attrib.pop(XSI_TYPE, None)
        if t is not None:
            e.set("xsi:type", t)
    return el


def _interval(el):
    lo = int(el.findtext("lower")) if el.findtext("lower") is not None else 0
    if el.findtext("upper_unbounded") == "true":
        return (lo, STAR)
    return (lo, int(el.findtext("upper")))


def _parse_obj(el):
    kind = el.get("xsi:type") or "C_COMPLEX_OBJECT"
    rm = el.findtext("rm_type_name")
    occ = _interval(el.find("occurrences"))
    node_id = el.findtext("node_id") or ""
    if kind == "C_COMPLEX_OBJECT":
        o = Obj(rm, node_id, occ)
        o.attrs = [_parse_attr(a) for a in el.findall("attributes")]
        return o
    if kind == "ARCHETYPE_SLOT":
        o = Obj(rm, node_id, occ, kind="slot")
        for inc in el.findall("includes"):
            m = re.search(r"matches \{/(.*)/\}", inc.findtext("string_expression") or "")
            if m:
                o.include.append(m.group(1))
        return o
    o = Obj(rm, node_id, occ, kind="raw")
    o.raw = copy.deepcopy(el)
    return o


def _parse_attr(el):
    a = Attr(el.findtext("rm_attribute_name"),
             [_parse_obj(c) for c in el.findall("children")],
             _interval(el.find("existence")))
    card = el.find("cardinality")
    if el.get("xsi:type") == "C_MULTIPLE_ATTRIBUTE" and card is not None:
        lo, hi = _interval(card.find("interval"))
        a.card = (lo, hi, card.findtext("is_ordered") == "true", card.findtext("is_unique") == "true")
    else:
        a.card = None
    return a


def load_ckm_xml(path):
    root = _strip(ET.parse(path).getroot())
    archetype_id = root.findtext("archetype_id/value")
    terms = {}
    for td in root.findall("ontology/term_definitions"):
        if td.get("language") != "en":
            continue
        for item in td.findall("items"):
            d = {i.get("id"): (i.text or "") for i in item.findall("items")}
            terms[item.get("code")] = (d.get("text", ""), d.get("description", ""), d.get("comment"))
    other = {i.get("id"): i.text for i in root.findall("description/other_details")}
    desc = {"purpose": root.findtext("description/details/purpose"),
            "licence": other.get("licence"),
            "revision": other.get("revision"),
            "copyright": root.findtext("description/details/copyright")}
    return Archetype(archetype_id, _parse_obj(root.find("definition")), terms,
                     uid=root.findtext("uid/value"), description=desc, source="ckm")


# ---------------------------------------------------------------- ADL 1.4 writer

def _occ(occ):
    lo, hi = occ
    return "%d..%s" % (lo, "*" if hi is STAR else hi)


def _q(s):
    return '"%s"' % s.replace("\\", "\\\\").replace('"', '\\"')


def _adl_obj(o, ind, terms, out, root=False):
    t = "\t" * ind
    text = terms.get(o.node_id, (None,))[0] if o.node_id else None
    comment = ("\t-- %s" % text) if text else ""
    if o.kind == "slot":
        out.append("%sallow_archetype %s[%s] occurrences matches {%s} matches {%s"
                   % (t, o.rm, o.node_id, _occ(o.occ), comment))
        out.append("%s\tinclude" % t)
        for inc in o.include:
            out.append("%s\t\tarchetype_id/value matches {/%s/}" % (t, inc))
        out.append("%s}" % t)
        return
    if o.kind == "code_phrase":
        out.append("%s[%s::" % (t, o.terminology))
        for i, c in enumerate(o.codes):
            sep = "]" if i == len(o.codes) - 1 else ","
            label = terms.get(c, ("",))[0]
            out.append("%s%s%s\t-- %s" % (t, c, sep, label))
        return
    head = o.rm + ("[%s]" % o.node_id if o.node_id else "")
    if o.node_id and not root:
        head += " occurrences matches {%s}" % _occ(o.occ)
    if not o.attrs:
        out.append("%s%s matches {*}%s" % (t, head, comment))
        return
    out.append("%s%s matches {%s" % (t, head, comment))
    for a in o.attrs:
        _adl_attr(a, ind + 1, terms, out)
    out.append("%s}" % t)


def _adl_prim(p):
    xtype, fields = p.prim
    if xtype == "C_STRING":
        return "{%s}" % ", ".join(_q(v) for k, v in fields if k == "list")
    if xtype == "C_DATE":
        return "{%s}" % dict(fields)["pattern"]
    raise ValueError("no ADL form for %s" % xtype)


def _adl_attr(a, ind, terms, out):
    t = "\t" * ind
    head = a.name
    if a.existence != (1, 1) and not (a.name == "value" and a.existence == (0, 1)):
        head += " existence matches {%s}" % _occ(a.existence)
    if a.card is not None:
        lo, hi, ordered, unique = a.card
        head += " cardinality matches {%s; %s%s}" % (
            _occ((lo, hi)), "ordered" if ordered else "unordered", "; unique" if unique else "")
    if not a.children:
        out.append("%s%s matches {*}" % (t, head))
        return
    if len(a.children) == 1 and a.children[0].kind == "primitive":
        out.append("%s%s matches %s" % (t, head, _adl_prim(a.children[0])))
        return
    out.append("%s%s matches {" % (t, head))
    for c in a.children:
        _adl_obj(c, ind + 1, terms, out)
    out.append("%s}" % t)


def _odin_list(values):
    return ", ".join(_q(v) for v in values)


def write_adl(arch, meta):
    """Serialise a locally authored archetype as ADL 1.4 text."""
    d = arch.description
    out = ["archetype (adl_version=1.4; uid=%s)" % arch.uid,
           "\t%s" % arch.archetype_id, "",
           "concept", "\t[at0000]\t-- %s" % arch.terms["at0000"][0],
           "language", "\toriginal_language = <[ISO_639-1::en]>", "",
           "description",
           "\toriginal_author = <",
           '\t\t["name"] = <%s>' % _q(meta["author"]),
           '\t\t["date"] = <%s>' % _q(meta["date"]),
           "\t>",
           "\tdetails = <",
           '\t\t["en"] = <',
           "\t\t\tlanguage = <[ISO_639-1::en]>",
           "\t\t\tpurpose = <%s>" % _q(d["purpose"]),
           "\t\t\tuse = <%s>" % _q(d["use"]),
           "\t\t\tkeywords = <%s>" % _odin_list(d["keywords"]),
           "\t\t\tmisuse = <%s>" % _q(d["misuse"]),
           "\t\t\tcopyright = <%s>" % _q(meta["copyright"]),
           "\t\t>",
           "\t>",
           "\tlifecycle_state = <%s>" % _q(meta["lifecycle_state"]),
           "\tother_details = <",
           '\t\t["licence"] = <%s>' % _q(meta["licence"]),
           '\t\t["references"] = <%s>' % _q(d["references"]),
           "\t>", "",
           "definition"]
    _adl_obj(arch.definition, 1, arch.terms, out, root=True)
    out += ["", "ontology"]
    if arch.bindings:
        out.append("\tterminologies_available = <%s>" % _odin_list(sorted(arch.bindings)))
    out += ["\tterm_definitions = <", '\t\t["en"] = <', "\t\t\titems = <"]
    for code in sorted(arch.terms, key=_code_key):
        text, desc, comment = arch.terms[code]
        out.append('\t\t\t\t["%s"] = <' % code)
        out.append("\t\t\t\t\ttext = <%s>" % _q(text))
        out.append("\t\t\t\t\tdescription = <%s>" % _q(desc))
        if comment:
            out.append("\t\t\t\t\tcomment = <%s>" % _q(comment))
        out.append("\t\t\t\t>")
    out += ["\t\t\t>", "\t\t>", "\t>"]
    if arch.bindings:
        out.append("\tterm_bindings = <")
        for tid in sorted(arch.bindings):
            out += ['\t\t["%s"] = <' % tid, "\t\t\titems = <"]
            for code in sorted(arch.bindings[tid], key=_code_key):
                out.append('\t\t\t\t["%s"] = <[%s::%s]>' % (code, tid, arch.bindings[tid][code]))
            out += ["\t\t\t>", "\t\t>"]
        out.append("\t>")
    return "\n".join(out) + "\n"


def _code_key(code):
    return [int(p) for p in re.findall(r"\d+", code)]


# ---------------------------------------------------------------- template operations

def instantiate(arch, occ=None):
    """An archetype root node: a deep copy of the archetype's definition."""
    o = copy.deepcopy(arch.definition)
    o.kind = "root"
    o.archetype = arch
    o.node_id = "at0000"
    if occ is not None:
        o.occ = occ
    return o


def _segments(path):
    segs = []
    for part in re.findall(r"[a-z_]+(?:\[[^\]]+\])?", path):
        m = re.fullmatch(r"([a-z_]+)(?:\[([^\]]+)\])?", part)
        segs.append((m.group(1), m.group(2)))
    return segs


def find(root, path):
    """The node at an archetype path such as /details[at0001]/items[at0002]."""
    node = root
    for name, key in _segments(path):
        a = node.attr(name)
        if a is None:
            raise KeyError("%s: no attribute %s" % (path, name))
        if key is None:
            if len(a.children) != 1:
                raise KeyError("%s: %s has %d children" % (path, name, len(a.children)))
            node = a.children[0]
            continue
        hits = [c for c in a.children if c.key() == key]
        if len(hits) != 1:
            raise KeyError("%s: %d nodes match %s" % (path, len(hits), key))
        node = hits[0]
    return node


def _parent(root, path):
    segs = _segments(path)
    parent = find(root, "/" + "/".join("%s[%s]" % s if s[1] else s[0] for s in segs[:-1])) \
        if len(segs) > 1 else root
    return parent, parent.attr(segs[-1][0]), segs[-1][1]


def drop(root, *paths):
    for path in paths:
        _, attr, key = _parent(root, path)
        before = len(attr.children)
        attr.children = [c for c in attr.children if c.key() != key]
        if len(attr.children) != before - 1:
            raise KeyError("drop %s: no such node" % path)


def occurrences(root, path, lo, hi):
    node = find(root, path)
    if lo < node.occ[0] or (node.occ[1] is not STAR and (hi is STAR or hi > node.occ[1])):
        raise ValueError("%s: %s widens %s" % (path, (lo, hi), node.occ))
    node.occ = (lo, hi)


def existence(root, path, name, lo, hi):
    node = find(root, path) if path not in ("", "/") else root
    a = node.attr(name)
    if a is None:
        a = Attr(name, [], (0, 1))
        node.attrs.append(a)
    if lo < a.existence[0] or hi > a.existence[1]:
        raise ValueError("%s/%s: existence %s widens %s" % (path, name, (lo, hi), a.existence))
    a.existence = (lo, hi)
    if hi == 0:
        a.children = []


def fill(root, slot_path, *archetypes, occ=None):
    """Replace a slot by the roots of the archetypes that fill it."""
    _, attr, key = _parent(root, slot_path)
    idx = [i for i, c in enumerate(attr.children) if c.kind == "slot" and c.node_id == key]
    if len(idx) != 1:
        raise KeyError("fill %s: no such slot" % slot_path)
    slot = attr.children[idx[0]]
    roots = []
    for arch in archetypes:
        if not any(re.fullmatch(inc, arch.archetype_id) for inc in slot.include):
            raise ValueError("%s does not match the slot %s" % (arch.archetype_id, slot_path))
        roots.append(instantiate(arch, occ or slot.occ))
    attr.children[idx[0]:idx[0] + 1] = roots


def date_pattern(root, element_path, pattern):
    el = find(root, element_path)
    dv = [c for c in el.attr("value").children if c.rm == "DV_DATE"]
    dv[0].attrs = DATE(pattern).attrs


def keep_open(root, *slot_paths):
    """Keep slots open in the template: close_slots leaves them, and the OPT holds each as
    an ARCHETYPE_SLOT that admits any archetype its include patterns match."""
    for path in slot_paths:
        node = find(root, path)
        if node.kind != "slot":
            raise KeyError("keep_open %s: not a slot" % path)
        node.open = True


def close_slots(node):
    """Remove every slot the template left unfilled and did not keep open."""
    for a in node.attrs:
        a.children = [c for c in a.children if c.kind != "slot" or c.open]
        for c in a.children:
            if c.kind in ("complex", "root"):
                close_slots(c)


def roots(node, acc=None):
    acc = [] if acc is None else acc
    if node.kind == "root":
        acc.append(node.archetype)
    for a in node.attrs:
        for c in a.children:
            if c.kind in ("complex", "root"):
                roots(c, acc)
    return acc


def check_cardinalities(node, path=""):
    """Each list's cardinality must admit what its children's occurrences allow."""
    problems = []
    for a in node.attrs:
        p = "%s/%s" % (path, a.name)
        if a.card is not None and a.existence[1] != 0:
            mins = sum(c.occ[0] for c in a.children)
            if a.card[1] is not STAR and mins > a.card[1]:
                problems.append("%s: children need %d, cardinality allows %s" % (p, mins, a.card[1]))
            maxes = [c.occ[1] for c in a.children]
            if a.card[0] > 0 and maxes and STAR not in maxes and sum(maxes) < a.card[0]:
                problems.append("%s: cardinality needs %d, children allow %d" % (p, a.card[0], sum(maxes)))
            if a.card[0] > 0 and not a.children:
                problems.append("%s: cardinality needs %d, no children" % (p, a.card[0]))
        for c in a.children:
            if c.kind in ("complex", "root"):
                problems += check_cardinalities(c, "%s[%s]" % (p, c.key()))
    return problems


# ---------------------------------------------------------------- OPT 1.4 XML writer

def _sub(parent, tag, text=None, **attrs):
    e = ET.SubElement(parent, tag, attrs)
    if text is not None:
        e.text = text
    return e


def _x_interval(parent, tag, lo, hi):
    e = _sub(parent, tag)
    _sub(e, "lower_included", "true")
    if hi is not STAR:
        _sub(e, "upper_included", "true")
    _sub(e, "lower_unbounded", "false")
    _sub(e, "upper_unbounded", "true" if hi is STAR else "false")
    _sub(e, "lower", str(lo))
    if hi is not STAR:
        _sub(e, "upper", str(hi))
    return e


def _x_obj(parent, o, tag="children"):
    if o.kind == "raw":
        e = copy.deepcopy(o.raw)
        e.tag = tag
        old = e.find("occurrences")
        new = _x_interval(ET.Element("x"), "occurrences", *o.occ)
        old[:] = list(new)
        parent.append(e)
        return
    xtype = {"complex": "C_COMPLEX_OBJECT", "root": "C_ARCHETYPE_ROOT", "slot": "ARCHETYPE_SLOT",
             "code_phrase": "C_CODE_PHRASE", "primitive": "C_PRIMITIVE_OBJECT"}.get(o.kind)
    if o.kind == "slot" and not o.open:
        raise ValueError("an open slot %s[%s] is left in the template" % (o.rm, o.node_id))
    e = _sub(parent, tag) if tag == "definition" else _sub(parent, tag, **{"xsi:type": xtype})
    _sub(e, "rm_type_name", o.rm)
    _x_interval(e, "occurrences", *o.occ)
    _sub(e, "node_id", o.node_id)
    if o.kind == "slot":
        for inc in o.include:
            _x_include(e, inc)
        return
    if o.kind == "code_phrase":
        tid = _sub(e, "terminology_id")
        _sub(tid, "value", o.terminology)
        for c in o.codes:
            _sub(e, "code_list", c)
        return
    if o.kind == "primitive":
        item = _sub(e, "item", **{"xsi:type": o.prim[0]})
        for k, v in o.prim[1]:
            _sub(item, k, v)
        return
    for a in o.attrs:
        _x_attr(e, a)
    if o.kind == "root":
        arch = o.archetype
        aid = _sub(e, "archetype_id")
        _sub(aid, "value", arch.archetype_id)
        for code in sorted(arch.terms, key=_code_key):
            text, desc, comment = arch.terms[code]
            td = _sub(e, "term_definitions", code=code)
            _sub(td, "items", text, id="text")
            _sub(td, "items", desc, id="description")
            if comment:
                _sub(td, "items", comment, id="comment")
        for tid in sorted(arch.bindings):
            tb = _sub(e, "term_bindings", terminology=tid)
            for code in sorted(arch.bindings[tid], key=_code_key):
                it = _sub(tb, "items", code=code)
                v = _sub(it, "value")
                t = _sub(v, "terminology_id")
                _sub(t, "value", tid)
                _sub(v, "code_string", arch.bindings[tid][code])


def _x_include(slot, pattern):
    """One include assertion of a slot, archetype_id/value matching pattern, as CKM writes it."""
    inc = _sub(slot, "includes")
    _sub(inc, "string_expression", "archetype_id/value matches {/%s/}" % pattern)
    ex = _sub(inc, "expression", **{"xsi:type": "EXPR_BINARY_OPERATOR"})
    _sub(ex, "type", "Boolean")
    _sub(ex, "operator", "2007")  # OPERATOR_KIND op_matches
    _sub(ex, "precedence_overridden", "false")
    left = _sub(ex, "left_operand", **{"xsi:type": "EXPR_LEAF"})
    _sub(left, "type", "String")
    _sub(left, "item", "archetype_id/value", **{"xsi:type": "xsd:string"})
    _sub(left, "reference_type", "attribute")
    right = _sub(ex, "right_operand", **{"xsi:type": "EXPR_LEAF"})
    _sub(right, "type", "C_STRING")
    _sub(_sub(right, "item", **{"xsi:type": "C_STRING"}), "pattern", pattern)
    _sub(right, "reference_type", "constraint")


def _has_slot(node):
    return any(c.kind == "slot" or (c.kind in ("complex", "root") and _has_slot(c))
               for a in node.attrs for c in a.children)


def _x_attr(parent, a):
    multiple = a.card is not None
    e = _sub(parent, "attributes", **{"xsi:type": "C_MULTIPLE_ATTRIBUTE" if multiple else "C_SINGLE_ATTRIBUTE"})
    _sub(e, "rm_attribute_name", a.name)
    _x_interval(e, "existence", *a.existence)
    for c in a.children:
        _x_obj(e, c)
    if multiple:
        lo, hi, ordered, unique = a.card
        card = _sub(e, "cardinality")
        _sub(card, "is_ordered", "true" if ordered else "false")
        _sub(card, "is_unique", "true" if unique else "false")
        _x_interval(card, "interval", lo, hi)


def write_opt(template_id, uid, concept, definition, meta, desc):
    ns = {"xmlns:xsi": XSI_NS}
    if _has_slot(definition):
        ns["xmlns:xsd"] = XSD_NS  # a slot's include assertion types an operand xsd:string
    ns["xmlns"] = OPENEHR_NS
    t = ET.Element("template", ns)
    lang = _sub(t, "language")
    _sub(_sub(lang, "terminology_id"), "value", "ISO_639-1")
    _sub(lang, "code_string", "en")
    d = _sub(t, "description")
    _sub(d, "original_author", meta["author"], id="Original Author")
    _sub(d, "lifecycle_state", meta["opt_lifecycle_state"])
    _sub(d, "other_details", meta["author"], id="Owner")
    _sub(d, "other_details", meta["copyright"], id="Copyright")
    _sub(d, "other_details", meta["licence"], id="Licence")
    _sub(d, "other_details", desc["references"], id="References")
    det = _sub(d, "details")
    dl = _sub(det, "language")
    _sub(_sub(dl, "terminology_id"), "value", "ISO_639-1")
    _sub(dl, "code_string", "en")
    _sub(det, "purpose", desc["purpose"])
    for k in desc["keywords"]:
        _sub(det, "keywords", k)
    _sub(det, "use", desc["use"])
    _sub(det, "misuse", desc["misuse"])
    _sub(det, "copyright", meta["copyright"])
    _sub(_sub(t, "uid"), "value", uid)
    _sub(_sub(t, "template_id"), "value", template_id)
    _sub(t, "concept", concept)
    _x_obj(t, definition, tag="definition")
    ET.indent(t, space="  ") if hasattr(ET, "indent") else _indent(t)
    body = ET.tostring(t, encoding="unicode", short_empty_elements=True)
    head = '<?xml version="1.0" encoding="utf-8"?>\n<!--%s-->\n' % meta["opt_comment"]
    return head + body + "\n"


def _indent(el, level=0):
    # ElementTree.indent arrived in Python 3.9; this is its fallback.
    pad = "\n" + "  " * level
    if len(el):
        if not el.text or not el.text.strip():
            el.text = pad + "  "
        for child in el:
            _indent(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = pad
    if level and (not el.tail or not el.tail.strip()):
        el.tail = pad
