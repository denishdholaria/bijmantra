import hashlib
from typing import List

def calculate_merkle_root(hashes: List[str]) -> str:
    """
    Calculates the Merkle Root for a list of hashes.
    """
    if not hashes:
        return ""

    if len(hashes) == 1:
        return hashes[0]

    new_level = []
    # Process pairs of hashes
    for i in range(0, len(hashes), 2):
        left = hashes[i]
        # If there is an odd number of hashes, duplicate the last one
        right = hashes[i+1] if i+1 < len(hashes) else left

        combined = left + right
        new_hash = hashlib.sha256(combined.encode()).hexdigest()
        new_level.append(new_hash)

    return calculate_merkle_root(new_level)
