"""Blob storage backends for compressed vectors.

Two backends are planned for v0.1:

- ``MetadataBlobStorage`` — base64 blobs inside Chroma metadata. Maximum
  compatibility, +33% storage overhead.
- ``SidecarParquetStorage`` — parquet file next to the Chroma DB. ~1.01x
  overhead, faster batch reads.

Empty in the scaffold commit; populated in subsequent refactors.
"""
