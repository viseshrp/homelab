"""Append-only ownership records for Cloudflare rules created by this installation."""
import contextlib
import fcntl
import json
import os
from pathlib import Path


class Ownership:
    def __init__(self, path):
        self.path = Path(path)

    @contextlib.contextmanager
    def locked(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(str(self.path) + '.lock', 'a', encoding='utf-8') as lock:
            os.chmod(lock.name, 0o600)
            fcntl.flock(lock, fcntl.LOCK_EX)
            yield

    def read(self):
        owned, intents = {}, {}
        if self.path.exists():
            with self.path.open(encoding='utf-8') as source:
                for line in source:
                    item = json.loads(line)
                    if item['event'] in ('adopt', 'created'):
                        owned[item['id']] = item
                    elif item['event'] == 'released':
                        owned.pop(item['id'], None)
                    elif item['event'] == 'intent':
                        intents[item['notes']] = item['ip']
        return owned, intents

    def append(self, item):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        with os.fdopen(fd, 'a', encoding='utf-8') as target:
            target.write(json.dumps(item, sort_keys=True) + '\n')
            target.flush()
            os.fsync(target.fileno())
