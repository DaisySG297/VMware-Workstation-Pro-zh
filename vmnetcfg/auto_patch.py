# -*- coding: utf-8 -*-
"""
VMware Workstation Pro 26H1「虚拟网络编辑器」(vmnetcfg.exe) 一键汉化工具

用法：
    python auto_patch.py              # 自动定位并汉化已安装的 vmnetcfg.exe
    python auto_patch.py <exe路径>     # 汉化指定路径的 vmnetcfg.exe
    python auto_patch.py --restore    # 从自动备份恢复原版

原理：等长替换 + 借用 padding，不改变文件大小与任何偏移，零崩溃风险。
"""
import os
import sys
import string
import shutil

# 让控制台输出在中文 Windows 上正确显示中文（GBK 代码页）
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='gbk', errors='replace')
        sys.stderr.reconfigure(encoding='gbk', errors='replace')
    except Exception:
        pass

# ==================== 内嵌汉化方案 ====================
# 1) 等长替换方案（195 条，中文 UTF-8 <= 原英文字节，原地覆盖补 \x00）
EQUAL_LENGTH = {
    "msg.netcfg.common.bridge.setAuto.notvmnet0": "只能在 vmnet0 上启用自动桥接功能。",
    "msg.netcfg.common.bridge.addAutoAdapter.alreadyBridged": "无法自动桥接至主机适配器 %s。%s 已与其桥接。",
    "msg.netcfg.common.bridge.setAdapter.alreadyBridged": "无法桥接至主机适配器 %s。%s 已与其桥接。",
    "msg.netcfg.common.editable.addNetwork.duplicate": "网络 %s 已存在。请选未使用的网络。",
    "msg.netcfg.common.editable.addNetwork.noBridgedAdapters": "无法添加桥接网络: 没有未桥接的主机网络适配器。",
    "msg.netcfg.common.network.setType.noBridgedAdapters": "无法将网络更改为桥接状态: 没有未桥接的主机网络适配器。",
    "msg.vmnetcfg.mainDlg.oneNAT": "无法改为 NAT 模式: 仅可设一个网络为 NAT。",
    "msg.vmnetcfg.mgr.loading": "正在加载网络配置。",
    "msg.vmnetcfg.mgr.assignIPFmt": "正在分配子网 IP: %s",
    "msg.vmnetcfg.mgr.checkAddRemove": "正在检查已添加或移除的网络",
    "msg.vmnetcfg.mgr.checkBridge": "正在检查桥接配置。",
    "msg.vmnetcfg.mgr.setDHCPFmt": "正在更新 %s:设置 DHCP",
    "msg.vmnetcfg.mgr.setDHCPParamFmt": "正在更新 %s:设置 DHCP 参数",
    "msg.vmnetcfg.mgr.setNATParamFmt": "正在更新 %s:设置 NAT 参数",
    "msg.vmnetcfg.mgr.uninstallAdapterFmt": "正在更新 %s:卸载虚拟适配器",
    "msg.vmnetcfg.mgr.changeDisplayName": "正在更新 %s:修改名称",
    "msg.vmnetcfg.mgr.installAdapterFmt": "正在更新 %s:安装虚拟适配器",
    "msg.vmnetcfg.mgr.updateVMwareUI": "正在广播网络设置。",
    "msg.vmnetcfg.mgr.uninstallingNetworkComponents": "正在卸载网络组件。",
    "msg.vmnetcfg.mgr.installingNetworkComponents": "正在安装网络组件。",
    "msg.vmnetcfg.mgr.installServices": "正在安装网络服务。",
    "msg.vmnetcfg.mgr.installAdapters": "正在安装网络适配器",
    "msg.vmnetcfg.mgr.importDatabase": "从文件导入网络配置。",
    "msg.vmnetcfg.mgr.applyImportedDatabase": "应用导入的网络配置。",
    "msg.vmnetcfg.mgr.exportDatabase": "将网络配置导出到文件。",
    "msg.vmnetcfg.mgr.removingNetwork.dhcp": "正在移除 %s:清除 DHCP 设置",
    "msg.vmnetcfg.mgr.removingNetwork.nat": "正在移除 %s:清除 NAT 设置",
    "msg.vmnetcfg.mgr.removingNetwork.port": "正在移除 %s:清除端口转发",
    "msg.vmnetcfg.mgr.removingNetwork.adapter": "正在移除 %s:清除适配器",
    "msg.vmnetcfg.mainDlg.externalConnection": "外部连接",
    "msg.vmnetcfg.mainDlg.hostConnection": "主机连接",
    "msg.vmnetcfg.mainDlg.dhcp": "DHCP",
    "msg.vmnetcfg.mainDlg.subnetAddress": "子网地址",
    "msg.vmnetcfg.mainDlg.appTitle": "虚拟网络编辑器",
    "msg.vmnetcfg.mainDlg.btnAddNetwork": "添加网络(E",
    "msg.vmnetcfg.mainDlg.btnRemoveNetwork": "移除网络(O",
    "msg.vmnetcfg.mainDlg.btnRenameNetwork": "重命名网络(W",
    "msg.vmnetcfg.mainDlg.title": "VMnet 信息",
    "msg.vmnetcfg.mainDlg.rdoBridge": "桥接(将虚拟机直接连接到外部网络)(&B)",
    "msg.vmnetcfg.mainDlg.autoBridgeSettings": "自动设置(&U)...",
    "msg.vmnetcfg.mainDlg.rdoNAT": "NAT(与虚拟机共享主机 IP)(&N)",
    "msg.vmnetcfg.mainDlg.natSettings": "NAT 设置(&S)",
    "msg.vmnetcfg.mainDlg.rdoHostOnly": "仅主机模式(在专用网络内连接虚拟机)(&H)",
    "msg.vmnetcfg.mainDlg.hostAdapter": "将主机虚拟适配器连接到此网络(&V)",
    "msg.vmnetcfg.mainDlg.useDHCP": "使用本地 DHCP 分配 IP 给虚拟机(&D)",
    "msg.vmnetcfg.mainDlg.dhcpSettings": "DHCP 设置(&P)",
    "msg.vmnetcfg.mainDlg.subnetIP": "子网 IP(I",
    "msg.vmnetcfg.mainDlg.txtAdminPermission": "需要具备管理员特权才能修改网络配置。",
    "msg.vmnetcfg.mainDlg.changeSettings": "更改设置(&C)",
    "msg.vmnetcfg.mainDlg.btnImport": "导入(&T)",
    "msg.vmnetcfg.mainDlg.btnExport": "导出(&X)",
    "msg.vmnetcfg.mainDlg.btnCancel": "取消",
    "msg.vmnetcfg.mainDlg.maximumNetworkExceeded": "您已创建了最大数量的虚拟网络。必须先移除一个网络，才能创建新网络。",
    "msg.vmnetcfg.mainDlg.jobTitleOnOK": "正在保存网络配置",
    "msg.vmnetcfg.mainDlg.jobTitleOnApply": "正在应用网络配置",
    "msg.vmnetcfg.mainDlg.restoreWithVMRunning": "虚拟机开机后无法还原虚拟网络设置。\n请先关闭所有虚拟机。",
    "msg.vmnetcfg.mainDlg.restoreWarning": "您的所有自定义网络设置均将丢失。\n确实要恢复到默认网络设置吗?",
    "msg.vmnetcfg.mainDlg.jobTitleOnRestore": "正在还原网络配置",
    "msg.vmnetcfg.mainDlg.pendingChanges": "有更改挂起时，无法导出虚拟网络设置。\n请先应用更改。",
    "msg.vmnetcfg.mainDlg.importWithVMRunning": "虚拟机打开电源后无法导入虚拟网络设置。\n请先关闭所有虚拟机。",
    "msg.vmnetcfg.browserDlg.title": "浏览配置文件",
    "msg.vmnetcfg.mainDlg.jobTitleImport": "导入网络配置",
    "msg.vmnetcfg.mainDlg.jobTitleExport": "导出网络配置",
    "msg.vmnetcfg.mainDlg.jobTitleOnCheckIP": "正在初始化虚拟网络",
    "msg.vmnetcfg.mainDlg.jobTitleOnReload": "正在初始化虚拟网络",
    "msg.vmnetcfg.mainDlg.netTypeBridged": "桥接",
    "msg.vmnetcfg.mainDlg.netTypeNAT": "NAT",
    "msg.vmnetcfg.mainDlg.netTypeHostOnly": "仅主机",
    "msg.vmnetcfg.mainDlg.optNoeExternConn": "-",
    "msg.vmnetcfg.mainDlg.optNoHostConn": "-",
    "msg.vmnetcfg.mainDlg.optNoDHCP": "-",
    "msg.vmnetcfg.mainDlg.optNoAddr": "-",
    "msg.vmnetcfg.mainDlg.hasVirtualAdapter": "已连接",
    "msg.vmnetcfg.mainDlg.hasNAT": "NAT",
    "msg.vmnetcfg.mainDlg.optAutoBridge": "自动桥接",
    "msg.vmnetcfg.mainDlg.defaultHostAdapterName": "VMware 网络适配器 VMnet%d",
    "msg.vmnetcfg.mainDlg.hostAdapterNameFmt": "主机虚拟适配器: %s",
    "msg.vmnetcfg.mainDlg.optionAutomatic": "自动",
    "msg.vmnetcfg.mainDlg.invalidIPMaskFmt": "%s 设置中出现错误。\n%s",
    "msg.vmnetcfg.mainDlg.ipConflictFmt": "%s 和 %s 子网 IP 相同。\n请为各子网输入不同的 IP。",
    "msg.vmnetcfg.natDlg.title": "NAT 设置",
    "msg.vmnetcfg.natDlg.network": "网络:",
    "msg.vmnetcfg.natDlg.subnetIP": "子网 IP:",
    "msg.vmnetcfg.natDlg.subnetMask": "子网掩码",
    "msg.vmnetcfg.natDlg.gatewayIP": "网关 IP(G",
    "msg.vmnetcfg.natDlg.portForwarding": "端口转发(&F)",
    "msg.vmnetcfg.natDlg.btnProperties": "属性(&P)",
    "msg.vmnetcfg.natDlg.advanced": "高级",
    "msg.vmnetcfg.natDlg.allowOUI": "允许任何组织唯一标识符(&O)",
    "msg.vmnetcfg.natDlg.UDPTimeout": "UDP 超时(秒)(&U)",
    "msg.vmnetcfg.natDlg.ipv6Prefix": "IPv6 前缀(6",
    "msg.vmnetcfg.natDlg.btnDNSSettings": "DNS 设置(&D)",
    "msg.vmnetcfg.natDlg.btnNetBIOSSettings": "NetBIOS 设置(&N)",
    "msg.vmnetcfg.natDlg.btnCancel": "取消",
    "msg.vmnetcfg.natDlg.vmIP": "虚拟机 IP 地址",
    "msg.vmnetcfg.natDlg.desc": "描述",
    "msg.vmnetcfg.natDlg.tcp": "TCP",
    "msg.vmnetcfg.natDlg.udp": "UDP",
    "msg.vmnetcfg.natDlg.ipportFmt": "%s:%d",
    "msg.vmnetcfg.natDlg.gatewayIPErrorFmt": "网关 IP 地址无效。\n%s",
    "msg.vmnetcfg.natDlg.udpTimeoutErrorFmt": "UDP 超时值无效。\n%s",
    "msg.vmnetcfg.natDlg.configPortErrorFmt": "配置端口无效。\n%s",
    "msg.vmnetcfg.mapPortDlg.ipAddr": "虚拟机 IP 地址(&A):",
    "msg.vmnetcfg.mapPortDlg.port": "虚拟机端口(&P):",
    "msg.vmnetcfg.mapPortDlg.desc": "描述(&D):",
    "msg.vmnetcfg.mapPortDlg.btnCancel": "取消",
    "msg.vmnetcfg.mapPortDlg.hostPortErrorFmt": "主机端口无效。\n%s",
    "msg.vmnetcfg.mapPortDlg.zeroIP": "虚拟机 IP 地址不能为零。",
    "msg.vmnetcfg.mapPortDlg.virtualPortErrorFmt": "虚拟机端口无效。\n%s",
    "msg.vmnetcfg.mapPortDlg.duplicateEntry": "已存在相同类型和主机端口的条目。\n请用不同的端口或类型。",
    "msg.vmnetcfg.dnsDlg.preferredDNS": "首选 DNS(&P)",
    "msg.vmnetcfg.dnsDlg.alternateDNS": "备用 DNS 服务器 &%d:",
    "msg.vmnetcfg.dnsDlg.title": "域名服务器 (DNS)",
    "msg.vmnetcfg.dnsDlg.autoDetect": "自动检测可用的 DNS(&A)",
    "msg.vmnetcfg.dnsDlg.policy": "策略(Y",
    "msg.vmnetcfg.dnsDlg.timeout": "超时(秒)(&T)",
    "msg.vmnetcfg.dnsDlg.btnCancel": "取消",
    "msg.vmnetcfg.dnsDlg.policyRotate": "轮换",
    "msg.vmnetcfg.dnsDlg.maxEmptyDNS": "必须启用自动检测功能或必须提供 DNS 设置。",
    "msg.vmnetcfg.dnsDlg.timeoutErrorFmt": "超时值无效。\n%s",
    "msg.vmnetcfg.dnsDlg.retriesErrorFmt": "重试次数无效。\n%s",
    "msg.vmnetcfg.dhcpDlg.title": "DHCP 设置",
    "msg.vmnetcfg.dhcpDlg.network": "网络:",
    "msg.vmnetcfg.dhcpDlg.subnetIP": "子网 IP:",
    "msg.vmnetcfg.dhcpDlg.subnetMask": "子网掩码",
    "msg.vmnetcfg.dhcpDlg.startIP": "起始 IP 地址(&S):",
    "msg.vmnetcfg.dhcpDlg.endIP": "结束 IP(&E)",
    "msg.vmnetcfg.dhcpDlg.broadcastIP": "广播地址:",
    "msg.vmnetcfg.dhcpDlg.days": "天:",
    "msg.vmnetcfg.dhcpDlg.hours": "小时",
    "msg.vmnetcfg.dhcpDlg.minutes": "分钟:",
    "msg.vmnetcfg.dhcpDlg.defaultLeaseTime": "默认租用时间(D",
    "msg.vmnetcfg.dhcpDlg.btnCancel": "取消",
    "msg.vmnetcfg.dhcpDlg.startIPErrorFmt": "起始 IP 地址无效。\n%s",
    "msg.vmnetcfg.dhcpDlg.endIPErrorFmt": "结束 IP 地址无效。\n%s",
    "msg.vmnetcfg.dhcpDlg.wrongIPOrder": "起始和结束 IP 地址指定的范围无效。\n请输入有效的 IP 地址。\n",
    "msg.vmnetcfg.dhcpDlg.defaultLeaseTimeDayErrorFmt": "无效的默认租用时间天数。\n%s",
    "msg.vmnetcfg.dhcpDlg.defaultLeaseTimeHourErrorFmt": "无效的默认租用时间小时数。\n%s",
    "msg.vmnetcfg.dhcpDlg.defaultLeaseTimeMinuteErrorFmt": "无效的默认租用时间分钟数。\n%s",
    "msg.vmnetcfg.dhcpDlg.maxLeaseTimeDayErrorFmt": "无效的最长租用时间天数。\n%s",
    "msg.vmnetcfg.dhcpDlg.maxLeaseTimeHourErrorFmt": "无效的最长租用时间小时数。\n%s",
    "msg.vmnetcfg.dhcpDlg.maxLeaseTimeMinuteErrorFmt": "无效的最长租用时间分钟数。\n%s",
    "msg.vmnetcfg.dhcpDlg.defaultLeaseGreaterThanMaxLeaseError": "默认租用时间大于最大租用时间。\n请使用正确的时间长度更新租用时间。\n",
    "msg.vmnetcfg.netbiosDlg.title": "NetBIOS 设置",
    "msg.vmnetcfg.netbiosDlg.nbnsTimeout": "NBNS 超时(秒)(&T)",
    "msg.vmnetcfg.netbiosDlg.nbdsTimeout": "NBDS 超时(秒)(&S)",
    "msg.vmnetcfg.netbiosDlg.btnCancel": "取消",
    "msg.vmnetcfg.netbiosDlg.NBNSTimeoutErrorFmt": "NBNS 超时值无效。\n%s",
    "msg.vmnetcfg.netbiosDlg.NBNSRetriesErrorFmt": "NBNS 重试次数无效。\n%s",
    "msg.vmnetcfg.netbiosDlg.NBDSTimeoutErrorFmt": "NBDS 超时值无效。\n%s",
    "msg.vmnetcfg.addNetworkDlg.title": "添加虚拟网络",
    "msg.vmnetcfg.addNetworkDlg.btnCancel": "取消",
    "msg.vmnetcfg.addNetworkDlg.vmnetNameFmt": "VMnet%d",
    "msg.vmnetcfg.renameNetworkDlg.title": "重命名虚拟网络",
    "msg.vmnetcfg.renameNetworkDlg.btnCancel": "取消",
    "msg.vmnetcfg.renameNetworkDlg.btnDefault": "默认",
    "msg.vmnetcfg.renameNetworkDlg.errorTitle": "名称无效",
    "msg.vmnetcfg.renameNetworkDlg.errorExistName": "无法使用现有的名称",
    "msg.vmnetcfg.renameNetworkDlg.errorName": "不能使用以“VMnet”开头的名称(默认名除外)",
    "msg.vmnetcfg.renameNetworkDlg.errorLength": "名称太长。",
    "msg.vmnetcfg.util.questionTitle": "虚拟网络编辑器",
    "msg.vmnetcfg.util.errorTitle": "虚拟网络编辑器",
    "msg.vmnetcfg.util.spinEditValueNotNumber": "输入一个数值。",
    "msg.vmnetcfg.util.ipOutOfRange": "子网 IP 的第一个字节应介于 0 到 126 或 128 到 223 之间。",
    "msg.vmnetcfg.util.zeroMask": "子网掩码不能为零。",
    "msg.vmnetcfg.util.maskTooLarge": "子网掩码不能大于 0xfffffff8。",
    "msg.vmnetcfg.util.invalidMask": "子网掩码无效。",
    "msg.vmnetcfg.util.ipMaskMismatch": "子网 IP 和子网掩码不匹配。",
    "msg.vmnetcfg.util.ipNotInSubnetFmt": "在子网范围内输入 IP 地址。",
    "msg.vmnetcfg.mainDlg.hasDHCP": "启用",
    "msg.vmnetcfg.mainDlg.cmbBridge": "已桥接至",
    "msg.vmnetcfg.mainDlg.subnetMask": "子网掩码",
    "msg.vmnetcfg.mainDlg.btnRestoreDefault": "还原默认",
    "msg.vmnetcfg.mainDlg.btnApply": "应用",
    "msg.vmnetcfg.mgr.setNATFmt": "更新%s:启用NAT",
    "msg.vmnetcfg.mgr.changeAddrFmt": "更新%s:修改子网IP",
    "msg.vmnetcfg.mgr.changeMaskFmt": "更新%s:修改子网掩码",
    "msg.vmnetcfg.mgr.stopDHCP": "停止DHCP服务",
    "msg.vmnetcfg.mgr.stopNAT": "停止NAT服务",
    "msg.vmnetcfg.mgr.startNAT": "启动NAT服务",
    "msg.vmnetcfg.mgr.startDHCP": "启动DHCP服务",
    "msg.vmnetcfg.mgr.updateAdapters": "更新主机虚拟适配器",
    "msg.vmnetcfg.natDlg.btnAdd": "添加",
    "msg.vmnetcfg.natDlg.btnRemove": "移除",
    "msg.vmnetcfg.natDlg.allowActiveFTP": "允许活动FTP",
    "msg.vmnetcfg.natDlg.configPort": "配置端口",
    "msg.vmnetcfg.natDlg.enableIPv6": "启用IPv6",
    "msg.vmnetcfg.mapPortDlg.title": "端口映射",
    "msg.vmnetcfg.mapPortDlg.rdoTCP": "TCP",
    "msg.vmnetcfg.mapPortDlg.rdoUDP": "UDP",
    "msg.vmnetcfg.dnsDlg.retries": "重试",
    "msg.vmnetcfg.dhcpDlg.maxLeaseTime": "最长租用",
    "msg.vmnetcfg.netbiosDlg.nbnsRetries": "NBNS重试",
    "msg.vmnetcfg.addNetworkDlg.desc": "选择要添加的网络",
    "msg.vmnetcfg.util.spinEditOutOfRangeFmt": "输入%d到%d之间的值",
}

