from typing import Dict, Any
from .models import Transaction, TransactionType

class SmartContract:
    def execute(self, transaction: Transaction, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the contract logic and returns the state updates.
        Should return a dictionary of state changes, or empty dict if no changes.
        """
        raise NotImplementedError

class CertificationContract(SmartContract):
    """
    Auto-issues a certificate if QA score is > 98%.
    """
    def execute(self, transaction: Transaction, state: Dict[str, Any]) -> Dict[str, Any]:
        if transaction.type != TransactionType.QA_PASS:
            return {}

        data = transaction.data
        qa_score = data.get("qa_score", 0)
        lot_id = data.get("lot_id")

        if not lot_id:
            return {}

        if qa_score > 98:
            # Auto-issue certificate
            # In a real system, this might trigger another transaction or update the global state
            return {
                "lot_id": lot_id,
                "status": "CERTIFIED",
                "certification_date": transaction.timestamp.isoformat(),
                "qa_score": qa_score,
                "certificate_id": f"CERT-{lot_id}-{int(qa_score)}"
            }
        return {}

class TransferContract(SmartContract):
    """
    Handles ownership transfer of a Seed Lot.
    """
    def execute(self, transaction: Transaction, state: Dict[str, Any]) -> Dict[str, Any]:
        if transaction.type != TransactionType.TRANSFER:
            return {}

        data = transaction.data
        lot_id = data.get("lot_id")
        new_owner = transaction.receiver

        if not lot_id or not new_owner:
            return {}

        # Here we would check if the sender actually owns the lot
        # based on the passed 'state'.
        # For simulation, we assume valid if the transaction exists.

        return {
            "lot_id": lot_id,
            "owner": new_owner,
            "transfer_date": transaction.timestamp.isoformat()
        }
