"""Compare real Mindustry execution before/after signing and extraction."""
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
import mlogsim
import msch
import mschgen
from mlogent.logic import source


def main():
    java, jar = mlogsim._default_java(), mlogsim._default_jar()
    if not java or not Path(jar).is_file():
        raise RuntimeError('Real roundtrip regression requires Java and a Mindustry server JAR')
    original = (Path(__file__).parent / 'fixtures' / 'impact-startup.mlog').read_text(encoding='utf-8')
    signed, *_ = source.to_delivery(original, 'Iliary')
    blueprint = mschgen.Blueprint('impact-roundtrip')
    blueprint.add_logic(signed)
    extracted_code = msch.parse_bytes(blueprint.build()).logic_tiles()[0].logic.code
    editable, *_ = source.to_editable(extracted_code)
    rebuilt, *_ = source.to_delivery(editable, 'Iliary')
    tracked = ('return', 'E', 'E.need', 't', 't0', 'h', 'h0', 'i', 'E.imptr',
               'PI', 'PO', 'Delta', 'P.E', 'E.b', 'E(h)', 't(h)')
    server = mlogsim.Server(java, jar)
    try:
        server.prepare()
        with tempfile.TemporaryDirectory() as directory:
            for block, heat in ((None, 0), ('container', 0), ('impact-reactor', .2), ('impact-reactor', .98)):
                baseline = None
                for name, code in (('original', original), ('signed', signed),
                                   ('editable', editable), ('rebuilt', rebuilt)):
                    server.reset_world()
                    links = [] if block is None else [{'name': 'target1', 'block': block}]
                    setup = '' if block != 'impact-reactor' else (
                        'var lk=b.links.get(0); W.build(lk.x,lk.y).warmup=' + str(heat) + ';')
                    trace = str(Path(directory) / 'instructions.tsv')
                    with patch.object(mlogsim, 'infer_links', return_value=links):
                        record = mlogsim.run_mlog(server, name, code, steps=1000,
                                                 setup_js=setup, itrace=trace, itrace_vars=tracked,
                                                 compile_diagnostics=True)
                    assert record['compile']['ok'], record['compile']
                    assert record['compile']['instructions'] == 86, record['compile']
                    rows = [line.split('\t')[:3] for line in Path(trace).read_text(encoding='utf-8').splitlines()[1:]]
                    assert len(rows) == 1000
                    effects = server.js('for(var k=0;k<b.links.size;k++){var lk=b.links.get(k);'
                                        'var target=W.build(lk.x,lk.y);'
                                        'print("EFFECT\\t"+lk.name+"\\t"+target.enabled);}')
                    result = (rows, record['counter'], record['text'], effects,
                              {key: record['vars'].get(key) for key in tracked})
                    if baseline is None:
                        baseline = result
                        pcs = {int(row[1]) for row in rows}
                        assert {15, 16, 67, 85, 17} <= pcs, pcs
                        if block == 'impact-reactor' and heat == .2:
                            assert {43, 44, 45} <= pcs, pcs
                    else:
                        assert result == baseline, (block, heat, name, 'execution diverged')
                print(f'PASS impact {block or "no links"} heat={heat}: 4 variants, 1000 instructions each')
        # Guard the dynamic return itself against a shared mistake in converters.
        call_return = ('set result 0\nset return @counter\njump 5 always 0 false\n'
                       'op add result result 1\nend\nop add result result 10\nop add @counter return 1\n')
        for code in (call_return, source.to_delivery(call_return, 'Iliary')[0]):
            server.reset_world()
            rec = mlogsim.run_mlog(server, 'call-return', code, steps=7)
            assert float(rec['vars']['result']) == 11, rec
        print('PASS explicit dynamic call/return: result=11 before and after signing')
    finally:
        server.close()


if __name__ == '__main__':
    main()
