# ADR-0005: Separate Repos Per Language

**Status:** Accepted
**Date:** 2026-03-30
**Deciders:** @yboujraf

## Context

As the platform tooling grows, the question arose: should a library have implementations in multiple languages in the same repo (e.g., Python + Go in `lib-synology-dsm`), or should each language be a separate repo?

## Decision

**Each library is language-specific. One language per repo.**

- `lib-synology-dsm` = Python only
- A future Go implementation would be `lib-synology-dsm-go`
- No multi-language folders within a single library repo

## Consequences

**Positive:**
- Clear dependency management per language ecosystem
- CI/CD tooling is language-specific (pytest vs go test)
- No confusion about which implementation to use for a given runtime

**Negative:**
- API parity must be maintained manually across language repos
- More repos to manage as the platform grows

## Notes

Different languages serve different performance profiles: Python for Ansible/automation/file processing, Go/C++ for real-time or high-throughput workloads.

## Compliance

| Framework | Control | Relevance |
|---|---|---|
| ISO 27001 | A.14.2.1 | Secure development — language-specific repos enable targeted CI/CD security gates |
