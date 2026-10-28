# -*- coding: utf-8 -*-
"""
VMware Workstation Pro 26H1u1 全汉化一键工具（主程序 + 虚拟网络编辑器）

一次搞定两件事：
  1. 主程序(vmware.exe)界面汉化 —— 部署 5 个语言文件到 messages/zh_CN/
  2. 虚拟网络编辑器(vmnetcfg.exe)汉化 —— 二进制等长替换 + 借用 padding

用法：
  - 双击运行：自动定位 VMware 安装目录，交互选择「汉化」或「恢复」
  - 拖拽 vmware.exe 到本工具：自动定位到该安装目录
  - 命令行：
      vmware-zh-patcher.exe                          # 自动定位 + 交互
      vmware-zh-patcher.exe "D:\\...\\VMware Workstation"   # 指定目录
      vmware-zh-patcher.exe --apply                  # 直接汉化（跳过交互）
      vmware-zh-patcher.exe --restore                # 直接恢复（跳过交互）
"""
import os
import sys
import shutil
import string
import time

# 中文控制台输出：Windows 中文系统默认 GBK 代码页
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='gbk', errors='replace')
        sys.stderr.reconfigure(encoding='gbk', errors='replace')
    except Exception:
        pass


# ---------------------------------------------------------------------------
# 内嵌资源解析（PyInstaller --onefile 运行时解包路径）
# ---------------------------------------------------------------------------
def resource_path(rel):
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel)


ASSETS_DIR = resource_path('assets')

BACKUP_DIR_NAME = 'vmware-zh_CN-backup'

# 主程序汉化：资源名 -> 目标相对路径（需部署到安装目录）
MAIN_FILES = [
    ('vmware.vmsg',        'messages/zh_CN/vmware.vmsg'),
    ('vmui-zh_CN.dll',     'messages/zh_CN/vmui-zh_CN.dll'),
    ('vmappsdk-zh_CN.dll', 'messages/zh_CN/vmappsdk-zh_CN.dll'),
    ('vmware-tray.exe',    'vmware-tray.exe'),
]

# ==================== vmnetcfg 内嵌汉化方案 ====================
# 1) 等长替换方案（中文 UTF-8 <= 原英文字节，原地覆盖补 \x00）
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

# 2) 借用 padding 的短词方案
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


