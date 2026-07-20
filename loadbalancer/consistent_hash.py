"""
Implements a consistent hash map using a fixed-size circular array (M slots).
Each physical server is represented by K virtual servers to improve load
distribution evenness, per the assignment's Appendix B specification.
"""
class ConsistentHashMap:
    def __init__(self, M=512, K=9):
        self.M = M              # total slots
        self.K = K               # virtual servers per physical server
        self.slots = [None] * M  # slot -> server hostname

    def _H(self, i):
        # Hash function for request mapping
        return (3*i**2 + 5*i + 11) % self.M

    def _phi(self, i, j):
        # Hash function for virtual server mapping
        return (2*i**2 + 3*j**2 + j + 7) % self.M

    def _find_free_slot(self, start):
        idx = start
        count = 0
        while self.slots[idx] is not None:
            idx = (idx + 1) % self.M
            count += 1
            if count > self.M:
                raise Exception("Hash map is full")
        return idx

    def add_server(self, hostname, server_num):
        # server_num = a numeric id used only for hashing (0,1,2...)
        for j in range(self.K):
            slot = self._find_free_slot(self._phi(server_num, j))
            self.slots[slot] = hostname

    def remove_server(self, hostname):
        for i in range(self.M):
            if self.slots[i] == hostname:
                self.slots[i] = None

    def get_server(self, request_id):
        idx = self._H(request_id) % self.M
        count = 0
        while self.slots[idx] is None:
            idx = (idx + 1) % self.M
            count += 1
            if count > self.M:
                return None  # no servers available
        return self.slots[idx]
