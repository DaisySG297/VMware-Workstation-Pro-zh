# -*- coding: utf-8 -*-
"""生成严格等长替换方案：对每条消息尝试用精简中文压到 <= 原英文字节数，
生成最终 key->等长中文 映射，以及无法等长的保留英文清单。
"""
import json, re, os

EXE = r'C:\Program Files\VMware\VMware Workstation\vmnetcfg.exe'
MAP = r'C:\Users\Administrator\WorkBuddy\2026-10-28-14-44-08\vmnetcfg_zh_map.json'

whole = open(EXE, 'rb').read()
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
    entries.append({
        'key': key,
        'text_start': ts,
        'orig_len': null - ts,
        'orig_text': whole[ts:null].decode('utf-8', 'ignore'),
    })
    pos = i + 1

with open(MAP, 'r', encoding='utf-8') as f:
    m = json.load(f)
zh = m['mapping'] if isinstance(m, dict) and 'mapping' in m else m

def convert(s):
    s = re.sub(r'%(\d+)\$([sd])', r'%\2', s)
    s = s.replace('|0A', '\n').replace('|7C', '|')
    return s

# 精简映射：对超长条目提供更短译法（key -> 精简中文）
compact = {
    'msg.netcfg.common.editable.addNetwork.duplicate': '网络 %s 已存在。请选未使用的网络。',
    'msg.vmnetcfg.mainDlg.oneNAT': '无法改为 NAT 模式: 仅可设一个网络为 NAT。',
    'msg.vmnetcfg.mgr.assignIPFmt': '正在分配子网 IP: %s',
    'msg.vmnetcfg.mgr.checkAddRemove': '正在检查已添加或移除的网络',
    'msg.vmnetcfg.mgr.setNATFmt': '正在更新 %s:启用 NAT',
    'msg.vmnetcfg.mgr.setDHCPFmt': '正在更新 %s:设置 DHCP',
    'msg.vmnetcfg.mgr.setDHCPParamFmt': '正在更新 %s:设置 DHCP 参数',
    'msg.vmnetcfg.mgr.setNATParamFmt': '正在更新 %s:设置 NAT 参数',
    'msg.vmnetcfg.mgr.uninstallAdapterFmt': '正在更新 %s:卸载虚拟适配器',
    'msg.vmnetcfg.mgr.changeAddrFmt': '正在更新 %s:修改子网 IP',
    'msg.vmnetcfg.mgr.changeMaskFmt': '正在更新 %s:修改子网掩码',
    'msg.vmnetcfg.mgr.changeDisplayName': '正在更新 %s:修改名称',
    'msg.vmnetcfg.mgr.stopDHCP': '正在停止 DHCP 服务',
    'msg.vmnetcfg.mgr.stopNAT': '正在停止 NAT 服务',
    'msg.vmnetcfg.mgr.startNAT': '正在启动 NAT 服务',
    'msg.vmnetcfg.mgr.startDHCP': '正在启动 DHCP 服务',
    'msg.vmnetcfg.mgr.installAdapterFmt': '正在更新 %s:安装虚拟适配器',
    'msg.vmnetcfg.mgr.updateAdapters': '正在更新主机虚拟适配器',
    'msg.vmnetcfg.mgr.installAdapters': '正在安装网络适配器',
    'msg.vmnetcfg.mgr.removingNetwork.dhcp': '正在移除 %s:清除 DHCP 设置',
    'msg.vmnetcfg.mgr.removingNetwork.nat': '正在移除 %s:清除 NAT 设置',
    'msg.vmnetcfg.mgr.removingNetwork.port': '正在移除 %s:清除端口转发',
    'msg.vmnetcfg.mgr.removingNetwork.adapter': '正在移除 %s:清除适配器',
    'msg.vmnetcfg.mainDlg.btnAddNetwork': '添加网络(&E)',
    'msg.vmnetcfg.mainDlg.btnRemoveNetwork': '移除网络(&O)',
    'msg.vmnetcfg.mainDlg.btnRenameNetwork': '重命名网络(&W)',
    'msg.vmnetcfg.mainDlg.rdoBridge': '桥接(将虚拟机直接连接到外部网络)(&B)',
    'msg.vmnetcfg.mainDlg.cmbBridge': '已桥接至(&G)',
    'msg.vmnetcfg.mainDlg.rdoNAT': 'NAT(与虚拟机共享主机 IP)(&N)',
    'msg.vmnetcfg.mainDlg.natSettings': 'NAT 设置(&S)',
    'msg.vmnetcfg.mainDlg.useDHCP': '使用本地 DHCP 分配 IP 给虚拟机(&D)',
    'msg.vmnetcfg.mainDlg.dhcpSettings': 'DHCP 设置(&P)',
    'msg.vmnetcfg.mainDlg.subnetIP': '子网 IP(&I)',
    'msg.vmnetcfg.mainDlg.subnetMask': '子网掩码(&M)',
    'msg.vmnetcfg.mainDlg.btnRestoreDefault': '还原默认设置(&R)',
    'msg.vmnetcfg.mainDlg.btnImport': '导入(&T)',
    'msg.vmnetcfg.mainDlg.btnExport': '导出(&X)',
    'msg.vmnetcfg.mainDlg.btnApply': '应用(&A)',
    'msg.vmnetcfg.browserDlg.filter': '所有文件|*.*||',
    'msg.vmnetcfg.mainDlg.netTypeBridged': '桥接',
    'msg.vmnetcfg.mainDlg.netTypeHostOnly': '仅主机',
    'msg.vmnetcfg.mainDlg.netTypeCustom': '自定义',
    'msg.vmnetcfg.mainDlg.hasDHCP': '已启用',
    'msg.vmnetcfg.mainDlg.hostAdapterNameFmt': '主机虚拟适配器: %s',
    'msg.vmnetcfg.mainDlg.ipConflictFmt': '%s 和 %s 子网 IP 相同。\n请为各子网输入不同的 IP。',
    'msg.vmnetcfg.natDlg.subnetMask': '子网掩码',
    'msg.vmnetcfg.natDlg.gatewayIP': '网关 IP(&G)',
    'msg.vmnetcfg.natDlg.btnAdd': '添加(&A)',
    'msg.vmnetcfg.natDlg.btnRemove': '移除(&R)',
    'msg.vmnetcfg.natDlg.allowActiveFTP': '允许活动 FTP(&T)',
    'msg.vmnetcfg.natDlg.UDPTimeout': 'UDP 超时(秒)(&U)',
    'msg.vmnetcfg.natDlg.configPort': '配置端口(&C)',
    'msg.vmnetcfg.natDlg.enableIPv6': '启用 IPv6(&E)',
    'msg.vmnetcfg.natDlg.ipv6Prefix': 'IPv6 前缀(&6)',
    'msg.vmnetcfg.natDlg.btnDNSSettings': 'DNS 设置(&D)',
    'msg.vmnetcfg.natDlg.btnNetBIOSSettings': 'NetBIOS 设置(&N)',
    'msg.vmnetcfg.natDlg.hostPort': '主机端口',
    'msg.vmnetcfg.natDlg.ipportFmt': '%s:%d',
    'msg.vmnetcfg.mapPortDlg.title': '映射传入端口',
    'msg.vmnetcfg.mapPortDlg.hostPort': '主机端口(&H)',
    'msg.vmnetcfg.mapPortDlg.type': '类型',
    'msg.vmnetcfg.mapPortDlg.rdoTCP': 'TCP(&T)',
    'msg.vmnetcfg.mapPortDlg.rdoUDP': 'UDP(&U)',
    'msg.vmnetcfg.mapPortDlg.duplicateEntry': '已存在相同类型和主机端口的条目。\n请用不同的端口或类型。',
    'msg.vmnetcfg.dnsDlg.preferredDNS': '首选 DNS(&P)',
    'msg.vmnetcfg.dnsDlg.autoDetect': '自动检测可用的 DNS(&A)',
    'msg.vmnetcfg.dnsDlg.policy': '策略(&Y)',
    'msg.vmnetcfg.dnsDlg.timeout': '超时(秒)(&T)',
    'msg.vmnetcfg.dnsDlg.retries': '重试次数(&R)',
    'msg.vmnetcfg.dnsDlg.dnsServerGroup': 'DNS 服务器',
    'msg.vmnetcfg.dnsDlg.policyOrder': '顺序',
    'msg.vmnetcfg.dnsDlg.policyBurst': '迸发',
    'msg.vmnetcfg.dhcpDlg.subnetMask': '子网掩码',
    'msg.vmnetcfg.dhcpDlg.endIP': '结束 IP(&E)',
    'msg.vmnetcfg.dhcpDlg.hours': '小时',
    'msg.vmnetcfg.dhcpDlg.defaultLeaseTime': '默认租用时间(&D)',
    'msg.vmnetcfg.dhcpDlg.maxLeaseTime': '最长租用时间(&M)',
    'msg.vmnetcfg.netbiosDlg.nbnsTimeout': 'NBNS 超时(秒)(&T)',
    'msg.vmnetcfg.netbiosDlg.nbnsRetries': 'NBNS 重试次数(&R)',
    'msg.vmnetcfg.netbiosDlg.nbdsTimeout': 'NBDS 超时(秒)(&S)',
    'msg.vmnetcfg.addNetworkDlg.desc': '选择要添加的网络(&S)',
    'msg.vmnetcfg.renameNetworkDlg.errorExistName': '无法使用现有的名称',
    'msg.vmnetcfg.renameNetworkDlg.errorName': '不能使用以“VMnet”开头的名称(默认名除外)',
    'msg.vmnetcfg.util.spinEditOutOfRangeFmt': '输入 %d 到 %d 之间的值',
}

