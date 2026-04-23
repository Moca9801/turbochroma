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
**untrusted** for size and shape. The library enforces string length limits
and exact decoded length before decompression. For strict validation
(invalid blob → error instead of falling back to Chroma’s distance), use
`QuantizedCollection(..., strict=True)` or `query(..., strict=True)`.

The optional **blob specification** string (see `DefaultBlobspecKey` in the public API) ties each stored base64 payload to a codec/parameter fingerprint. If present, it must match the current codec configuration or, in `strict` mode, re-ranking fails.
