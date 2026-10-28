# -*- coding: utf-8 -*-
"""Convert old zh translations to 26H1 format, validate placeholder fidelity, emit final map."""
import pefile, re, io, json

P = r"C:\Program Files\VMware\VMware Workstation\vmnetcfg.exe"
pe = pefile.PE(P, fast_load=False)
whole = open(P, "rb").read()
marker = b"@&!*@*@("

# parse 26H1 entries in file order (key, text, key_start, text_start, text_end)
entries = []
pos = 0
while True:
    i = whole.find(marker, pos)
    if i < 0:
        break
    ek = whole.find(b")", i, i + 200)
    if ek < 0:
        break
    key = whole[i + len(marker):ek].decode("ascii", "ignore")
    tstart = ek + 1
    nx = whole.find(b"\x00", tstart, tstart + 600)
    if nx < 0:
        break
    text = whole[tstart:nx].decode("utf-8", "ignore")
    entries.append({"key": key, "marker_off": i, "key_start": i, "text_start": tstart,
                    "text_end": nx, "en_text": text})
    pos = i + 1

print("26H1 entries: %d" % len(entries))

# load old zh mapping
d = json.load(open(r"C:\Users\Administrator\WorkBuddy\2026-10-28-14-44-08\vmnetcfg_zh_map.json", encoding="utf-8"))
old = d["mapping"]

def convert_placeholders(s):
    # %1$s -> %s, %2$d -> %d (remove positional index)
    s = re.sub(r"%\d+\$(?=[sd])", "%", s)
    # |0A -> \n
    s = s.replace("|0A", "\n")
    return s

# Build final list with converted Chinese
def placeholder_signature(s):
    """Extract ordered list of placeholder specifiers to verify fidelity."""
    return re.findall(r"%[sd]", s)

problems = []
final = []
for e in entries:
    k = e["key"]
    en = e["en_text"]
    if k not in old:
        problems.append(("MISSING", k))
        zh = en  # fallback to English
    else:
        zh = convert_placeholders(old[k])
    # verify placeholder fidelity vs english
    en_sig = placeholder_signature(en)
    zh_sig = placeholder_signature(zh)
    if en_sig != zh_sig:
        problems.append(("PLACEHOLDER", k, en_sig, zh_sig, zh))
    final.append({"key": k, "zh_text": zh, **e})

print("problems: %d" % len(problems))
for p in problems:
    print("  ", p)

# summary of length delta
delta = 0
for f in final:
    delta += len(f["zh_text"].encode("utf-8")) - len(f["en_text"].encode("utf-8"))
print("total utf8 byte delta (zh - en): %d" % delta)

# save final list
with io.open(r"C:\Users\Administrator\WorkBuddy\2026-10-28-14-44-08\vmnetcfg_final.json", "w", encoding="utf-8") as f:
    json.dump(final, f, ensure_ascii=False, indent=1)
print("saved final list to vmnetcfg_final.json")
