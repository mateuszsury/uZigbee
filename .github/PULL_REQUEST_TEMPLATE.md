## Description

Brief description of the changes in this PR.

## Motivation

Why is this change needed? Link any related issues.

Closes #

## Changes

-

## Testing

- [ ] Host tests pass (`python -m pytest tests/test_import.py tests/test_network_api.py -q`)
- [ ] HIL tests pass (if runtime/bridge changes)
- [ ] New tests added for changed behavior

## Checklist

- [ ] Code follows project conventions (see `CONTRIBUTING.md`)
- [ ] Documentation updated for API or behavior changes
- [ ] No unnecessary memory allocations in hot paths
- [ ] C bridge changes are defensive (argument validation, clear errors)
- [ ] Callback safety preserved (scheduler-safe Zigbee callbacks)

## Breaking Changes

List any breaking changes and migration steps, or write "None".

## Risk & Rollback

Describe risk level and rollback strategy for low-level or runtime changes.
