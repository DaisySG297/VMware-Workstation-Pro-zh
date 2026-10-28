# -*- coding: utf-8 -*-
"""Map 26H1 vmnetcfg.exe message keys to old 17.6.4 zh_CN translations."""
import pefile, re, io

# 1. parse 26H1 vmnetcfg.exe message table keys
P = r"C:\Program Files\VMware\VMware Workstation\vmnetcfg.exe"
pe = pefile.PE(P, fast_load=False)
whole = open(P, "rb").read()
marker = b"@&!*@*@("

keys_26 = []
pos = 0
while True:
    i = whole.find(marker, pos)
    if i < 0:
        break
    endkey = whole.find(b")", i, i + 200)
    if endkey < 0:
        break
    key = whole[i + len(marker):endkey].decode("ascii", "ignore")
    keys_26.append(key)
    pos = i + 1

print("26H1 vmnetcfg.exe keys: %d" % len(keys_26))

# 2. parse old 17.6.4 zh_CN vmsg
OLD = r"C:\Users\Administrator\WorkBuddy\2026-10-28-14-44-08\vmware-zh_CN-backup\vmware.vmsg.orig"
old_map = {}
pat = re.compile(r'^(\s*msg\.[^\s=]+)\s*=\s*"(.*)"\s*$', re.M)
with io.open(OLD, "r", encoding="utf-8", errors="replace") as f:
    for m in pat.finditer(f.read()):
        old_map[m.group(1).strip()] = m.group(2)

print("old 17.6.4 zh_CN vmsg keys: %d" % len(old_map))

# 3. map coverage
covered = 0
missing = []
for k in keys_26:
    if k in old_map:
        covered += 1
    else:
        missing.append(k)

print("covered: %d / %d" % (covered, len(keys_26)))
print("missing: %d" % len(missing))
for m in missing:
    print("  MISSING:", m)

# 4. save the mapping (key -> old translation) for later use
import json
mapping = {k: old_map[k] for k in keys_26 if k in old_map}
with io.open(r"C:\Users\Administrator\WorkBuddy\2026-10-28-14-44-08\vmnetcfg_zh_map.json", "w", encoding="utf-8") as f:
    json.dump({"keys_26": keys_26, "mapping": mapping, "missing": missing}, f, ensure_ascii=False, indent=1)
print("saved mapping to vmnetcfg_zh_map.json")