# ---------------------------------------------------------------------------
# 定位 VMware 安装目录
# ---------------------------------------------------------------------------
def find_install_dir():
    """自动定位 VMware Workstation 安装目录。"""
    candidates = []

    try:
        import winreg
        for root, path in [
            (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\VMware, Inc.\VMware Workstation'),
            (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\WOW6432Node\VMware, Inc.\VMware Workstation'),
        ]:
            try:
                k = winreg.OpenKey(root, path)
                v, _ = winreg.QueryValueEx(k, 'InstallPath')
                winreg.CloseKey(k)
                if v:
                    candidates.append(v)
            except Exception:
                pass
    except Exception:
        pass

    for env in ('ProgramFiles', 'ProgramFiles(x86)', 'ProgramW6432'):
        p = os.environ.get(env)
        if p:
            candidates.append(os.path.join(p, 'VMware', 'VMware Workstation'))
            candidates.append(os.path.join(p, 'VMware'))

    for d in string.ascii_uppercase:
        root = d + ':\\'
        if not os.path.exists(root):
            continue
        candidates.append(os.path.join(root, 'Program Files', 'VMware', 'VMware Workstation'))
        candidates.append(os.path.join(root, 'Program Files (x86)', 'VMware', 'VMware Workstation'))
        candidates.append(os.path.join(root, 'VMware', 'VMware Workstation'))

    for c in candidates:
        if c and os.path.isfile(os.path.join(c, 'vmware.exe')):
            return os.path.normpath(c)
    return None


def resolve_target(args):
    """从命令行参数/拖拽解析目标安装目录。"""
    for a in args:
        if a in ('--apply', '--restore'):
            continue
        p = os.path.abspath(a)
        if os.path.isfile(p):
            base = os.path.basename(p).lower()
            if base in ('vmware.exe', 'vmware-tray.exe', 'vmnetcfg.exe') or base.startswith('vmware'):
                return os.path.dirname(p)
        if os.path.isdir(p) and os.path.isfile(os.path.join(p, 'vmware.exe')):
            return p
    return None


# ---------------------------------------------------------------------------
# 主程序汉化：备份 + 部署 / 恢复
# ---------------------------------------------------------------------------
def backup_dir(install):
    return os.path.join(install, BACKUP_DIR_NAME)


def main_apply(install, scope='all'):
    """部署主程序语言文件 + vmnetcfg 汉化。scope: all / main / vmnetcfg。返回统计。"""
    bk = backup_dir(install)
    os.makedirs(bk, exist_ok=True)
    ok = 0
    skip = 0
    fails = []

    # 1) 主程序语言文件
    if scope in ('all', 'main'):
        for res_name, rel in MAIN_FILES:
            src = os.path.join(ASSETS_DIR, res_name)
            dst = os.path.join(install, rel)
            if not os.path.exists(src):
                fails.append('缺少资源: ' + res_name)
                continue
            if os.path.exists(dst):
                bak = os.path.join(bk, rel)
                if not os.path.exists(bak):
                    os.makedirs(os.path.dirname(bak), exist_ok=True)
                    shutil.copy2(dst, bak)
                else:
                    skip += 1
            else:
                bak = os.path.join(bk, rel)
                if not os.path.exists(bak):
                    open(bak + '.was-absent', 'w').close()
            try:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
                ok += 1
            except Exception as e:
                fails.append('%s: %s' % (rel, e))
        print('[OK] 主程序界面汉化完成（4 个语言文件）')

    # 2) vmnetcfg 二进制汉化
    if scope not in ('all', 'vmnetcfg'):
        return ok, skip, fails

    vmn = os.path.join(install, 'vmnetcfg.exe')
    if os.path.exists(vmn):
        bak = os.path.join(bk, 'vmnetcfg.exe')
        if not os.path.exists(bak):
            shutil.copy2(vmn, bak)
        else:
            skip += 1
        try:
            whole = bytearray(open(vmn, 'rb').read())
            orig_size = len(whole)
            if whole.find(MARKER) >= 0:
                applied, _ = patch_vmnetcfg(whole)
                if len(whole) == orig_size:
                    open(vmn, 'wb').write(whole)
                    ok += 1
                    if applied > 0:
                        print('[OK] vmnetcfg.exe 已汉化 %d 条' % applied)
                else:
                    fails.append('vmnetcfg.exe: 大小改变已取消')
            else:
                # 可能已是汉化版，跳过
                print('[..] vmnetcfg.exe 未发现消息表（可能已汉化或非原版），跳过')
                skip += 1
        except Exception as e:
            fails.append('vmnetcfg.exe: %s' % e)
    else:
        print('[..] 未找到 vmnetcfg.exe，跳过')

    return ok, skip, fails


def main_restore(install):
    """恢复主程序语言文件 + vmnetcfg。返回统计。"""
    bk = backup_dir(install)
    if not os.path.isdir(bk):
        print('[!!] 未找到备份目录：' + bk)
        return 0, 0, ['无备份']

    restored = 0
    removed = 0
    fails = []

    for res_name, rel in MAIN_FILES:
        bak = os.path.join(bk, rel)
        dst = os.path.join(install, rel)
        absent_marker = bak + '.was-absent'
        if os.path.exists(absent_marker):
            if os.path.exists(dst):
                try:
                    os.remove(dst)
                    removed += 1
                except Exception as e:
                    fails.append('%s: %s' % (rel, e))
            try:
                os.remove(absent_marker)
            except Exception:
                pass
        elif os.path.exists(bak):
            try:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(bak, dst)
                restored += 1
            except Exception as e:
                fails.append('%s: %s' % (rel, e))

    # vmnetcfg 恢复
    vmn = os.path.join(install, 'vmnetcfg.exe')
    bak = os.path.join(bk, 'vmnetcfg.exe')
    if os.path.exists(bak):
        try:
            shutil.copy2(bak, vmn)
            restored += 1
        except Exception as e:
            fails.append('vmnetcfg.exe: %s' % e)

    return restored, removed, fails


# ---------------------------------------------------------------------------
# vmnetcfg 二进制 patch（等长替换 + 借 padding，零崩溃）
# ---------------------------------------------------------------------------
def parse_entries(whole):
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


def patch_vmnetcfg(whole):
    entries, by, idx = parse_entries(whole)
    applied = 0
    skipped = []

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

    return applied, (len(skipped) if skipped else 0)


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------
def print_banner():
    print('=' * 60)
    print('  VMware Workstation Pro 26H1u1 全汉化工具')
    print('  主程序 + 虚拟网络编辑器（vmnetcfg）')
    print('=' * 60)
    print()


def _read_choice(prompt='请输入选项：'):
    try:
        return input(prompt).strip()
    except Exception:
        return ''


def _input_countdown(seconds, cancel_key='0'):
    """倒计时自动选择：返回 True 表示执行默认，False 表示取消。"""
    import threading
    holder = {}

    def _wait():
        try:
            holder['v'] = input()
        except Exception:
            holder['v'] = ''

    t = threading.Thread(target=_wait, daemon=True)
    t.start()
    for i in range(seconds, 0, -1):
        if 'v' in holder:
            break
        sys.stdout.write('\r  %d 秒后自动执行，按 %s 回车取消，直接回车立即执行... ' % (i, cancel_key))
        sys.stdout.flush()
        t.join(1)
    if 'v' not in holder:
        holder['v'] = ''
    v = holder['v'].strip()
    if v == cancel_key:
        return False
    return True


def main():
    args = sys.argv[1:]
    target = resolve_target(args)
    if target is None:
        target = find_install_dir()

    print_banner()

    if target is None or not os.path.isfile(os.path.join(target, 'vmware.exe')):
        print('[!!] 未自动定位到 VMware 安装目录。')
        print()
        print('请任选一种方式：')
        print('  1. 把 vmware.exe 拖到本工具图标上')
        print('  2. 命令行：vmware-zh-patcher.exe "D:\\Program Files\\VMware\\VMware Workstation"')
        print()
        _read_choice('按回车退出...')
        return

    print('[+] 安装目录：' + target)
    print()

    # 命令行直通模式（无人值守，不等待输入）
    if '--apply' in args:
        scope = 'main' if '--no-vmnetcfg' in args else 'all'
        _run_apply(target, scope, interactive=False)
        return
    if '--restore' in args:
        _run_restore(target, interactive=False)
        return

    # 交互菜单
    print('=' * 46)
    print('           请选择要执行的操作')
    print('=' * 46)
    print('  [1] 全部汉化（主程序 + 虚拟网络编辑器）')
    print('  [2] 仅汉化主程序（不含 vmnetcfg）')
    print('  [3] 仅汉化虚拟网络编辑器（vmnetcfg）')
    print('  [4] 恢复原版（还原所有英文）')
    print('  [0] 退出')
    print('=' * 46)
    print()

    choice = _read_choice('请输入选项数字并回车：')
    print()

    if choice == '1':
        _run_apply(target, 'all')
    elif choice == '2':
        _run_apply(target, 'main')
    elif choice == '3':
        _run_apply(target, 'vmnetcfg')
    elif choice == '4':
        _run_restore(target)
    elif choice == '0':
        print('已退出。')
    else:
        print('[!] 无效选项，退出。')


def _run_apply(target, scope, interactive=True):
    print('正在汉化，请稍候...')
    print('[提示] 若 VMware 正在运行，请先关闭（尤其是 vmware-tray.exe / vmware.exe）。')
    print()
    ok, skip, fails = main_apply(target, scope)
    print()
    if ok:
        print('[OK] 汉化完成！共处理 %d 项。' % ok)
    if skip:
        print('     其中 %d 项之前已备份（跳过重复备份）。' % skip)
    if fails:
        print('[!!] %d 项处理失败：' % len(fails))
        for f in fails:
            print('      - ' + f)
    print()
    print('备份目录：' + backup_dir(target))
    print('恢复原版：重新运行本工具，选 [4] 恢复原版。')
    print()
    if interactive:
        _read_choice('按回车退出...')


def _run_restore(target, interactive=True):
    print('正在恢复原版，请稍候...')
    restored, removed, fails = main_restore(target)
    print()
    if restored:
        print('[OK] 已还原 %d 个文件为原版。' % restored)
    if removed:
        print('     已删除 %d 个汉化新增文件。' % removed)
    if fails:
        print('[!!] %d 项处理失败：' % len(fails))
        for f in fails:
            print('      - ' + f)
    if not restored and not removed and not fails:
        print('[提示] 没有可恢复的文件（可能从未汉化过，或已恢复）。')
    print()
    if interactive:
        _read_choice('按回车退出...')


if __name__ == '__main__':
    main()
