"""In-memory Redis-compatible store for local testing when Redis is unavailable"""
import asyncio
import time
from typing import Optional, Dict, Any, List
from collections import defaultdict

class MemoryRedis:
    """Redis-compatible in-memory store for local development"""
    
    def __init__(self):
        self.data: Dict[str, Any] = {}
        self.hashes: Dict[str, Dict[str, str]] = defaultdict(dict)
        self.sorted_sets: Dict[str, Dict[str, float]] = defaultdict(dict)
        self.ttls: Dict[str, float] = {}
        self._lock = asyncio.Lock()
    
    async def ping(self):
        return True
    
    async def hgetall(self, key: str) -> Dict[str, str]:
        self._cleanup_expired()
        return dict(self.hashes.get(key, {}))
    
    async def hset(self, key: str, mapping: dict):
        self.hashes[key].update(mapping)
    
    async def setex(self, key: str, seconds: int, value: str):
        self.data[key] = value
        self.ttls[key] = time.time() + seconds
    
    async def get(self, key: str) -> Optional[str]:
        self._cleanup_expired()
        return self.data.get(key)
    
    async def exists(self, key: str) -> int:
        self._cleanup_expired()
        return 1 if key in self.data or key in self.hashes or key in self.sorted_sets else 0
    
    async def delete(self, key: str):
        self.data.pop(key, None)
        self.hashes.pop(key, None)
        self.sorted_sets.pop(key, None)
        self.ttls.pop(key, None)
    
    async def incr(self, key: str) -> int:
        current = int(self.data.get(key, 0))
        current += 1
        self.data[key] = str(current)
        return current
    
    async def expire(self, key: str, seconds: int):
        if key in self.data or key in self.hashes or key in self.sorted_sets:
            self.ttls[key] = time.time() + seconds

    async def zadd(self, key: str, mapping: dict):
        for member, score in mapping.items():
            self.sorted_sets[key][member] = float(score)

    async def zcard(self, key: str) -> int:
        self._cleanup_expired()
        return len(self.sorted_sets.get(key, {}))

    async def zremrangebyscore(self, key: str, min_score: float, max_score: float) -> int:
        self._cleanup_expired()
        members = self.sorted_sets.get(key, {})
        to_delete = [
            member
            for member, score in members.items()
            if float(min_score) <= score <= float(max_score)
        ]
        for member in to_delete:
            members.pop(member, None)
        return len(to_delete)

    async def zrange(self, key: str, start: int, end: int, withscores: bool = False):
        self._cleanup_expired()
        items = sorted(self.sorted_sets.get(key, {}).items(), key=lambda item: (item[1], item[0]))
        if end == -1:
            selected = items[start:]
        else:
            selected = items[start : end + 1]
        if withscores:
            return selected
        return [member for member, _ in selected]
    
    async def close(self):
        pass
    
    def _cleanup_expired(self):
        now = time.time()
        expired = [k for k, v in self.ttls.items() if v < now]
        for k in expired:
            self.data.pop(k, None)
            self.hashes.pop(k, None)
            self.sorted_sets.pop(k, None)
            self.ttls.pop(k, None)

async def from_url(url: str, **kwargs):
    """Create memory redis instance (URL ignored for local testing)"""
    return MemoryRedis()
