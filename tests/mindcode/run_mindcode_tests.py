#!/usr/bin/env python3
"""Assert that tools/mindcode.py compiles, diagnoses, and fails honestly.

Why this exists: the compiler is a 33 MB jar behind a JRE probe, so nearly every
way it breaks is environmental -- a JRE too old to load the jar, a UTF-8 BOM
that turns into a fake syntax error on line 1, a jar whose `cm` action
deadlocks, an exit code that conflates "bad source" with "could not write the
output file".  Each test below pins one of those, plus the JSON contract that
tools/ and downstream agents actually consume.

Inputs : tools/mindcode.py, out/_mindcode/*.jar, a Java 22+ runtime
Output : stdout, one 'ok <name>' line per passing check
Exit   : 0 everything passed / 1 a check failed / 3 no compiler (skip)
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.dont_write_bytecode = True
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / 'tools'
CLI = TOOLS / 'mindcode.py'
sys.path.insert(0, str(TOOLS))

import mindcode as MC  # noqa: E402

SOURCE_OK = 'x = 1;\nprint(x);\nprintflush(message1);\n'
SOURCE_BAD = 'x = 1\n'
CONTRACT = {'ok', 'mlog', 'diagnostics', 'stats', 'tool', 'elapsed_ms', 'source_sha256'}

CASES = []


def case(fn):
    CASES.append(fn)
    return fn


def check(cond, msg):
    if not cond:
        raise AssertionError(msg)


def same(a, b):
    return os.path.normcase(os.path.abspath(str(a))) == os.path.normcase(os.path.abspath(str(b)))


def run_cli(*args):
    return subprocess.run([sys.executable, str(CLI)] + list(args),
                          capture_output=True, text=True, encoding='utf-8',
                          errors='replace', cwd=str(ROOT), timeout=300)


def one_json(proc):
    lines = [ln for ln in (proc.stdout or '').splitlines() if ln.strip()]
    check(len(lines) == 1, 'expected exactly one stdout line, got %d: %r'
          % (len(lines), lines[:3]))
    return json.loads(lines[0])


def write_source(text, name='input.mnd', bom=False):
    """Write a BOM-free (or deliberately BOM'd) UTF-8 .mnd in a temp dir."""
    holder = tempfile.mkdtemp(prefix='mindcode-test-')
    path = Path(holder) / name
    data = text.encode('utf-8')
    path.write_bytes((b'\xef\xbb\xbf' + data) if bom else data)
    return path


# --------------------------------------------------------------------------
@case
def test_locate_contract():
    info = MC.locate()
    check(set(info) == {'jar', 'java', 'version', 'ok', 'notes'},
          'locate() keys are %r' % (sorted(info),))
    check(info['ok'] is True, 'locate() says the compiler is unusable')
    check(isinstance(info['jar'], str) and Path(info['jar']).is_file(),
          'jar is not an existing file: %r' % (info['jar'],))
    check(isinstance(info['java'], str) and Path(info['java']).is_file(),
          'java is not an existing file: %r' % (info['java'],))
    check(bool(info['version']), 'version is empty')
    check(isinstance(info['notes'], list), 'notes is not a list')
    check(all(isinstance(n, str) for n in info['notes']), 'notes holds non-strings')


@case
def test_compile_source_ok():
    res = MC.compile_source(SOURCE_OK)
    check(set(res) >= CONTRACT, 'result is missing %r' % (sorted(CONTRACT - set(res)),))
    check(res['ok'] is True, 'compile failed: %r' % (res['diagnostics'],))
    check(isinstance(res['mlog'], str) and res['mlog'].strip(), 'mlog is empty')
    check('printflush message1' in res['mlog'], 'mlog lacks printflush: %r' % res['mlog'][:80])
    check(res['diagnostics'] == [], 'unexpected diagnostics: %r' % (res['diagnostics'],))
    stats = res['stats']
    check(stats['instructions'] >= 1, 'instructions is %r' % (stats['instructions'],))
    check(stats['ast_nodes'] >= 1, 'ast_nodes is %r' % (stats['ast_nodes'],))
    check(isinstance(stats['timings_ms'], dict), 'timings_ms is not a dict')
    check(bool(stats['raw']), 'stats.raw is empty')
    check(stats['timed_out'] is False, 'timed_out on a successful compile')
    check(res['tool']['name'] == 'mindcode', 'tool.name is %r' % (res['tool']['name'],))
    check(res['tool']['version'] == MC.locate()['version'], 'tool.version disagrees with locate()')
    check(res['source_sha256'] == hashlib.sha256(SOURCE_OK.encode('utf-8')).hexdigest(),
          'source_sha256 is not the sha256 of the source')
    check(isinstance(res['elapsed_ms'], int) and res['elapsed_ms'] >= 0,
          'elapsed_ms is %r' % (res['elapsed_ms'],))
    check(res['mlog'].endswith('\n') and '\r\n' not in res['mlog'],
          'mlog is not normalised to LF: %r' % res['mlog'][-20:])


@case
def test_parse_error_carries_line_and_col():
    res = MC.compile_source(SOURCE_BAD)
    check(res['ok'] is False, 'a missing semicolon compiled')
    check(res['mlog'] is None, 'mlog is not None on failure')
    diags = res['diagnostics']
    check(len(diags) >= 1, 'no diagnostic for a parse error')
    first = diags[0]
    check(first['file'] == '<source>', 'file is %r' % (first['file'],))
    check(first['line'] == 1, 'line is %r' % (first['line'],))
    check(first['col'] == 6, 'col is %r' % (first['col'],))
    check('error' in first['kind'].lower(), 'kind is %r' % (first['kind'],))
    check(bool(first['message']), 'message is empty')
    check(res['stats']['timed_out'] is False, 'timed_out on a syntax error')


@case
def test_bom_is_not_a_syntax_error():
    plain = MC.compile_source(SOURCE_OK)
    bom = MC.compile_source('\ufeff' + SOURCE_OK)
    check(bom['ok'] is True, 'a BOM turned into a compile error: %r' % (bom['diagnostics'],))
    check(not [d for d in bom['diagnostics'] if d['line'] == 1 and d['col'] == 1],
          'BOM produced a diagnostic at 1:1')
    check(bom['source_sha256'] == plain['source_sha256'],
          'the BOM changed source_sha256 (it should be stripped first)')
    path = write_source(SOURCE_OK, 'bom-on-disk.mnd', bom=True)
    try:
        res = MC.compile_file(str(path))
        check(res['ok'] is True, 'a BOM on disk broke the compile: %r' % (res['diagnostics'],))
    finally:
        path.unlink(missing_ok=True)
        path.parent.rmdir()


@case
def test_compile_file_reports_caller_path():
    path = write_source(SOURCE_BAD, 'broken.mnd')
    try:
        res = MC.compile_file(str(path))
        check(res['ok'] is False, 'broken source compiled')
        check(res['diagnostics'], 'no diagnostic')
        check(res['diagnostics'][0]['file'] == str(path),
              'diagnostic file is %r, expected the caller path' % (res['diagnostics'][0]['file'],))
    finally:
        path.unlink(missing_ok=True)
        path.parent.rmdir()


@case
def test_compile_file_missing_is_io_not_crash():
    missing = ROOT / 'out' / '_mindcode' / 'definitely-not-here.mnd'
    res = MC.compile_file(str(missing))
    check(res['ok'] is False, 'a missing file compiled')
    check(res['mlog'] is None, 'mlog is not None for a missing file')
    check(res['diagnostics'] and res['diagnostics'][0]['kind'] == 'io',
          'kind is %r' % (res['diagnostics'][0]['kind'] if res['diagnostics'] else None,))


@case
def test_env_override_is_authoritative():
    info = MC.locate()
    saved = {k: os.environ.get(k) for k in ('MINDCODE_JAR', 'MINDCODE_JAVA')}
    try:
        os.environ['MINDCODE_JAR'] = info['jar']
        os.environ['MINDCODE_JAVA'] = info['java']
        again = MC.locate()
        check(again['ok'] is True, 'an explicit, working pair was rejected')
        check(same(again['jar'], info['jar']), 'MINDCODE_JAR was not honoured: %r' % (again['jar'],))
        check(same(again['java'], info['java']), 'MINDCODE_JAVA was not honoured')

        bogus = str(Path(info['jar']).with_name('no-such-mindcode.jar'))
        os.environ['MINDCODE_JAR'] = bogus
        broken = MC.locate()
        check(broken['ok'] is False, 'a bogus MINDCODE_JAR silently fell back to another jar')
        check(same(broken['jar'], bogus), 'reported jar is %r, expected the override' % (broken['jar'],))
        check(bool(broken['notes']), 'no note explaining the failure')
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


@case
def test_timeout_is_detected_not_hung():
    started = time.perf_counter()
    res = MC.compile_source(SOURCE_OK, timeout=0.001)
    wall = time.perf_counter() - started
    check(res['ok'] is False, 'a 1 ms timeout still reported success')
    check(res['mlog'] is None, 'mlog is not None after a timeout')
    check(res['stats']['timed_out'] is True, 'stats.timed_out is not set')
    check(any(d['kind'] == 'timeout' for d in res['diagnostics']),
          'no timeout diagnostic: %r' % (res['diagnostics'],))
    check(wall < 90, 'the timeout path took %.1f s' % wall)


@case
def test_cli_json_contract():
    path = write_source(SOURCE_OK, 'cli-ok.mnd')
    try:
        proc = run_cli('compile', str(path), '--json')
        check(proc.returncode == 0, 'exit %d: %r' % (proc.returncode, (proc.stderr or '')[-300:]))
        obj = one_json(proc)
        check(set(obj) >= CONTRACT, 'JSON is missing %r' % (sorted(CONTRACT - set(obj)),))
        check(obj['ok'] is True, 'JSON says ok=False: %r' % (obj['diagnostics'],))
        check('printflush message1' in (obj['mlog'] or ''), 'JSON mlog is wrong')
        check(obj['tool']['version'] == MC.locate()['version'], 'JSON tool.version is wrong')
    finally:
        path.unlink(missing_ok=True)
        path.parent.rmdir()


@case
def test_cli_exit_codes():
    good = write_source(SOURCE_OK, 'exit-ok.mnd')
    bad = write_source(SOURCE_BAD, 'exit-bad.mnd')
    try:
        proc = run_cli('compile', str(good), '--json')
        check(proc.returncode == 0, 'success exit is %d' % proc.returncode)
        proc = run_cli('compile', str(bad), '--json')
        check(proc.returncode == 1, 'compile-error exit is %d' % proc.returncode)
        obj = one_json(proc)
        check(obj['ok'] is False and obj['mlog'] is None, 'error JSON claims success')
        check(bool(obj['diagnostics']), 'error JSON has no diagnostics')
        proc = run_cli('compile', str(ROOT / 'out' / '_mindcode' / 'nope.mnd'), '--json')
        check(proc.returncode == 2, 'missing-file exit is %d (expected 2: cannot run)'
              % proc.returncode)
        # 1 ms cannot compile anything: the JVM needs ~1 s just to start.
        proc = run_cli('compile', str(good), '--json', '--timeout', '0.001')
        check(proc.returncode == 2, 'timeout exit is %d (expected 2: environment)' % proc.returncode)
        obj = one_json(proc)
        check(obj['stats']['timed_out'] is True, 'timeout JSON does not set stats.timed_out')
    finally:
        for p in (good, bad):
            p.unlink(missing_ok=True)
            p.parent.rmdir()


@case
def test_cli_doctor_json():
    proc = run_cli('doctor', '--json')
    check(proc.returncode == 0, 'doctor exit is %d: %r'
          % (proc.returncode, (proc.stderr or '')[-300:]))
    obj = one_json(proc)
    check(obj['ok'] is True, 'doctor says not ok: %r' % (obj.get('notes'),))
    check(obj['status'] == 'ok', 'status is %r' % (obj.get('status'),))
    check({'jar', 'java', 'version', 'candidates', 'checks', 'notes'} <= set(obj),
          'doctor JSON is missing keys')
    checks = {c['name']: c['status'] for c in obj['checks']}
    check(checks.get('version') == 'ok', 'doctor version check is %r' % (checks.get('version'),))
    check(checks.get('smoke-compile') == 'ok',
          'doctor smoke compile is %r' % (checks.get('smoke-compile'),))


@case
def test_target_and_optimizer_flags():
    seven = MC.compile_source(SOURCE_OK, target='7.0')
    eight = MC.compile_source(SOURCE_OK, target='8.0')
    plain = MC.compile_source(SOURCE_OK, optimize=False)
    for tag, res in (('7.0', seven), ('8.0', eight), ('-O 0', plain)):
        check(res['ok'] is True, 'compile failed for %s: %r' % (tag, res['diagnostics']))
        check(res['stats']['instructions'] >= 1, 'no instructions for %s' % tag)
        check(res['stats']['timed_out'] is False, 'timed out for %s' % tag)
    check(plain['stats']['ast_nodes'] == seven['stats']['ast_nodes'],
          'ast_nodes changed with the optimizer flag')



# --- the syntax claims in knowledge/06-mlog/M10-Mindcode-Syntax.md ----------
# The article quotes real compiler output.  If a jar bump changes any of it, the
# article is lying and this case says which line.
SYNTAX_CLAIMS = {
    "variables": ("a = 3;\nb = a + 4;\nprint(b);\n",
                  ["set :a 3", "op add *tmp0 :a 4", "set :b *tmp0", "print :b"]),
    "if_then": ('v = 7;\nif v > 5 then\n    print("big");\nelse\n'
                '    print("small");\nend;\n',
                ["op greaterThan *tmp0 :v 5", "jump 6 equal *tmp0 false",
                 'print "big"', 'print "small"']),
    "for_range": ("s = 0;\nfor n in 1..3 do\n    s += n;\nend;\n",
                  ["set :s 0", "set :n 1", "jump 6 greaterThan :n 3",
                   "op add :s :s :n", "jump 2 always 0 0"]),
    "function_inlines": ("def twice(x)\n    return x * 2;\nend;\nprint(twice(5));\n",
                         ["print 10"]),
    "heap_index": ("allocate heap in cell1;\ndef store(i, v)\n    $i = v;\nend;\n"
                   "store(0, 7);\n",
                   ["set :store:i 0", "write :store:v cell1 0"]),
    "const_folds": ("const L = 4;\nprint(L * 2);\n", ["print 8"]),
}


@case
def test_documented_syntax_still_compiles_as_documented():
    for name, (src, expect) in SYNTAX_CLAIMS.items():
        got = MC.compile_source(src, target='7.0', optimize=False)
        check(got['ok'], '%s no longer compiles: %r'
              % (name, (got.get('diagnostics') or [])[:1]))
        body = [ln.strip() for ln in (got.get('mlog') or '').split('\n') if ln.strip()]
        for line in expect:
            check(line in body, '%s lost %r (got %r)' % (name, line, body[:8]))


@case
def test_documented_gotchas_still_fail_the_documented_way():
    # if ... do is a syntax error; only "then" opens a branch
    bad = MC.compile_source('v = 1;\nif v > 0 do\n    print("x");\nend;\n',
                            target='7.0', optimize=False)
    check(not bad['ok'] and any('then' in (d.get('message') or '')
                                for d in bad['diagnostics']),
          'if/then regression: %r' % (bad.get('diagnostics') or [])[:1])
    # a string literal plus a number is not concatenation
    concat = MC.compile_source('i = 2;\nprint("i=" + i);\n',
                               target='7.0', optimize=False)
    check(not concat['ok'] and any('string' in (d.get('message') or '').lower()
                                   for d in concat['diagnostics']),
          'string concatenation stopped being an error')
    # {i} inside $"..." is NOT interpolated -- it survives as text
    braces = MC.compile_source('i = 2;\nprint($"i={i}");\n',
                               target='7.0', optimize=False)
    check(braces['ok'] and 'i={i}' in (braces.get('mlog') or ''),
          'brace interpolation changed: %r' % (braces.get('mlog') or '')[:80])
    # and $i does interpolate, as two separate prints
    dollar = MC.compile_source('i = 2;\nprint($"i=$i");\n',
                               target='7.0', optimize=False)
    body = [ln.strip() for ln in (dollar.get('mlog') or '').split('\n') if ln.strip()]
    check(dollar['ok'] and 'print "i="' in body and 'print :i' in body,
          'dollar interpolation changed: %r' % body[:4])
    # stack allocation does not serve external variables
    stack = MC.compile_source('allocate stack in cell1;\ndef put(i, v)\n    $i = v;\nend;\n'
                              'put(0, 9);\n', target='7.0', optimize=False)
    check(not stack['ok'] and any('heap' in (d.get('message') or '').lower()
                                  for d in stack['diagnostics']),
          'stack/heap distinction changed')

def main():
    info = MC.locate()
    if not info['ok']:
        print('skip mindcode: no usable compiler on this machine')
        for note in info['notes']:
            print('     - %s' % note)
        print('     set MINDCODE_JAR and MINDCODE_JAVA to run these tests')
        return 3
    java = Path(info['java'])
    runtime = java.parent.parent.name if java.name.lower().startswith('java') else java.name
    print('mindcode %s via %s' % (info['version'], runtime))

    started = time.perf_counter()
    failed = []
    for fn in CASES:
        step = time.perf_counter()
        try:
            fn()
        except AssertionError as exc:
            failed.append(fn.__name__)
            print('FAIL %-38s %s' % (fn.__name__, exc))
        except Exception as exc:                                  # noqa: BLE001
            failed.append(fn.__name__)
            print('FAIL %-38s %s: %s' % (fn.__name__, type(exc).__name__, exc))
        else:
            print('ok   %-38s %6d ms' % (fn.__name__, (time.perf_counter() - step) * 1000))

    total = time.perf_counter() - started
    if failed:
        print('\n%d/%d checks failed in %.1f s: %s'
              % (len(failed), len(CASES), total, ', '.join(failed)))
        return 1
    print('\nall %d checks passed in %.1f s' % (len(CASES), total))
    return 0


if __name__ == '__main__':
    sys.exit(main())
