#!/usr/bin/env python3
"""dbstat.py - 只读查看 kb.sqlite3 的规模（chunks/文件数/各类块数/最新写入时间不查，避免锁库）。

用法:
    python dbstat.py <kb.sqlite3>
"""
import sqlite3
import sys


def main(argv):
    if len(argv) != 2:
        print("用法: dbstat.py <kb.sqlite3>", file=sys.stderr)
        return 2
    path = argv[1]
    con = sqlite3.connect("file:" + path.replace("\\", "/") + "?mode=ro", uri=True)
    try:
        q = con.execute
        chunks = q("select count(*) from chunks").fetchone()[0]
        files = q("select count(distinct path) from chunks").fetchone()[0]
        kinds = dict(q("select kind, count(*) from chunks group by kind").fetchall())
        print("chunks=%d files=%d kinds=%s" % (chunks, files, kinds))
        for row in q("select path, count(*) c from chunks where kind='data' group by path").fetchall():
            print("  data  %s  %d" % row)
        print("top paths:")
        for p, c in q("select path, count(*) c from chunks group by path order by c desc limit 8").fetchall():
            print("  %4d  %s" % (c, p))
    finally:
        con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
