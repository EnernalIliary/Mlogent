"""Persistent world paths and owned daemon shutdown resources."""
from dataclasses import dataclass
from typing import Callable
from pathlib import Path
import json
import threading
import time

@dataclass(frozen=True)
class WorldPaths:
    root: str
    world: str
    data: str
    handshake: str
    log: str
    audit: str
    schematics: str
    doors: str
    feed: str

    @classmethod
    def from_root(cls, root):
        root=Path(root).resolve(); world=root/'out/_world'; data=world/'server'
        return cls(str(root),str(world),str(data),str(world/'daemon.json'),str(world/'server.log'),
                   str(world/'audit.log'),str(data/'config/schematics'),str(data/'doors.json'),str(world/'feed.json'))

class WorldRuntime:
    def __init__(self, world, paths, api=None):
        self.world=world
        self.paths=paths
        self.api=api
        self.api_thread=None
        self.stopped=threading.Event()
        self._lock=threading.Lock()
        self._closed=False
        self.cleanup_errors=[]

    def close(self):
        with self._lock:
            if self._closed: return
            self._closed=True
            self.stopped.set()
        world=self.world
        world._dir_stop=True
        threads=[getattr(world,'_dir_thread',None)]
        for state in getattr(world,'_mirrors',{}).values():
            state['feed']=None
            state['seq']=int(state.get('seq',0))+1
            threads.append(state.get('thread'))
        if self.api:
            if self.api_thread and self.api_thread.is_alive():
                try: self.api.shutdown()
                except Exception as exc: self.cleanup_errors.append(str(exc))
            try: self.api.server_close()
            except Exception as exc: self.cleanup_errors.append(str(exc))
        try: world.close()
        except Exception as exc: self.cleanup_errors.append(str(exc))
        deadline=time.monotonic()+3
        for thread in threads+[self.api_thread]:
            if thread and thread is not threading.current_thread():
                try:
                    thread.join(timeout=max(0,deadline-time.monotonic()))
                    if thread.is_alive(): self.cleanup_errors.append('thread did not stop: '+thread.name)
                except RuntimeError as exc: self.cleanup_errors.append(str(exc))
        path=Path(self.paths.handshake)
        try: path.unlink(missing_ok=True)
        except OSError as exc: self.cleanup_errors.append(str(exc))


@dataclass(frozen=True)
class ProjectionActionsServices:
    MINE_BLOCK: object
    REPLACE_MINE_JS: object
    DEMOLISH_JS: object
    MS_CLEAR_JS: object
    mirror_watch: Callable
    mirror_stop: Callable
    resync_builds: Callable
    sb_event: Callable
    chat: Callable


@dataclass(frozen=True)
class ProjectionDirectorServices:
    FRAME_LIVE_MAX: object
    FRAME_SWEEP_JS: object
    LIVE_COLOR: object
    MINE_BLOCK: object
    MINE_HITS_JS: object
    MINE_STATE_JS: object
    SB_SWEEP_JS: object
    _projs: Callable
    _sb_store: Callable
    chat: Callable
    end_projection: Callable
    frame_clear: Callable
    frame_paint: Callable
    project_at: Callable
    sb_clear: Callable
    sb_event: Callable
    sb_render: Callable


@dataclass(frozen=True)
class ProjectionControlServices:
    end_projection: Callable
    projection_director: Callable
    frame_clear: Callable
    frame_paint: Callable
    FRAME_LIST_JS: object
    mirror_stop: Callable
    _mirror_slot: Callable
    start_projection: Callable
    sb_event: Callable
    sb_render: Callable
    sb_clear: Callable
    SB_SWEEP_JS: object
    FRAME_LIVE_MAX: object
    sb_lines: Callable


@dataclass(frozen=True)
class WorldStartupServices:
    find_java: Callable
    pick_port: Callable
    create_world: Callable
    configure_chat: Callable
    mirror_watch: Callable
    projection_director: Callable
    make_handler: Callable


def write_audit(paths, operation, **fields):
    try:
        Path(paths.world).mkdir(parents=True, exist_ok=True)
        with open(paths.audit, 'a', encoding='utf-8') as stream:
            stream.write(json.dumps({'t':time.strftime('%Y-%m-%d %H:%M:%S'), 'op':operation, **fields},ensure_ascii=False)+'\n')
    except OSError:
        pass
