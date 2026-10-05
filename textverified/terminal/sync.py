"""Conservative complete reconciliation: no undocumented timestamp watermark."""
from collections import OrderedDict
import hashlib
import json
import heapq


def digest(message):
    material = {k: v for k, v in message.items() if k not in ("observed_at", "is_unread")}
    return hashlib.sha256(json.dumps(material, sort_keys=True).encode()).hexdigest()


class Feed:
    def __init__(self, adapter, max_bodies=10000):
        self.adapter = adapter
        self.digests = {}
        self.messages = OrderedDict()
        self.max_bodies = max_bodies
        self.baseline = False
        self.last_success_at = None
        self.possible_gap = False
        self.heap = []
        self.pinned = set()

    def reconcile(self, number=None, cancel=None, resource_id=None, resource_kind=None):
        # Commit identity metadata only as records are normalized. Failed scans
        # leave the last known data visible, and never declare complete coverage.
        for message in self.adapter.messages(
            number=number, cancel=cancel, resource_id=resource_id, resource_kind=resource_kind
        ):
            identity, current = message["id"], digest(message)
            previous = self.digests.get(identity)
            self.digests[identity] = current
            if (
                identity in self.messages
                or len(self.messages) < self.max_bodies
                or not self.heap
                or (message["created_at"] or "", identity) > self.heap[0][:2]
                or identity in self.pinned
            ):
                self.messages[identity] = message
                heapq.heappush(self.heap, (message["created_at"] or "", identity, current))
                while len(self.messages) > self.max_bodies + len(self.pinned):
                    _, oldest, version = heapq.heappop(self.heap)
                    if oldest in self.messages and self.digests[oldest] == version and oldest not in self.pinned:
                        del self.messages[oldest]
            if len(self.heap) > max(100, self.max_bodies * 2):
                self.heap = [
                    (m["created_at"] or "", i, self.digests[i])
                    for i, m in self.messages.items()
                    if i not in self.pinned
                ]
                heapq.heapify(self.heap)
            # Events can be consumed incrementally; callers commit output before
            # writing durable checkpoints. Body retention is independently bounded.
            if previous != current:
                yield ("sms.received" if previous is None else "sms.updated"), message
        if cancel and cancel.is_set():
            return
        from .models import now

        self.last_success_at = now()
        self.baseline = True

    def newest(self, limit=20):
        return sorted(self.messages.values(), key=lambda m: (m["created_at"] or "", m["id"]), reverse=True)[:limit]
