# Skill: uzigbee-docs-release

Purpose: Maintain docs, examples, and release packaging.

Use when:
- Editing docs/ or python/examples/
- Preparing pre-built firmware binaries
- Documenting build/flash steps or limitations

Docs checklist:
- Getting started
- Build instructions
- API reference
- Examples for coordinator/router/end device
- Memory and limitations
- License and redistribution notes (esp-zboss-lib)

Release checklist:
- Provide binaries per role (coordinator/router/end device)
- Include flash instructions and partition table
- Track ESP-IDF and MicroPython versions
- Record Zigbee lib versions

Note:
- Verify esp-zboss-lib licensing before publishing binaries.
