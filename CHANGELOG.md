# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-03-27

### Added
- `DSMClient` — session lifecycle management via context manager
- `ShareManager` — shared folder CRUD and NFS permission management
- `NFSManager` — NFS export rule management
- `UserManager` — user/group CRUD with disable-not-delete pattern
- Unit tests for auth flow
- `pyproject.toml` with hatchling build system
