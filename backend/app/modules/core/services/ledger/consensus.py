
from .models import Block


class ProofOfAuthority:
    def __init__(self, validators: list[str]):
        self.validators: set[str] = set(validators)

    def is_validator(self, node_id: str) -> bool:
        return node_id in self.validators

    def validate_block(self, block: Block) -> bool:
        """
        Validates that the block was signed by an authorized validator.
        """
        if not self.is_validator(block.validator):
            return False

        # Check hash integrity
        calculated_hash = block.calculate_hash()
        return calculated_hash == block.hash

    def add_validator(self, validator_id: str):
        self.validators.add(validator_id)

    def remove_validator(self, validator_id: str):
        self.validators.discard(validator_id)
