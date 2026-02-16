from typing import List, Dict, Any, Optional
from uuid import uuid4
from .chain import Blockchain
from .models import Transaction, TransactionType

class LedgerService:
    def __init__(self):
        # Initial validators
        # In a real scenario, these would be config driven
        validators = ["node1", "certifier1", "SYSTEM"]
        self.blockchain = Blockchain(validators=validators, node_id="certifier1")

    def record_transaction(self,
                           tx_type: TransactionType,
                           data: Dict[str, Any],
                           sender: str,
                           receiver: Optional[str] = None) -> Transaction:

        tx = Transaction(
            id=str(uuid4()),
            type=tx_type,
            data=data,
            sender=sender,
            receiver=receiver
        )

        self.blockchain.add_transaction(tx)

        # In a real system, mining happens periodically or on demand.
        # For this simulation, we'll auto-mine for instant feedback.
        self.blockchain.mine_block()

        return tx

    def get_ledger(self) -> List[Dict[str, Any]]:
        return self.blockchain.get_chain_data()

    def verify_integrity(self) -> bool:
        return self.blockchain.verify_chain()

    def get_state(self, lot_id: str) -> Optional[Dict[str, Any]]:
        return self.blockchain.state.get(lot_id)

# Singleton instance
ledger_service = LedgerService()