# 2) 借用 padding 的短词方案（18 条，写入后仍保留 \x00 终止、marker 偏移不变）
SHORT_WORDS = {
    "msg.vmnetcfg.mainDlg.type": "类型",
    "msg.vmnetcfg.mainDlg.btnHelp": "帮助",
    "msg.vmnetcfg.mainDlg.netTypeCustom": "自定义",
    "msg.vmnetcfg.natDlg.btnHelp": "帮助",
    "msg.vmnetcfg.natDlg.hostPort": "主端口",
    "msg.vmnetcfg.natDlg.type": "类型",
    "msg.vmnetcfg.mapPortDlg.hostPort": "主机端口",
    "msg.vmnetcfg.mapPortDlg.type": "类型",
    "msg.vmnetcfg.mapPortDlg.btnOK": "确定",
    "msg.vmnetcfg.mapPortDlg.btnHelp": "帮助",
    "msg.vmnetcfg.dnsDlg.dnsServerGroup": "DNS服务器",
    "msg.vmnetcfg.dnsDlg.btnHelp": "帮助",
    "msg.vmnetcfg.dnsDlg.policyOrder": "顺序",
    "msg.vmnetcfg.dnsDlg.policyBurst": "迸发",
    "msg.vmnetcfg.dhcpDlg.btnHelp": "帮助",
    "msg.vmnetcfg.netbiosDlg.btnOK": "确定",
    "msg.vmnetcfg.netbiosDlg.btnHelp": "帮助",
    "msg.vmnetcfg.addNetworkDlg.btnOK": "确定",
}

