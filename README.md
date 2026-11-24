<img src="docs/assets/mlogent-icon.png" alt="Mlogent world processor icon" width="64" height="64">

# Mlogent

**English** · [简体中文](README.zh-CN.md)

**Logic and blueprint tools for Mindustry, available through a CLI and MCP.**

Inspect processors inside an existing blueprint, recover readable jump labels,
check or simulate the code, preview an edit, and generate a new blueprint with
a revision you can inspect or roll back.

[Website & connection guide](https://mcp.iliary.life/?lang=en) ·
[Examples](https://mcp.iliary.life/?lang=en#examples) ·
[Releases](https://github.com/EnernalIliary/Mlogent/releases) ·
[Tool reference](tools/README.md)

## What you can do

- **Inspect blueprints:** list processors, coordinates, links and signed comment previews. Extract one processor or all of them as editable, labelled mlog.
- **Make targeted edits:** preview diffs, diagnostics and link checks, then replace a selected processor while preserving other blocks and configuration. A source hash protects against stale edits; successful injection creates a revision record.
- **Check and debug logic:** run static analysis, inspect control flow, execute programs with the Mindustry executor, and capture or compare instruction traces.
- **Explore mechanics:** search the included knowledge base and retrieve long results on demand.
- **Test power and world-processor behavior:** use native power grids, external supply curves, marker previews and scoped world-state probes.
- **Work with an online world:** supported deployments can inspect processor source, links and revisions, apply guarded edits and read back the result. Live-world tools use a separate entry point and depend on account permissions.

## Connect through MCP

### Hosted service

Use this **Streamable HTTP** endpoint in a compatible MCP client:

```text
https://mcp.iliary.life/mcp
```

Follow the client’s OAuth flow and use an available sign-in method. Tools and
limits depend on the account and deployed version. The website links to official
ChatGPT, Claude and Gemini CLI guides and includes copyable agent setup prompts.

In the game, `/mcp` opens a confirmation dialog linking to the website. The server
console command `mcpguide` prints connection instructions.

On deployments with a server Agent, administrators can use `/push <request>`
to queue a task and receive a private in-game reply. This requires the Ops inbox
relay and Agent integration; it does not automatically broadcast to a chat group.

### Local stdio

Configure your client to launch `python tools/mlog_mcp.py` from a local checkout.
Generic configuration; use the format supported by your client:

```json
{
  "mcpServers": {
    "mlogent": {
      "command": "/absolute/path/to/python",
      "args": ["/absolute/path/to/Mlogent/tools/mlog_mcp.py"]
    }
  }
}
```

Local stdio needs no remote OAuth or Bearer token. After connecting, call
`mlog_doctor` to inspect the runtime. For hosting, authentication, permissions and
rollback, see the [MCP deployment guide](docs/MCP部署.md).

## Quick start with the CLI

Use **Python 3.11 or newer**. Static checks, blueprint parsing and generation
need no third-party Python packages or Java.

```bash
git clone https://github.com/EnernalIliary/Mlogent.git
cd Mlogent
python tools/mlog.py doctor
python tools/mlog.py gen --logic "print 42" --name demo --binary demo.msch
python tools/mlog.py check demo.msch --cost
python tools/mlog.py extract-logic demo.msch -o demo-extracted.mlog
```

`gen` returns a blueprint paste code as well as the requested file. Named labels
become numeric jumps for delivery; their names are preserved in the signature
payload for later extraction.

To inspect existing work:

```bash
python tools/mlog.py parse demo.msch --labelize
python tools/mlog.py extract-logic demo.msch --index 0 -o processor.mlog
python tools/mlog.py extract-logic demo.msch --all --out-dir extracted
```

`extract-logic` accepts a `.msch` file, blueprint paste code or `.mlog` file, and
`-` for standard input. Processor indices start at zero. Use `--index` or `--all`
for multi-processor blueprints.

## A blueprint editing workflow

| Step | MCP tool | Purpose |
| --- | --- | --- |
| Inspect | `mlog_extract` | Read the processor inventory or extract labelled source. |
| Preview | `mlog_inject` with `preview: true` | Inspect the diff, diagnostics and link checks. |
| Apply | `mlog_inject` with `expected_sha256` | Pass the preview’s `source_sha256` back as a version guard; receive a new paste code and revision. |
| Review or roll back | `mlog_revision` | Inspect original code and checks, or recover the original paste code when the current blueprint matches the revision. |

Injection replaces one chosen processor, preserving the rest of the blueprint.
Revision records can contain original blueprints and source; keep their storage
private and persistent across upgrades.

## Simulation and Mindcode

| Capability | Additional requirements |
| --- | --- |
| Run mlog with the Mindustry executor | Mindustry server jar and Java 21+. Configure `MLOGSIM_JAR` and `MLOGSIM_JAVA` as needed. |
| Compile Mindcode | Mindcode jar and compatible Java. The preferred verified version is Mindcode 3.19.3, requiring Java 22+. Configure `MINDCODE_JAR` and `MINDCODE_JAVA`. |
| Extract a Mindcode draft | Mindcode runtime. Decompiled jumps may need manual restructuring before recompilation. |

```bash
python tools/mlogsim.py program.mlog --ticks 120
python tools/mindcode.py doctor
python tools/mindcode.py decompile program.mlog -o draft.mnd
```

MCP `mlog_sim` supports `power: "grid"` for native power networks,
`power_profile` for scheduled supply, `marker_preview` for marker state and PNG
output, `world_probe` for selected world state, and `trace_vars` for instruction
traces that can be inspected with `mlog_trace`. Simple SVGs can be converted to
world-processor marker code using `marker_from_svg`.

Simulation checks have a defined scope; they do not prove correct behavior in
every multiplayer world. Read the [observation contract](docs/观察与差分-契约.md),
[tool reference](tools/README.md) and [Mindcode integration notes](docs/Mindcode集成.md).
Missing optional runtimes leave static tools available.

## Languages

The project website and authorization pages support Simplified Chinese and
English. The website has a language switch; authorization language follows the
browser and is retained through provider sign-in.

On the hosted game server, Mlogent messages follow the client locale: Chinese
uses Simplified Chinese and other languages fall back to English. Use
`/language zh`, `/language en` or `/language auto` for Mlogent messages.
Wayzer uses its separate `/lang zh` or `/lang en` preference. Map names and
third-party map scripts are not automatically translated. Some plugin menus
contain hardcoded Chinese text and still display their original wording.

Detailed mechanism and tool documentation currently includes Chinese material;
this English README does not mean every document is translated.

## Downloads and development

[Releases](https://github.com/EnernalIliary/Mlogent/releases) provide four packages:

| Package | Contents |
| --- | --- |
| `toolchain` | Local CLI, rules, tests and documentation |
| `knowledge` | Mindustry mechanics, data tables and verification evidence |
| `skills` | Two independently installable DSH skills with generated tools |
| `mcp` | MCP server, knowledge base and deployment configuration |

Verify downloads with `SHA256SUMS.txt`. Game and Mindcode Java runtimes are not
bundled. Codex discovers project skills under `.agents/skills/`; DSH packages are
built from the same root tools.

Build the four release packages and `SHA256SUMS.txt` with
`python tools/build_release.py <version>`. Outputs are written to
`dist/release/v<version>/`; optional Java runtimes are supplied separately.

```bash
python gate.py
python tools/check_manifest.py
python tools/build_skills.py --verify-only
```

Checks requiring unavailable optional runtimes are reported as skipped. More
details: [documentation index](docs/README.md), [tool reference](tools/README.md),
[changelog](CHANGELOG.md).

## License and icon

Mlogent is licensed under [MIT](LICENSE). The project icon is the user-selected
Mindustry world-processor sprite from
[Anuken/Mindustry](https://github.com/Anuken/Mindustry/blob/master/core/assets-raw/sprites/blocks/logic/world-processor.png);
upstream artwork remains subject to its upstream terms.
