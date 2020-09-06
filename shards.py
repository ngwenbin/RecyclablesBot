import random, os
from google.cloud import firestore

"""
Distributed shards counter to allow more than 1 writes per second.
"""

class Shard(object):
    def __init__(self):
        self._countfri = 0
        self._countsat = 0
        self._totalorders = 0
        self._totalusers = 0

    def to_dict(self):
        return {"count_fri": self._countfri,
                "count_sat": self._countsat,
                "totalorders": self._totalorders,
                "totalusers": self._totalusers}

class Counter(object):
    def __init__(self, num_shards):
        self._num_shards = num_shards

    def init_counter(self, doc_ref):
        col_ref = doc_ref.collection("shards")

        for num in range(self._num_shards):
            shard = Shard()
            col_ref.document(str(num)).set(shard.to_dict())

    def increment_friday(self, doc_ref):
        """Increment a randomly picked shard."""
        doc_id = random.randint(0, self._num_shards - 1)

        shard_ref = doc_ref.collection("shards").document(str(doc_id))
        return shard_ref.update({"count_fri": firestore.Increment(1)})

    def increment_saturday(self, doc_ref):
        """Increment a randomly picked shard."""
        doc_id = random.randint(0, self._num_shards - 1)

        shard_ref = doc_ref.collection("shards").document(str(doc_id))
        return shard_ref.update({"count_sat": firestore.Increment(1)})

    def increment_user(self, doc_ref):
        """Increment a randomly picked shard."""
        doc_id = random.randint(0, self._num_shards - 1)

        shard_ref = doc_ref.collection("shards").document(str(doc_id))
        return shard_ref.update({"totalusers": firestore.Increment(1)})

    def increment_order(self, doc_ref):
        """Increment a randomly picked shard."""
        doc_id = random.randint(0, self._num_shards - 1)

        shard_ref = doc_ref.collection("shards").document(str(doc_id))
        return shard_ref.update({"totalorders": firestore.Increment(1)})

    def decrement_user(self, doc_ref):
        """Increment a randomly picked shard."""
        doc_id = random.randint(0, self._num_shards - 1)

        shard_ref = doc_ref.collection("shards").document(str(doc_id))
        return shard_ref.update({"totalusers": firestore.Increment(-1)})

    def get_count(self, doc_ref):
        """Return a total count across all shards."""
        total_fri = 0
        total_sat = 0
        shards = doc_ref.collection("shards").list_documents()
        for shard in shards:
            total_fri += shard.get().to_dict().get("count_fri", 0)
            total_sat += shard.get().to_dict().get("count_sat", 0)
        return [total_fri, total_sat]

# shard_counter = Counter(10)

# def init_counters():
#     shard_counter.init_counter(db)

# def add_fri():
#     shard_counter.increment_friday(db)
#     print("Added friday!")

# def add_sat():
#     shard_counter.increment_saturday(db)
#     print("Added saturday!")

# def total():
#     totals = shard_counter.get_count(db)
#     print(totals)