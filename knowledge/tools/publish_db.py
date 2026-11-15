#!/usr/bin/env python3
"""publish_db.py - 把构建好的 kb.sqlite3 用 sqlite backup API 写入正式落点（不 unlink，兼容 MCP 正持有句柄）。

用法:
    python publish_db.py <src.sqlite3> <dst.sqlite3>

为什么不用复制/替换: 正式库 out/_kb/kb.sqlite3 被 MCP 服务进程持有，
Windows 下 DB_PATH.unlink() 会 PermissionError [WinError 5]；
sqlite3 的 backup() 直接在目标文件内部重写页面，读方无需关闭。
"""
import sqlite3
import sys
from pathlib import Path

def main(argv):
    if len(argv) != 3:
        print("用法: publish_db.py <src.sqlite3> <dst.sqlite3>", file=sys.stderr)
        return 2
    src, dst = Path(argv[1]), Path(argv[2])
    if not src.is_file():
        print("源库不存在: " + str(src), file=sys.stderr)
        return 2
    dst.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(src)) as s, sqlite3.connect(str(dst)) as d:
        s.backup(d)
        d.commit()
        n_src = s.execute("select count(*) from chunks").fetchone()[0]
        n_dst = d.execute("select count(*) from chunks").fetchone()[0]
        fts = d.execute("select count(*) from fts").fetchone()[0]
    print("published %s -> %s  chunks src=%d dst=%d fts=%d" % (src.name, dst, n_src, n_dst, fts))
    return 0 if n_src == n_dst else 1

if __name__ == "__main__":
    sys.exit(main(sys.argv))
