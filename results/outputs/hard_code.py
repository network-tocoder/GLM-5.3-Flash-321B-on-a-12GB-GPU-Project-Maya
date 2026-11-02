class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.data = {}
        self.head = None  # least recently used
        self.tail = None  # most recently used
        self.prev = {}
        self.next = {}

    def _remove(self, node):
        p, n = self.prev[node], self.next[node]
        if p is not None:
            self.next[p] = n
        else:
            self.head = n
        if n is not None:
            self.prev[n] = p
        else:
            self.tail = p

    def _append_front(self, node):
        self.prev[node] = None
        self.next[node] = self.head
        if self.head is not None:
            self.prev[self.head] = node
        self.head = node
        if self.tail is None:
            self.tail = node

    def _move_to_front(self, node):
        if self.head == node:
            return
        self._remove(node)
        self._append_front(node)

    def get(self, key):
        if key not in self.data:
            return -1
        self._move_to_front(key)
        return self.data[key]

    def put(self, key, value):
        if key in self.data:
            self.data[key] = value
            self._move_to_front(key)
            return
        if len(self.data) >= self.capacity:
            lru = self.head
            self._remove(lru)
            del self.data[lru]
            del self.prev[lru]
            del self.next[lru]
        self.data[key] = value
        self._append_front(key)
