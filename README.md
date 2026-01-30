# data_ingestion_pimcore
This project is a high-performance, fault-tolerant data ingestion service built using Python and FastAPI.
Its primary purpose is to reliably ingest large JSON and Excel datasets into PIM-Core while guaranteeing:
- Exactly-once chunk delivery semantics
- Resume-safe ingestion after crashes or restarts
- External acknowledgment–driven progress tracking
- Data integrity validation at chunk level
- High throughput without exhausting memory

This service is designed to solve real ingestion bottlenecks observed when pushing large datasets directly into PIM-Core.

## Problem Statement
PIM-Core ingestion APIs are typically:
- Network-bound
- Sensitive to payload size
- Not restart-safe
- Prone to duplicate or partial ingestion on failures

When ingesting large datasets (JSON / Excel), the traditional approach of:
- Loading full files into memory
- Sending monolithic payloads
- Retrying blindly on failures

leads to:
- Memory exhaustion
- Duplicate records
- Corrupted partial ingestion
- No way to resume from the last successful state

## Real-World Constraints
This system was designed under the following constraints:
- Files can be very large
- Network failures are expected
- PIM-Core is the source of truth for ingestion acknowledgment
- The ingestion service may crash or restart
- Duplicate data ingestion is unacceptable

This is **not a best-effort ingestion service** — correctness is prioritized over speed.

## Design goals 
The ingestion service explicitely guarantees
| Goal                 | Description                           |
| -------------------- | ------------------------------------- |
| Crash Resilience     | Service can restart without data loss |
| Resume Safety        | Continues from last ACKed chunk       |
| Exactly-Once         | No duplicate chunk ingestion          |
| External ACK Control | PIM-Core controls progress            |
| Memory Safety        | Never loads entire file               |
| High Throughput      | Streamed ingestion                    |

## High level architecture
```bash
Client
  |
  | POST /api/ingest
  |
FastAPI Controller
  |
  | Background Task
  |
Ingestion Service
  |
  | Stream → Chunk → Send
  |
PIM-Core Callback API
  |
  | ACK / Reject
  |
State Store (SQLite)

```

## Key Design Decisions
### Streaming Instead of Loading
Decision: 
- Use streaming parsers (ijson, fsspec) instead of loading files into memory.

Why:
- Prevents memory exhaustion
- Enables ingestion of arbitrarily large files
- Allows fine-grained chunk control

Alternative Rejected:
- json.load() — rejected due to memory risks.

### Chunk-Based Ingestion
Decision:
- Split data into chunks based on:
    - Number of records OR
    - Memory size (bytes)

Why:
- Avoids large payload failures
- Improves retry granularity
- Matches PIM-Core ingestion limits

Enforced Rule:
- Only one chunking strategy is allowed at a time.

### External ACK-Driven Progress
Decision: Chunks are marked complete only after PIM-Core ACKs them.

Why:
- PIM-Core is the final authority
- Prevents false positives
- Guarantees correctness under retries

Key Rule:
- No ACK = No progress saved

### Persistent Ingestion State
Decision:
- Persist ingestion progress in SQLite (ingestion_state.db).

Tracked data includes:
- Last ACKed chunk
- Total records ingested
- Completion status

Why:
- Enables resume after crashes
- Allows container restarts
- Makes ingestion idempotent

### Deterministic Chunk Integrity
Decision: Compute SHA-256 checksum using canonical JSON serialization.

Why:
- Prevents:
    - Partial transmission
    - Proxy truncation
    - Payload corruption
    - Duplicate chunk retries
    - Out-of-order chunk submission

### Retry With Safety
Decision: Retry chunk delivery up to 3 times, but only persist progress after ACK.

Why:
- Network failures are expected
- Blind retries without state would cause duplication
- ACK-first ensures correctness

## Ingestion Lifecycle
### Start
- Client calls /api/ingest
- Service generates:
    - file_id
    - ingestion_id
- Background ingestion begins

### Streaming & Chunking
- Data streamed record-by-record
- Chunk flushed when limits reached
- Each chunk is sent sequentially

### ACK Validation
- PIM-Core validates:
    - Chunk order
    - Checksum
    - Completeness
- ACK response determines progress

### Resume Support
- On restart:
    - Service reads last ACKed chunk
    - Skips already processed chunks
    - Continues safely

### Completion
- Final chunk sent
- Completion event sent
- State marked as COMPLETED

### Re-Ingestion vs Resume behaviour
| Mode         | Behavior                                      |
| ------------ | --------------------------------------------- |
| Resume       | Continues from last chunk                     |
| Re-Ingestion | Creates new execution with fresh ingestion ID |

This is controlling the behaviour:
```python
"re_ingestion": true
```

## Failures & Problems Solved
Duplicate Data on Retry
- Solved by: ACK-driven persistence + chunk IDs

Partial Chunk Transmission
- Solved by: Canonical checksum validation

Out-of-Order Delivery
- Solved by: Strict chunk_number sequencing

Service Crash Mid-Ingestion
- Solved by: Persistent ingestion state store

Memory Exhaustion
- Solved by: Streaming + bounded chunk sizes

## Why This Design Works
This system borrows ideas from:
- Distributed streaming systems
- Exactly-once delivery semantics
- Event-driven acknowledgments
- Idempotent processing patterns

But it is implemented pragmatically, without heavyweight infrastructure like Kafka.

