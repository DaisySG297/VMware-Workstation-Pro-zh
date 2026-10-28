# -*- coding: utf-8 -*-
"""
VMware Workstation Pro 26H1u1 一键汉化 / 一键恢复工具（主程序 + 虚拟网络编辑器）

用法：
  - 双击运行：自动定位 VMware 安装目录，交互式选择「汉化」或「恢复」
  - 拖拽 vmware.exe 到本工具：自动定位到该安装目录
  - 命令行：
      vmware-zh-patcher.exe                    # 自动定位 + 交互选择
      vmware-zh-patcher.exe "D:\\VMware\\..."   # 指定安装目录
      vmware-zh-patcher.exe --apply            # 直接汉化（跳过交互）
      vmware-zh-patcher.exe --restore          # 直接恢复（跳过交互）
"""
import os
import sys
import shutil
import time

# 中文控制台输出：Windows 中文系统默认 GBK 代码页
if sys.platform == 'win32':
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

# 需要部署的文件：资源名 -> (目标相对路径, 是否必选)
FILES = [
    ('vmware.vmsg',        'messages/zh_CN/vmware.vmsg',        True),
    ('vmui-zh_CN.dll',     'messages/zh_CN/vmui-zh_CN.dll',     True),
    ('vmappsdk-zh_CN.dll', 'messages/zh_CN/vmappsdk-zh_CN.dll', True),
    ('vmware-tray.exe',    'vmware-tray.exe',                   True),
    ('vmnetcfg_zh.exe',    'vmnetcfg.exe',                      True),
]

BACKUP_DIR_NAME = 'vmware-zh_CN-backup'


# ---------------------------------------------------------------------------
# 定位 VMware 安装目录
# ---------------------------------------------------------------------------
def find_install_dir():
    """自动定位 VMware Workstation 安装目录。"""
    candidates = []

    # 1. 注册表
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

    # 2. 环境变量
    for env in ('ProgramFiles', 'ProgramFiles(x86)', 'ProgramW6432'):
        p = os.environ.get(env)
        if p:
            candidates.append(os.path.join(p, 'VMware', 'VMware Workstation'))
            candidates.append(os.path.join(p, 'VMware'))

    # 3. 各盘符常见位置
    import string
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
            # 可能是拖进来的 vmware.exe 或某个 dll，取其所在目录
            if os.path.basename(p).lower() in ('vmware.exe', 'vmware-tray.exe', 'vmnetcfg.exe'):
                return os.path.dirname(p)
            if os.path.basename(p).lower().startswith('vmware'):
                return os.path.dirname(p)
        if os.path.isdir(p) and os.path.isfile(os.path.join(p, 'vmware.exe')):
            return p
    return None


# ---------------------------------------------------------------------------
# 备份 / 部署 / 恢复
# ---------------------------------------------------------------------------
def backup_dir(install):
    return os.path.join(install, BACKUP_DIR_NAME)


def do_apply(install, verbose=True):
    """备份原文件并部署汉化文件。返回 (成功数, 跳过数, 失败列表)。"""
    if not os.path.isfile(os.path.join(install, 'vmware.exe')):
        print('[!!] 未在目录找到 vmware.exe，可能不是 VMware 安装目录：')
        print('     ' + install)
        return 0, 0, ['目标目录无效']

    bk = backup_dir(install)
    os.makedirs(bk, exist_ok=True)

    ok = 0
    skip = 0
    fails = []

    for res_name, rel, required in FILES:
        src = os.path.join(ASSETS_DIR, res_name)
        dst = os.path.join(install, rel)
        if not os.path.exists(src):
            fails.append('缺少资源: ' + res_name)
            continue

        # 备份原文件（若目标存在且未备份过）
        if os.path.exists(dst):
            bak = os.path.join(bk, rel)
            if not os.path.exists(bak):
                os.makedirs(os.path.dirname(bak), exist_ok=True)
                shutil.copy2(dst, bak)
            else:
                skip += 1
        else:
            # 目标不存在也记录（恢复时知道这个文件是新加的）
            bak = os.path.join(bk, rel)
            if not os.path.exists(bak):
                # 标记为"部署前不存在"，恢复时删除
                marker = bak + '.was-absent'
                open(marker, 'w').close()

        # 部署
        try:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            ok += 1
        except Exception as e:
            fails.append('%s: %s' % (rel, e))

    return ok, skip, fails


def do_restore(install, verbose=True):
    """从备份还原原版文件。返回 (还原数, 删除数, 失败列表)。"""
    bk = backup_dir(install)
    if not os.path.isdir(bk):
        print('[!!] 未找到备份目录，无法恢复：' + bk)
        return 0, 0, ['无备份']

    restored = 0
    removed = 0
    fails = []

    for res_name, rel, required in FILES:
        bak = os.path.join(bk, rel)
        dst = os.path.join(install, rel)
        absent_marker = bak + '.was-absent'

        if os.path.exists(absent_marker):
            # 部署前该文件不存在 -> 恢复时删除
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
        # 若无备份也无标记，说明该文件从未被本工具部署过，跳过

    # 若备份目录已空，清理
    return restored, removed, fails


def print_banner():
    print('=' * 60)
    print('  VMware Workstation Pro 26H1u1 一键汉化工具')
    print('  主程序 + 虚拟网络编辑器（vmnetcfg）')
    print('=' * 60)
    print()


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
        input('按回车退出...')
        return

    print('[+] 已定位安装目录：' + target)
    print()

    # 判断动作
    if '--apply' in args:
        action = 'apply'
    elif '--restore' in args:
        action = 'restore'
    else:
        print('请选择操作：')
        print('  [1] 汉化（备份原文件后部署中文）')
        print('  [2] 恢复原版（从备份还原英文）')
        print()
        try:
            choice = input('输入 1 或 2，回车确认：').strip()
        except Exception:
            choice = ''
        action = 'apply' if choice == '1' else ('restore' if choice == '2' else None)
        if action is None:
            print('[!] 输入无效，退出。')
            return

    print()
    if action == 'apply':
        print('正在汉化，请稍候...')
        # 提示关闭 VMware
        print('[提示] 若 VMware 正在运行，请先关闭（尤其是 vmware-tray.exe）。')
        ok, skip, fails = do_apply(target)
        print()
        if ok:
            print('[OK] 汉化完成！已部署 %d 个文件。' % ok)
        if skip:
            print('     其中 %d 个文件之前已备份过（跳过重复备份）。' % skip)
        if fails:
            print('[!!] %d 个文件处理失败：' % len(fails))
            for f in fails:
                print('      - ' + f)
        print()
        print('备份目录：' + backup_dir(target))
        print('恢复原版：重新运行本工具，选择 [2] 恢复原版。')
    else:
        print('正在恢复原版，请稍候...')
        restored, removed, fails = do_restore(target)
        print()
        if restored:
            print('[OK] 已还原 %d 个文件为原版。' % restored)
        if removed:
            print('     已删除 %d 个汉化新增文件。' % removed)
        if fails:
            print('[!!] %d 个文件处理失败：' % len(fails))
            for f in fails:
                print('      - ' + f)
        if not restored and not removed and not fails:
            print('[提示] 没有可恢复的文件（可能从未汉化过，或已恢复）。')
        print()

    print('完成。')
    time.sleep(1)


if __name__ == '__main__':
    main()
