# MCP server, container form.
#
#   docker build -f deploy/Dockerfile -t mlogent-mcp .
#   docker run --rm -p 8765:8765 -e MLOG_MCP_TOKEN=... mlogent-mcp
#
# The image is the toolchain only: no game jar, no JRE.  `mlog_sim`,
# `mlog_validate` (simulation part), `mlog_diff` and `mindcode_compile` come back
# as `unsupported_environment` until you mount a runtime, which is deliberate --
# a 150 MB JDK in the base image would be dead weight for everyone who only
# wants the static analysis.  See deploy/README.md for the mount.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MLOG_MCP_TOKEN=""

WORKDIR /opt/mlogent

# Only what the server reads.  `git ls-files`-shaped, no caches, no test fixtures.
COPY tools/    ./tools/
COPY rules/    ./rules/
COPY data/     ./data/
COPY deploy/   ./deploy/

RUN useradd --system --create-home --uid 10001 mlog \
    && mkdir -p /opt/mlogent/out /opt/mlogent/runtime \
    && chown -R mlog:mlog /opt/mlogent
USER mlog

EXPOSE 8765
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,os;urllib.request.urlopen('http://127.0.0.1:8765/health',timeout=4)" || exit 1

# `--insecure` is required because the bind address is not loopback; the token
# still gates every request.  Refuse to start without one.
CMD ["sh", "-c", "test -n \"$MLOG_MCP_TOKEN\" || { echo 'MLOG_MCP_TOKEN is required' >&2; exit 2; }; exec python tools/mlog_mcp_http.py --bind 0.0.0.0 --port 8765 --token \"$MLOG_MCP_TOKEN\" --insecure"]
