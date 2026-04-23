"""turbochroma — drop-in vector compression for ChromaDB.

Public surface is **not yet defined** in this scaffold commit. The first
real classes (``QuantizedCollection``, ``SQ8Codec``, ``SparseRotation``,
``MetadataBlobStorage``, ``SidecarParquetStorage``) land in subsequent
commits; see ``CHANGELOG.md`` and ``docs/design/`` for the plan.
"""

from turbochroma._version import __version__

__all__ = ["__version__"]