# 生成最终方案
final = {}  # key -> (final_zh_text_or_None 表示保留英文)
kept_en = []
for e in entries:
    k = e['key']
    if k not in zh:
        continue
    base = convert(zh[k])
    # 尝试 1: 精简映射
    cand = compact.get(k, base)
    # 尝试 2: 若还超长，尝试去掉加速键 & 和空格
    def try_len(s):
        return len(s.encode('utf-8'))
    candidates = [cand]
    if try_len(cand) > e['orig_len']:
        c2 = cand.replace('(&', '(').replace(')','').replace('&','')
        candidates.append(c2)
    chosen = None
    for c in candidates:
        if try_len(c) <= e['orig_len']:
            chosen = c
            break
    if chosen is not None:
        final[k] = chosen
    else:
        kept_en.append((k, e['orig_len'], cand, try_len(cand)))

print('=== 最终等长方案 ===')
print('总消息: %d' % len(entries))
print('可等长汉化: %d' % len(final))
print('无法等长(保留英文): %d' % len(kept_en))
print()
print('=== 保留英文的条目 ===')
for k, olen, cand, clen in kept_en:
    print('  %s  %d->%d  中文尝试:%s' % (k, olen, clen, cand))

# 保存最终方案
out = {'final': final, 'kept_en': [k for k,_,_,_ in kept_en]}
with open(r'C:\Users\Administrator\WorkBuddy\2026-10-28-14-44-08\equal_length_final.json', 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print()
print('已保存方案到 equal_length_final.json')
