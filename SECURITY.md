# Security

## Supported versions

Security fixes are applied to the current development branch and will be
released in the next tagged version. Use the latest pre-release or stable
release and pin dependencies in production.

## Reporting a vulnerability

If you believe you have found a security issue in this project, please
**do not** open a public issue with exploit details.

Preferred options:

- Open a [GitHub Security Advisory](https://github.com/Moca9801/turbochroma/security/advisories/new) (private report), or
- Email the maintainers: see `pyproject.toml` under `[project] authors` for
  a contact address.

Please include: affected version or commit, steps to reproduce, and impact
if known. We will acknowledge receipt and coordinate a fix and disclosure
timeline when appropriate.

## Metadata and untrusted inputs

Blobs for ADC re-ranking are read from Chroma `metadatas` and are treated as
**untrusted** for size and shape. The library enforces a maximum **declared**
compressed payload size (`MAX_COMPRESSED_BLOB_BYTES`, 1 MiB in current
releases), string length limits before decoding, and exact decoded length
after decoding. For strict validation
(invalid blob → error instead of falling back to Chroma’s distance), use
`QuantizedCollection(..., strict=True)` or `query(..., strict=True)`.

The optional **blob specification** string (see `DefaultBlobspecKey` in the public API) ties each stored base64 payload to a codec/parameter fingerprint. If present, it must match the current codec configuration or, in `strict` mode, re-ranking fails.

## Confidentiality and Chroma access control

`turbochroma` is **not** an encryption or field-level access layer. Quantized
blobs and metadata live in the same **Chroma** collections your application
already exposes: anyone with **read access to that collection** (or export of
its data) can read the **compressed** sidecar data and, where Chroma also stores
**original embeddings**, those vectors as configured by you.

For **highly sensitive** use cases (e.g. fine-grained PII, regulated health
records), the control plane is your **infrastructure and Chroma’s access model**:
isolation, authentication, tenant boundaries, and collection-level permissions
— not this library. Treat the stored blobs as **sensitive in proportion to the
sensitivity of the source embeddings**, and size your threats accordingly.

**Risk level (for threat modeling):** typically **low** for generic RAG, higher
where regulatory or policy obligations require strong confidentiality at rest or
in shared databases; in those cases, enforce **data residency and read policies**
independent of `turbochroma`.
