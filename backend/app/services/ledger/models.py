from enum import Enum
from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, Field
import hashlib
import json

class TransactionType(str, Enum):
    SOWING = "SOWING"
    INSPECTION = "INSPECTION"
    HARVEST = "HARVEST"
    QA_PASS = "QA_PASS"
    CERTIFICATION = "CERTIFICATION"
    TRANSFER = "TRANSFER"

class Transaction(BaseModel):
    id: str
    type: TransactionType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: dict[str, Any]
    sender: str
    receiver: Optional[str] = None
    signature: Optional[str] = None

    def calculate_hash(self) -> str:
        # Simple hash of the transaction content
        # We use model_dump_json to ensure consistent serialization
        tx_content = self.model_dump_json(exclude={"signature"})
        return hashlib.sha256(tx_content.encode()).hexdigest()

class Block(BaseModel):
    index: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    transactions: List[Transaction]
    prev_hash: str
    merkle_root: str
    validator: str  # The node (Certifier) who signed this block
    hash: str = ""

    def calculate_hash(self) -> str:
        block_content = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp.isoformat(),
            "transactions": [tx.calculate_hash() for tx in self.transactions],
            "prev_hash": self.prev_hash,
            "merkle_root": self.merkle_root,
            "validator": self.validator
        }, sort_keys=True)
        return hashlib.sha256(block_content.encode()).hexdigest()
