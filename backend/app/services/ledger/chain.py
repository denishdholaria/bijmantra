from typing import List, Dict, Any, Optional
import json
from .models import Block, Transaction, TransactionType
from .consensus import ProofOfAuthority
from .contracts import CertificationContract, TransferContract, SmartContract
from .merkle import calculate_merkle_root

class Blockchain:
    def __init__(self, validators: List[str], node_id: str):
        self.chain: List[Block] = []
        self.pending_transactions: List[Transaction] = []
        self.consensus = ProofOfAuthority(validators)
        self.node_id = node_id

        # World State (simulation of ledger state)
        # Key: Lot ID, Value: Dict of properties
        self.state: Dict[str, Any] = {}

        # Contracts
        self.contracts: List[SmartContract] = [
            CertificationContract(),
            TransferContract()
        ]

        # Create Genesis Block
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_tx = Transaction(
            id="0",
            type=TransactionType.SOWING,
            data={"message": "Genesis Block"},
            sender="SYSTEM",
            receiver="SYSTEM"
        )
        self.pending_transactions.append(genesis_tx)
        self.mine_block()

    def add_transaction(self, transaction: Transaction) -> bool:
        # Verify transaction (signature, etc - simplified)
        # In a real system, we'd verify the signature against the sender's public key
        self.pending_transactions.append(transaction)
        return True

    def mine_block(self) -> Optional[Block]:
        if not self.pending_transactions and len(self.chain) > 0:
            return None

        if not self.consensus.is_validator(self.node_id):
            raise PermissionError("This node is not authorized to create blocks.")

        last_block = self.chain[-1] if self.chain else None
        prev_hash = last_block.hash if last_block else "0"
        index = len(self.chain)

        # Calculate Merkle Root
        tx_hashes = [tx.calculate_hash() for tx in self.pending_transactions]
        merkle_root = calculate_merkle_root(tx_hashes)

        block = Block(
            index=index,
            transactions=list(self.pending_transactions),
            prev_hash=prev_hash,
            merkle_root=merkle_root,
            validator=self.node_id
        )
        block.hash = block.calculate_hash()

        # Validate and Append
        if self.consensus.validate_block(block):
            self.chain.append(block)
            self._execute_contracts(block.transactions)
            self.pending_transactions = []
            return block

        return None

    def _execute_contracts(self, transactions: List[Transaction]):
        for tx in transactions:
            for contract in self.contracts:
                updates = contract.execute(tx, self.state)
                if updates:
                    # Update state
                    lot_id = updates.get("lot_id")
                    if lot_id:
                        if lot_id not in self.state:
                            self.state[lot_id] = {}
                        self.state[lot_id].update(updates)

    def get_chain_data(self) -> List[Dict[str, Any]]:
        """Returns the chain data in a serializable format"""
        # Using json.loads(model_dump_json()) to ensure Pydantic serialization
        return [json.loads(b.model_dump_json()) for b in self.chain]

    def verify_chain(self) -> bool:
        """Verifies the integrity of the entire chain"""
        for i, block in enumerate(self.chain):
            if i == 0:
                continue # Skip genesis for now

            prev_block = self.chain[i-1]

            # Check prev_hash
            if block.prev_hash != prev_block.hash:
                return False

            # Check hash integrity
            if block.calculate_hash() != block.hash:
                return False

            # Check merkle root
            tx_hashes = [tx.calculate_hash() for tx in block.transactions]
            if calculate_merkle_root(tx_hashes) != block.merkle_root:
                return False

        return True