MARKER = b'@&!*@*@('


def parse_entries(whole):
    """解析消息表，返回按 start 排序的 entries 及 by_key 索引。"""
    entries = []
    pos = 0
    while True:
        i = whole.find(MARKER, pos)
        if i < 0:
            break
        ek = whole.find(b')', i, i + 300)
        if ek < 0:
            break
        key = whole[i + len(MARKER):ek].decode('ascii', 'ignore')
        ts = ek + 1
        null = whole.find(b'\x00', ts, ts + 4096)
        if null < 0:
            break
        entries.append({'key': key, 'start': i, 'ts': ts, 'end': null})
        pos = i + 1
    entries.sort(key=lambda e: e['start'])
    by = {e['key']: e for e in entries}
    idx = {e['key']: i for i, e in enumerate(entries)}
    return entries, by, idx


def patch(whole):
    """返回 (新字节数组, 应用条目数, 报告字符串)。原地等长 + 借 padding。"""
    entries, by, idx = parse_entries(whole)
    applied = 0
    skipped = []

    # 等长替换
    for k, zh in EQUAL_LENGTH.items():
        if k not in by:
            continue
        e = by[k]
        z = zh.encode('utf-8')
        olen = e['end'] - e['ts']
        if len(z) > olen:
            skipped.append(k)
            continue
        whole[e['ts']:e['end']] = z + b'\x00' * (olen - len(z))
        applied += 1

    # 借 padding 短词
    for k, zh in SHORT_WORDS.items():
        if k not in by:
            continue
        e = by[k]
        i = idx[k]
        ns = entries[i + 1]['start'] if i + 1 < len(entries) else len(whole)
        z = zh.encode('utf-8')
        if len(z) <= ns - e['ts'] - 1:
            whole[e['ts']:ns] = z + b'\x00' * (ns - e['ts'] - len(z))
            applied += 1
        else:
            skipped.append(k)

    report = '已汉化 %d 条' % applied
    if skipped:
        report += '，跳过 %d 条超长' % len(skipped)
    return whole, applied, report


