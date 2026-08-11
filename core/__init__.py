"""Application core: data access, factories, validation strategies.

Three layers, deliberately kept apart:

* ``core.repositories`` -- where the data comes from (IESVE, SIA files).
* ``core.factories``    -- how a checker is built without naming it in code.
* ``core.strategies``   -- which algorithm validates (PDF or official).

ONE RULE ACROSS THE PACKAGE: **no module here imports ``iesve`` at module
level**. The implementations that need it defer the import, so the whole of
``core`` stays importable in continuous integration, with no VE licence. Break
that and the engine stops being testable without a licence, which is rule 4 of
the project.
"""
