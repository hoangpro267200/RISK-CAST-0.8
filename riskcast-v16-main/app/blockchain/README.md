# Blockchain-based Immutable Audit Trail

Immutable, cryptographically-verified audit trail using Merkle trees and public blockchain anchoring.

## Features

1. **Merkle Tree**: Efficient verification of audit entries
2. **Block-based Chain**: Groups entries into blocks for efficiency
3. **Public Anchoring**: Anchor blocks to Ethereum/Bitcoin
4. **Proof Generation**: Generate cryptographic proofs for entries
5. **Verification**: Verify individual entries, blocks, and chain integrity
6. **Audit Certificates**: Generate shareable verification certificates

## Architecture

### Merkle Tree
- Binary Merkle tree for efficient inclusion proofs
- Incremental Merkle tree for append-only logs
- SHA-256 hashing

### Audit Chain
- Entries are grouped into blocks (default: 100 entries/block)
- Each block contains:
  - Merkle root of all entries
  - Previous block hash (chain linking)
  - Block hash (integrity)
- Blocks are immutable once created

### Anchoring
- Ethereum: Anchor via smart contract
- Bitcoin: OP_RETURN (planned)
- Periodic anchoring service

### Verification
- Entry-level: Verify hash and Merkle proof
- Block-level: Verify hash, chain link, Merkle root
- Chain-level: Verify entire chain integrity
- Certificate generation for external verification

## Usage

### Logging Events

```python
from app.blockchain.audit_chain import AuditChain
from app.database import get_db

db = next(get_db())
chain = AuditChain(db)

entry_id = chain.log_event(
    event_type="quote.created",
    entity_type="quote",
    entity_id="quote-123",
    action="created",
    actor_id="user-456",
    actor_type="user",
    data={"premium": 5000, "cargo_value": 100000}
)
```

### Creating Blocks

Blocks are automatically created when `BLOCK_SIZE` entries accumulate, or manually:

```python
block = chain.create_block()
```

### Verification

```python
from app.blockchain.verification import VerificationService

verifier = VerificationService(db)

# Verify entry
result = verifier.verify_entry(entry_id)
print(f"Verified: {result.verified}, Errors: {result.errors}")

# Verify block
result = verifier.verify_block(block_number=0)

# Verify chain
result = verifier.verify_chain_integrity()

# Generate certificate
cert = verifier.generate_audit_certificate(entry_id)
```

### Anchoring

```python
from app.blockchain.anchoring import AnchoringService, EthereumAnchor

eth_anchor = EthereumAnchor(
    rpc_url="https://mainnet.infura.io/v3/YOUR_KEY",
    contract_address="0x...",
    private_key="0x..."  # Keep secure!
)

service = AnchoringService(db, ethereum_anchor=eth_anchor)

# Anchor pending blocks
tx_hashes = await service.anchor_pending_blocks(batch_size=10)
```

### Merkle Proofs

```python
from app.blockchain.merkle_tree import MerkleTree

# Build tree
tree = MerkleTree()
root = tree.build(["data1", "data2", "data3"])

# Get proof
proof = tree.get_proof(index=0)

# Verify proof
is_valid = MerkleTree.verify_proof(proof)
```

## Database Models

### audit_blocks
- `block_id`: UUID
- `block_number`: Sequential number
- `previous_hash`: Hash of previous block
- `merkle_root`: Merkle root of entries
- `entries_count`: Number of entries
- `entries_data`: JSON array of entry summaries
- `block_hash`: SHA-256 hash of block
- `anchored`: Boolean (0/1)
- `anchor_tx_hash`: Ethereum transaction hash

### audit_entries
- `entry_id`: UUID
- `block_id`: FK to audit_blocks (nullable until included)
- `event_type`: Event type
- `entity_type`: Entity type
- `entity_id`: Entity ID
- `action`: Action performed
- `actor_id`: Actor ID
- `actor_type`: Actor type
- `data`: JSON payload
- `metadata`: JSON metadata
- `entry_hash`: SHA-256 hash
- `timestamp`: Event timestamp

## Configuration

### Environment Variables

```bash
# Ethereum anchoring (optional)
ETHEREUM_RPC_URL=https://mainnet.infura.io/v3/YOUR_KEY
ANCHOR_CONTRACT_ADDRESS=0x...
ANCHOR_PRIVATE_KEY=0x...  # Keep secure!

# Bitcoin anchoring (optional)
BITCOIN_RPC_URL=http://localhost:8332
BITCOIN_RPC_USER=user
BITCOIN_RPC_PASSWORD=password
```

## Dependencies

- `web3` (optional, for Ethereum anchoring): `pip install web3`
- Standard library: `hashlib`, `json`, `uuid`

## Security Notes

1. **Private Keys**: Never commit private keys. Use environment variables or secrets management.
2. **Anchoring Costs**: Ethereum transactions cost gas. Consider batching.
3. **Verification**: Always verify proofs before trusting audit data.
4. **Immutable**: Once entries are in blocks, they cannot be modified.

## Migration

Create database tables:

```python
from app.blockchain.audit_chain import AuditBlockModel, AuditEntryModel
from app.database import Base, engine

Base.metadata.create_all(bind=engine)
```

Or use Alembic:

```bash
alembic revision --autogenerate -m "Add blockchain audit tables"
alembic upgrade head
```