def _candidate_dirs():
    """返回可能的 VMware 安装根目录列表（按优先级）。"""
    dirs = []
    # 1) 常见默认路径
    for base in [r'C:\Program Files\VMware', r'C:\Program Files (x86)\VMware',
                 r'D:\Program Files\VMware', r'D:\Program Files (x86)\VMware']:
        dirs.append(base)
    # 2) 环境变量 ProgramFiles / ProgramFiles(x86)
    for env in ['ProgramFiles', 'ProgramFiles(x86)']:
        p = os.environ.get(env)
        if p:
            dirs.append(os.path.join(p, 'VMware'))
    # 3) 各盘符根目录下的常见位置
    import string
    for d in string.ascii_uppercase:
        root = d + ':\\'
        if os.path.isdir(root):
            dirs.append(os.path.join(root, 'VMware'))
            dirs.append(os.path.join(root, 'Program Files', 'VMware'))
            dirs.append(os.path.join(root, 'Program Files (x86)', 'VMware'))
    return dirs


def find_default_exe():
    """智能定位 vmnetcfg.exe：
    1) 常见路径
    2) 注册表查询 VMware 安装目录
    3) 各盘符 VMware 目录下递归查找
    """
    # 1) 直接候选
    seen = set()
    for base in _candidate_dirs():
        for sub in ['VMware Workstation', '']:
            c = os.path.join(base, sub, 'vmnetcfg.exe') if sub else os.path.join(base, 'vmnetcfg.exe')
            c = os.path.normpath(c)
            if c not in seen and os.path.exists(c):
                return c
            seen.add(c)

    # 2) 注册表查询
    try:
        import winreg
        for root, paths in [
            (winreg.HKEY_LOCAL_MACHINE, [r'SOFTWARE\VMware, Inc.\VMware Workstation',
                                         r'SOFTWARE\WOW6432Node\VMware, Inc.\VMware Workstation']),
            (winreg.HKEY_CURRENT_USER, [r'SOFTWARE\VMware, Inc.\VMware Workstation']),
        ]:
            for p in paths:
                try:
                    k = winreg.OpenKey(root, p)
                    try:
                        val, _ = winreg.QueryValueEx(k, 'InstallPath')
                        if val:
                            c = os.path.join(val, 'vmnetcfg.exe')
                            if os.path.exists(c):
                                return c
                    finally:
                        winreg.CloseKey(k)
                except OSError:
                    continue
    except ImportError:
        pass

    # 3) 各盘符 VMware 目录递归查找（限深度）
    for d in string.ascii_uppercase:
        root = d + ':\\'
        if not os.path.isdir(root):
            continue
        for base in [os.path.join(root, 'VMware'),
                     os.path.join(root, 'Program Files', 'VMware'),
                     os.path.join(root, 'Program Files (x86)', 'VMware')]:
            if not os.path.isdir(base):
                continue
            for dirpath, _, filenames in os.walk(base):
                if 'vmnetcfg.exe' in filenames:
                    return os.path.join(dirpath, 'vmnetcfg.exe')
                # 限制深度，避免全盘遍历
                if dirpath.count(os.sep) - base.count(os.sep) > 4:
                    continue
    return None


