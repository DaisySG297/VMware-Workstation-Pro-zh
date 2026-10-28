# -*- coding: utf-8 -*-
"""最终增强汉化：在原等长方案基础上，对 26 条保留英文的短词，
借用纯 \x00 padding 空间安全写入中文。原则：
1. 中文写入后，末尾必须仍有 >=1 个 \x00 作为消息终止；
2. 下一条消息 marker 的绝对偏移不变（不覆盖任何活数据）；
3. 文件大小完全不变。
"""
import json

EXE = r'C:\Users\Administrator\WorkBuddy\2026-10-28-14-44-08\vmware-zh_CN-backup\vmnetcfg.exe.orig'
PLAN = r'C:\Users\Administrator\WorkBuddy\2026-10-28-14-44-08\equal_length_final.json'
OUT = r'C:\Users\Administrator\WorkBuddy\2026-10-28-14-44-08\vmnetcfg_zh_equal.exe'

whole = bytearray(open(EXE, 'rb').read())
orig_size = len(whole)
marker = b'@&!*@*@('

# 解析消息表
entries = []
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
    entries.append({'key': key, 'start': i, 'ts': ts, 'end': null})
    pos = i + 1
entries.sort(key=lambda e: e['start'])
by = {e['key']: e for e in entries}

# 1. 先应用原等长方案（195 条）
plan = json.load(open(PLAN, 'r', encoding='utf-8'))
final = plan['final']
applied = 0
for k, zh in final.items():
    if k not in by:
        continue
    e = by[k]
    z = zh.encode('utf-8')
    olen = e['end'] - e['ts']
    if len(z) > olen:
        print('!! 超长跳过:', k)
        continue
    whole[e['ts']:e['end']] = z + b'\x00' * (olen - len(z))
    applied += 1

# 2. 处理 26 条保留英文的短词（借用 padding）
# 每条：计算 text 起点到下一条 marker 前的最大可用空间（含 padding），
# 中文写入后末尾留 1 个 \x00。只写能完整容纳的中文。
zh_short = {
    'msg.vmnetcfg.mainDlg.name': '名称',
    'msg.vmnetcfg.mainDlg.type': '类型',
    'msg.vmnetcfg.mainDlg.btnOK': '确定',
    'msg.vmnetcfg.mainDlg.btnHelp': '帮助',
    'msg.vmnetcfg.mainDlg.netTypeCustom': '自定义',
    'msg.vmnetcfg.natDlg.btnOK': '确定',
    'msg.vmnetcfg.natDlg.btnHelp': '帮助',
    'msg.vmnetcfg.natDlg.hostPort': '主端口',
    'msg.vmnetcfg.natDlg.type': '类型',
    'msg.vmnetcfg.mapPortDlg.hostPort': '主机端口',
    'msg.vmnetcfg.mapPortDlg.type': '类型',
    'msg.vmnetcfg.mapPortDlg.btnOK': '确定',
    'msg.vmnetcfg.mapPortDlg.btnHelp': '帮助',
    'msg.vmnetcfg.dnsDlg.dnsServerGroup': 'DNS服务器',
    'msg.vmnetcfg.dnsDlg.btnOK': '确定',
    'msg.vmnetcfg.dnsDlg.btnHelp': '帮助',
    'msg.vmnetcfg.dnsDlg.policyOrder': '顺序',
    'msg.vmnetcfg.dnsDlg.policyBurst': '迸发',
    'msg.vmnetcfg.dhcpDlg.btnOK': '确定',
    'msg.vmnetcfg.dhcpDlg.btnHelp': '帮助',
    'msg.vmnetcfg.netbiosDlg.btnOK': '确定',
    'msg.vmnetcfg.netbiosDlg.btnHelp': '帮助',
    'msg.vmnetcfg.addNetworkDlg.btnOK': '确定',
    'msg.vmnetcfg.addNetworkDlg.btnHelp': '帮助',
    'msg.vmnetcfg.renameNetworkDlg.btnOK': '确定',
}

# 找每条的下一条 marker 偏移
idx_map = {e['key']: i for i, e in enumerate(entries)}
short_ok = 0
short_fail = []
for k, zh in zh_short.items():
    if k not in by:
        continue
    e = by[k]
    i = idx_map[k]
    next_start = entries[i + 1]['start'] if i + 1 < len(entries) else len(whole)
    # 可用空间 = 从 text 起点到下一 marker 前（保留 1 字节 \x00 终止）
    max_space = next_start - e['ts'] - 1
    z = zh.encode('utf-8')
    if len(z) <= max_space:
        # 写入中文 + \x00 填充到 next_start
        whole[e['ts']:next_start] = z + b'\x00' * (next_start - e['ts'] - len(z))
        short_ok += 1
    else:
        short_fail.append((k, zh, len(z), max_space))

# 3. 对 btnOK 类差 1-2 字节的，用 1 字中文 + 保留（物理极限）
#    单字中文 = 3B，btnOK 空间 5B 可容纳 1 字 + 2 padding，但 1 字不像按钮，故保留英文。
#    这里对 natDlg.hostPort 已用"主端口"9B 解决。其余 btnOK/btnHelp 若仍失败，保留英文。

assert len(whole) == orig_size, '文件大小改变！拒绝保存'
open(OUT, 'wb').write(whole)

print('=== 最终增强汉化完成 ===')
print('原等长方案应用: %d 条' % applied)
print('借用 padding 短词汉化: %d / %d 条' % (short_ok, len(zh_short)))
print('仍无法汉化(物理极限): %d 条' % len(short_fail))
for k, zh, zl, ms in short_fail:
    print('  %s: 中文"%s"(%dB) > 空间(%dB)' % (k, zh, zl, ms))
print('文件大小不变: %d 字节' % orig_size)
print('输出: %s' % OUT)
