import pytest
from backend.app.services.ledger.models import Transaction, TransactionType, Block
from backend.app.services.ledger.merkle import calculate_merkle_root
from backend.app.services.ledger.chain import Blockchain
from backend.app.services.ledger.service import ledger_service, LedgerService

def test_merkle_tree():
    hashes = ["a", "b", "c", "d"]
    # a+b -> h1
    # c+d -> h2
    # h1+h2 -> root
    root = calculate_merkle_root(hashes)
    assert root != ""
    assert isinstance(root, str)

    # Same input same output
    assert calculate_merkle_root(hashes) == root

    # Different input different output
    assert calculate_merkle_root(["a", "b", "c", "e"]) != root

def test_transaction_hashing():
    tx = Transaction(
        id="1",
        type=TransactionType.SOWING,
        data={"test": "data"},
        sender="sender"
    )
    h = tx.calculate_hash()
    assert h

    # Verify hash changes with content
    tx2 = Transaction(
        id="1",
        type=TransactionType.SOWING,
        data={"test": "data2"},
        sender="sender"
    )
    assert tx.calculate_hash() != tx2.calculate_hash()

def test_blockchain_mining_and_verification():
    chain = Blockchain(validators=["node1"], node_id="node1")

    # Add transaction
    tx = Transaction(
        id="1",
        type=TransactionType.SOWING,
        data={"lot_id": "L1"},
        sender="farm"
    )
    chain.add_transaction(tx)

    # Mine
    block = chain.mine_block()
    assert block is not None
    assert len(chain.chain) == 2 # Genesis + 1
    assert block.index == 1

    # Verify integrity
    assert chain.verify_chain() is True

    # Tamper with chain: Modify transaction data in memory
    # Note: Pydantic models are mutable by default unless frozen=True
    chain.chain[1].transactions[0].data["lot_id"] = "L2_FAKE"

    # verify_chain calculates hashes based on CURRENT content of transactions
    # and compares with stored hashes in Block.
    # The Block hash is calculated based on transaction hashes.
    # So if we change transaction data, tx.calculate_hash() changes.
    # Then block.transactions[0].calculate_hash() changes.
    # Then verification checks if merkle root matches.
    # The stored merkle root in block is old. The calculated one will be new.
    # So it should fail.

    assert chain.verify_chain() is False

def test_smart_contracts():
    chain = Blockchain(validators=["node1"], node_id="node1")

    # QA Pass
    tx = Transaction(
        id="2",
        type=TransactionType.QA_PASS,
        data={"lot_id": "LOT-123", "qa_score": 99},
        sender="QA_LAB"
    )
    chain.add_transaction(tx)
    chain.mine_block()

    # Check state
    assert "LOT-123" in chain.state
    assert chain.state["LOT-123"]["status"] == "CERTIFIED"
    assert chain.state["LOT-123"]["qa_score"] == 99

def test_ledger_service_instance():
    # Use a fresh instance to avoid side effects from global singleton if used in other tests
    # But here we can just use the class

    # Re-initialize to clear previous state if any
    service = LedgerService()

    # Record transaction
    tx = service.record_transaction(
        TransactionType.HARVEST,
        {"quantity": 100},
        "farmer_john"
    )
    assert tx.type == TransactionType.HARVEST

    # Check if added to chain
    chain_data = service.get_ledger()
    # Genesis block + block with harvest tx
    assert len(chain_data) >= 2

    last_block = chain_data[-1]
    assert last_block["transactions"][0]["id"] == tx.id
