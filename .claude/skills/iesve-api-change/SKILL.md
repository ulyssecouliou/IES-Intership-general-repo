---
name: iesve-api-change
description: Develops or reviews IESVE VEScripts API integration safely across VE versions. Use for iesve objects, CDB, profiles, thermal templates, gbXML import, weather, rooms, surfaces, Apache systems, APS/Vista results, or runtime probes.
---

# IESVE API Change

1. Locate the API boundary in the gateway/extractor rather than importing `iesve` throughout domain code.
2. Check the bundled IESVE manual and the target installed version. Use current official IESVE documentation only when external access is approved.
3. Treat differences between VE releases as capabilities, not assumptions. Gate before mutation and report missing members explicitly.
4. Prefer documented setters/getters and perform immediate readback after every mutation.
5. Normalize enum layout variations in one adapter; do not spread version checks across workflow code.
6. Add pure-Python fakes that match documented signatures and cover missing-method, setter-failure and readback-mismatch paths.
7. Keep a real-runtime probe or qualification step for functionality that cannot be proven outside VE.
8. In the handoff, separate simulated validation from actual IESVE execution evidence.

Do not invent undocumented methods, automate VE UI interaction, or claim support for an untested installed release.
