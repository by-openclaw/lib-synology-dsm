# Ansible Collection Roadmap

Tracked in: [GitHub Issue #TBD](https://github.com/by-openclaw/lib-synology-dsm/issues)
ADR: TBD
Platform layer: Layer 3 (Automation) — depends on lib-synology-dsm stable

## Goal

Build an Ansible collection (`by_systems.synology_dsm`) that wraps `lib-synology-dsm`
for use in Ansible playbooks and roles. DevOps operators describe desired state in YAML;
the collection calls the lib's `ensure()` pattern and reports `changed`/`ok` back to Ansible.

## Planned modules

| Module | Wraps | State |
|---|---|---|
| `synology_dsm_share` | `ShareManager.ensure()` | 🗒️ Planned |
| `synology_dsm_user` | `UserManager.ensure()` | 🗒️ Planned |
| `synology_dsm_group` | `GroupManager.ensure()` | 🗒️ Planned |
| `synology_dsm_nfs` | `ShareManager.set_nfs_permission()` | 🗒️ Planned |
| `synology_dsm_filestation` | `FileStationManager.upload()/download()` | 🗒️ Planned |

## Example usage (target)

```yaml
- name: Ensure GitLab data share exists
  by_systems.synology_dsm.synology_dsm_share:
    host: "{{ nas_host }}"
    user: "{{ nas_user }}"
    password: "{{ nas_pass }}"
    name: by-gitlab
    state: present
    volume_path: /volume1
    description: "GitLab repository storage"
  register: share_result

- debug:
    msg: "Share {{ 'created' if share_result.changed else 'already existed' }}"
```

## Prerequisites before starting

- [ ] `lib-synology-dsm` stable release (v1.0.0) — current: v0.7.x (pre-stable)
- [ ] GitLab CE deployed (collection published to GitLab Package Registry)
- [ ] Ansible 2.15+ available in platform
- [ ] Integration test suite adapted for Ansible module testing (molecule)

## Testing plan

- Unit tests: mock DSMClient, verify module returns correct `changed`/`failed`
- Integration tests: molecule scenario against live NAS (same env vars as lib tests)
- CI: molecule + `ansible-lint` in GitHub Actions

## Blockers

1. lib-synology-dsm must reach v1.0.0 (no breaking API changes)
2. Vault AppRole auth must be implemented (lib ADR-0003 gap)
3. GitLab CE must be deployed for package publishing

## GitHub Issue

Track at: https://github.com/by-openclaw/platform-setup/issues (to be created)
