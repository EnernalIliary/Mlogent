# -*- coding: utf-8 -*-
"""Independent audit of tools/instr_semantics.json against the Mindustry source."""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGIC = os.path.join(ROOT, 'Mindustry-Source', 'core', 'src', 'mindustry', 'logic')
S = json.load(open(os.path.join(ROOT, 'tools', 'instr_semantics.json'), encoding='utf-8'))
fails = []

def strip_comments(t):
    return "\n".join(l for l in t.splitlines() if not l.strip().startswith('//'))

# 1. mnemonic coverage: every live @RegisterStatement in LStatements.java must be present
src = strip_comments(open(os.path.join(LOGIC, 'LStatements.java'), encoding='utf-8').read())
reg = re.findall(r'@RegisterStatement\("([^"]+)"\)', src)
missing = [r for r in reg if r not in S['instructions']]
extra = [k for k in S['instructions'] if k not in reg]
print("live @RegisterStatement: %d   json instructions: %d" % (len(reg), len(S['instructions'])))
if missing: fails.append("missing from json: %s" % missing)
if extra: fails.append("extra in json (not in source): %s" % extra)
dups = [r for r in set(reg) if reg.count(r) > 1]
if dups: fails.append("duplicate registrations in source: %s" % dups)
if '#' in reg: fails.append("'#' unexpectedly live")

# 2. op coverage
lopsrc = open(os.path.join(LOGIC, 'LogicOp.java'), encoding='utf-8').read()
body = lopsrc.split('public enum LogicOp{')[1].split('\n    ;')[0]
names = re.findall(r'^\s{4}([A-Za-z0-9]+)\(', body, re.M)
print("LogicOp constants: %d   json ops: %d" % (len(names), len(S['ops'])))
if set(names) != set(S['ops'].keys()):
    fails.append("ops mismatch: missing=%s extra=%s" % (sorted(set(names) - set(S['ops'])), sorted(set(S['ops']) - set(names))))

# 3. structural checks
for name, d in S['instructions'].items():
    ar = d['arity']
    if isinstance(ar, int):
        if len(d['params']) != ar:
            fails.append("%s: params len %d != arity %d" % (name, len(d['params']), ar))
        for k in ('defs', 'uses', 'maybe_uses', 'defs_conditional', 'always_evaluated'):
            for i in d.get(k, []):
                if not 0 <= i < ar:
                    fails.append("%s.%s index %d >= arity %d" % (name, k, i, ar))
        for i in d.get('tokens', {}):
            if not 0 <= int(i) < ar:
                fails.append("%s.tokens index %s" % (name, i))
            if int(i) in d.get('defs', []):
                fails.append("%s: token index %s is also a def" % (name, i))
            if int(i) in d.get('uses', []):
                fails.append("%s: token index %s is also a use" % (name, i))
    for sc, sd in d.get('subcommands', {}).items():
        n = len(sd.get('args', []))          # args lists only the semantically used params
        for k in ('defs', 'uses', 'semantic_uses'):
            for i in sd.get(k, []):
                if isinstance(ar, int) and not 0 <= i < ar:
                    fails.append("%s.%s.%s index %d out of range" % (name, sc, k, i))
                if i == 0:
                    fails.append("%s.%s touches token index 0" % (name, sc))
                if k == 'semantic_uses' and n and i > n:
                    fails.append("%s.%s uses index %d but only %d args declared" % (name, sc, i, n))

# 4. ops table sanity
for on, od in S['ops'].items():
    if od['operands'] not in (1, 2):
        fails.append("op %s operands=%s" % (on, od['operands']))
    if od['returns'] != 'number':
        fails.append("op %s returns %s but OpI always setnum()" % (on, od['returns']))

print()
print("%-13s %5s %-30s %-12s %s" % ("mnemonic", "arity", "params", "defs", "uses"))
for name, d in S['instructions'].items():
    print("%-13s %5s %-30s %-12s %s" % (name, d['arity'], ",".join(d['params'])[:30], d.get('defs'), d.get('uses')))

print()
print("defs per ucontrol: %s" % {k: v['defs'] for k, v in S['instructions']['ucontrol']['subcommands'].items() if v['defs']})
print("defs per ulocate:  %s" % {k: v['defs'] for k, v in S['instructions']['ulocate']['subcommands'].items()})
print("defs per draw:     %s" % {k: v['defs'] for k, v in S['instructions']['draw']['subcommands'].items() if v['defs']})
print("binary ops: %d  unary ops: %d" % (
    sum(1 for o in S['ops'].values() if o['operands'] == 2),
    sum(1 for o in S['ops'].values() if o['operands'] == 1)))
print()
if fails:
    print("FAILURES (%d):" % len(fails))
    for f in fails: print("  - " + f)
    sys.exit(1)
print("ALL CHECKS PASSED")
