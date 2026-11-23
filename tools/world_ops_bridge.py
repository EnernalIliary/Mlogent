"""Optional external server-operations extension; core has no policy implementation."""
import importlib
import json
import os
from pathlib import Path
import sys
import warnings

CORE_ROOT = Path(__file__).resolve().parents[1]
NATIVE_JS = r"""
if(this._mcpSnapshotPolicy){
 this._mcpSnapshotPolicy.interestEnabled=false;
 if(typeof this._mcpSnapshotPolicy.restoreOriginal==='function')this._mcpSnapshotPolicy.restoreOriginal();
}
sb.append('native synchronization; optional server operations extension not loaded');
"""


def player_limit(default=None, core_root=CORE_ROOT):
    try:
        value = json.loads((Path(core_root)/'out/_world/snapshot-profile.json').read_text(encoding='utf-8')).get('playerLimit')
        if isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 1024:
            return value
    except (OSError, ValueError, AttributeError):
        pass
    return default


def running_description(default, core_root=CORE_ROOT):
    """Allow an operator-owned profile to override runtime branding."""
    try:
        value = json.loads((Path(core_root)/'out/_world/snapshot-profile.json').read_text(encoding='utf-8')).get('runningDescription')
        if isinstance(value, str):
            return value
    except (OSError, ValueError, AttributeError):
        pass
    return default


def load_script(core_root=CORE_ROOT):
    profile_path = Path(core_root)/'out/_world/snapshot-profile.json'
    ops_root = os.environ.get('MLOGENT_OPS_ROOT')
    if not ops_root:
        try:
            ops_root = json.loads(profile_path.read_text(encoding='utf-8')).get('opsRoot')
        except (OSError, ValueError, AttributeError):
            pass
    if ops_root:
        resolved = str(Path(ops_root).resolve())
        if resolved not in sys.path:
            sys.path.insert(0, resolved)
    try:
        extension = importlib.import_module('mlogent_ops.world_network_policy')
        return extension.startup_script(profile_path=profile_path)
    except ModuleNotFoundError as exc:
        if ops_root or not (exc.name or '').startswith('mlogent_ops'):
            warnings.warn('Optional server operations unavailable: '+str(exc), RuntimeWarning)
    except Exception as exc:
        warnings.warn('Optional server operations failed; using native synchronization: '+str(exc), RuntimeWarning)
    return NATIVE_JS