def main():
    args = sys.argv[1:]

    # 恢复模式
    if '--restore' in args:
        exe = find_default_exe()
        bak = (exe or '') + '.orig'
        if exe and os.path.exists(bak):
            shutil.copyfile(bak, exe)
            print('[OK] 已从备份恢复原版: %s' % exe)
        else:
            print('[!!] 未找到备份文件 %s，无法恢复' % bak)
        return

    # 定位目标
    exe = None
    for a in args:
        if not a.startswith('-') and a.lower().endswith('.exe'):
            exe = a
            break
    if exe is None:
        exe = find_default_exe()
    if exe is None or not os.path.exists(exe):
        print('[!!] 未找到 vmnetcfg.exe。')
        print('     方法 1：把 vmnetcfg.exe 文件直接拖到这个工具图标上（会自动传入路径）')
        print('     方法 2：命令行运行：')
        print('        auto_patch.exe "你的 vmnetcfg.exe 完整路径"')
        print('     vmnetcfg.exe 通常在 VMware Workstation 安装目录下，可用资源管理器搜索')
        return

    # 备份
    bak = exe + '.orig'
    if not os.path.exists(bak):
        shutil.copyfile(exe, bak)
        print('[OK] 已备份原版到: %s' % bak)
    else:
        print('[..] 备份已存在: %s' % bak)

    # 读取并校验
    whole = bytearray(open(exe, 'rb').read())
    orig_size = len(whole)
    if whole.find(MARKER) < 0:
        print('[!!] 未在文件中找到 VMware 消息表标记，可能不是 vmnetcfg.exe 或已被处理过。')
        return

    # 应用
    whole, applied, report = patch(whole)

    # 校验大小不变
    if len(whole) != orig_size:
        print('[!!] 错误：文件大小改变，已取消写入。')
        return

    open(exe, 'wb').write(whole)
    print('[OK] 汉化完成！%s' % report)
    print('     目标文件: %s' % exe)
    print('     备份文件: %s' % bak)
    print('     提示：请关闭正在运行的虚拟网络编辑器后再运行本工具。')


if __name__ == '__main__':
    main()
