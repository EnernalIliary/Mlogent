"""Shared JavaScript for inspecting the running Mindustry assembler."""

COMPILE_JS = r"""
function compileMlog(source, privileged){
    var logic = Packages.mindustry.logic, asm = logic.LAssembler;
    var version = Packages.mindustry.core.Version;
    var result = {ok: true, build: version.build, version: String(version.buildString()),
                  privileged: !!privileged, statements: null, instructions: null, diagnostics: []};
    function diagnostic(code, message, instruction){
        result.diagnostics.push({code: code, message: message, instruction: instruction});
        result.ok = false;
    }
    try{
        var statements = asm.read(source, privileged);
        result.statements = statements.size;
        for(var i = 0; i < statements.size; i++){
            if(String(statements.get(i).getClass().getSimpleName()) === "InvalidStatement"){
                diagnostic("invalid_statement", "The game parser rejected or disallowed this statement", i);
            }
        }
        var program = asm.assemble(source, privileged);
        result.instructions = program.instructions.length;
        if(result.instructions < result.statements){
            diagnostic("instruction_omitted", "The game assembler omitted one or more statements", null);
        }
        if(result.statements === logic.LExecutor.maxInstructions){
            /* LAssembler.read returns no indication that the native parser stopped early. */
            try{
                var cls = java.lang.Class.forName("mindustry.logic.LParser");
                var ctor = cls.getDeclaredConstructor(java.lang.Class.forName("java.lang.String"),
                                                       java.lang.Boolean.TYPE);
                var parse = cls.getDeclaredMethod("parse"), pos = cls.getDeclaredField("pos");
                ctor.setAccessible(true);
                parse.setAccessible(true);
                pos.setAccessible(true);
                var parser = ctor.newInstance(new java.lang.String(source), java.lang.Boolean.valueOf(privileged));
                parse.invoke(parser);
                var tail = String(source).slice(pos.getInt(parser));
                if(tail.replace(/#[^\r\n]*/g, "").replace(/[\s;]+/g, "") !== ""){
                    diagnostic("instruction_limit", "The parser stopped before the end of the source", null);
                }
            }catch(ignored){
                diagnostic("instruction_limit", "The parser reached its limit and the remaining source could not be verified", null);
            }
        }
    }catch(e){
        diagnostic("assembler_error", String(e.javaException || e), null);
    }
    return result;
}
"""
