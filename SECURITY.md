# Security Policy

## Supported versions

The latest released `0.x` line receives security fixes. Until `1.0`, only the most recent
minor version is supported.

## Reporting a vulnerability

Please report suspected vulnerabilities privately using **GitHub Security Advisories**
("Report a vulnerability" on the repository's Security tab) rather than opening a public
issue. If you cannot use that, email the maintainers at the address in the repository
metadata.

We aim to acknowledge reports within 3 business days and to ship a fix or mitigation for
confirmed issues promptly, coordinating disclosure with you.

## Scope notes for this library

`attestable` is a pure-Python library with **no runtime dependencies** and performs **no
network, filesystem, or subprocess I/O**. That eliminates whole classes of supply-chain
and injection risk. Two things are worth understanding when you rely on it:

- **Unkeyed attestations detect tampering, they do not prevent forgery.** Anyone can
  recompute a `sha256` digest. Use a **keyed** attestation (`attest(d, key=...)`) when you
  need it to be infeasible for a third party to produce a valid attestation. Manage that
  key like any other secret (it never touches attestable's storage — you supply it).
- **`parse_anchor` is a trust boundary.** It safely rejects malformed input, but the
  *resolver* you implement is responsible for treating anchor fields as untrusted when it
  queries your store (e.g. parameterize SQL — never interpolate `lineage_id`).
