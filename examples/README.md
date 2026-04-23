# Examples

Runnable examples that demonstrate `turbochroma`'s public API.

## Planned examples (land in subsequent commits)

| File | Demonstrates |
|---|---|
| `01_basic_usage.py` | Wrap an existing Chroma collection and query with SQ8 re-ranking. |
| `02_from_scratch.py` | Create a cuantized collection from day one, no float32 round-trip. |
| `03_migration_from_float32.py` | Migrate an existing float32 Chroma collection in place (calibrate + backfill blobs). |
| `04_custom_rotation.py` | Plug in a custom ``BaseRotation`` subclass. |

Each example is self-contained and runnable with:

```bash
python examples/01_basic_usage.py
```
