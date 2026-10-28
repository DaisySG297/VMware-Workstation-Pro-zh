# -*- coding: utf-8 -*-
"""应用严格等长替换：逐条原地覆盖中文（<= 原字节长度，\x00 补齐），
不改变文件大小、不改变任何偏移。这是零崩溃风险的安全方案。
"""
import json, os

EXE = r'C:\Users\Administrator\WorkBuddy\2026-10-28-14-44-08\vmware-zh_CN-backup\vmnetcfg.exe.orig'
PLAN = r'C:\Users\Administrator\WorkBuddy\2026-10-28-14-44-08\equal_length_final.json'
OUT = r'C:\Users\Administrator\WorkBuddy\2026-10-28-14-44-08\vmnetcfg_zh_equal.exe'

with open(PLAN, 'r', encoding='utf-8') as f:
    plan = json.load(f)
final = plan['final']

whole = bytearray(open(EXE, 'rb').read())
orig_size = len(whole)
marker = b'@&!*@*@('

# 重新解析消息表，拿到每条 key 的 text_start 和 orig_len
entries = {}
pos = 0
while True:
    i = whole.find(marker, pos)
    if i < 0:
        break
    ek = whole.find(b')', i, i + 300)
    if ek < 0:
        break
    key = whole[i + len(marker):ek].decode('ascii', 'ignore')
    ts = ek + 1
    null = whole.find(b'\x00', ts, ts + 4096)
    if null < 0:
        break
    entries[key] = (ts, null - ts)
    pos = i + 1

applied = 0
for k, zh_text in final.items():
    if k not in entries:
        continue
    ts, olen = entries[k]
    zbytes = zh_text.encode('utf-8')
    if len(zbytes) > olen:
        print('!! 跳过超长(不应发生): %s' % k)
        continue
    # 原地写入：中文 + 补 \x00
    whole[ts:ts + olen] = zbytes + b'\x00' * (olen - len(zbytes))
    applied += 1

# 校验文件大小不变
assert len(whole) == orig_size, '文件大小变了！拒绝保存'
open(OUT, 'wb').write(whole)

print('=== 等长替换完成 ===')
print('应用条目: %d / %d' % (applied, len(final)))
print('原文件大小: %d 字节' % orig_size)
print('新文件大小: %d 字节 (必须相等)' % len(whole))
print('输出: %s' % OUT)
