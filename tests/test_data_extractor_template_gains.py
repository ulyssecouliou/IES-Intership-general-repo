"""Internal gains must be read from the assigned thermal template when the room
level is empty.

Real-VE probe (2026-08-19): on VE 2025 ``VERoomData.get_internal_gains()``
returns ``[]`` for gains inherited from the assigned thermal template; the gains
live on the template (reached via ``get_casual_gains()``). The audit must resolve
the template so a properly templated model is not read as gain-free.
"""

from __future__ import annotations

import unittest

from swiss_sia.data_extractor import VEDataExtractor


class _Template:
    def __init__(self, gains, air_exchanges=()):
        self._gains = gains
        self._air = list(air_exchanges)

    def get_casual_gains(self):
        return list(self._gains)

    def get_air_exchanges(self):
        return list(self._air)


class _RoomData:
    def __init__(self, room_gains, template_handle, room_air=()):
        self._room_gains = room_gains
        self._room_air = list(room_air)
        self._general = {"thermal_template": template_handle}

    def get_internal_gains(self):
        return list(self._room_gains)

    def get_air_exchanges(self):
        return list(self._room_air)

    def get_general(self):
        return dict(self._general)


class _RaisingRoomData(_RoomData):
    def get_internal_gains(self):
        raise RuntimeError("VE member read-back failed")


class TemplateGainResolutionTests(unittest.TestCase):
    def _extractor(self, templates):
        extractor = VEDataExtractor.__new__(VEDataExtractor)
        extractor._templates = templates
        return extractor

    def test_empty_room_gains_fall_back_to_the_assigned_template(self):
        template_gains = [{"type_str": "people"}, {"type_str": "lighting"}]
        extractor = self._extractor({5: _Template(template_gains)})
        room = _RoomData(room_gains=[], template_handle=5)

        audit = extractor.get_internal_gains_audit(room)

        self.assertEqual(audit["items"], template_gains)
        self.assertEqual(audit["status"], "OK")
        self.assertIn("assigned template", audit["source"])

    def test_room_level_gains_take_priority_over_the_template(self):
        room_gains = [{"type_str": "people"}]
        extractor = self._extractor({5: _Template([{"type_str": "lighting"}])})
        room = _RoomData(room_gains=room_gains, template_handle=5)

        audit = extractor.get_internal_gains_audit(room)

        self.assertEqual(audit["items"], room_gains)
        self.assertEqual(audit["source"], "VERoomData.get_internal_gains()")

    def test_handle_resolves_by_string_key_too(self):
        template_gains = [{"type_str": "energy"}]
        extractor = self._extractor({"5": _Template(template_gains)})
        room = _RoomData(room_gains=[], template_handle=5)

        self.assertEqual(
            extractor.get_internal_gains_audit(room)["items"], template_gains
        )

    def test_no_gains_anywhere_stays_empty_and_ok(self):
        extractor = self._extractor({5: _Template([])})
        room = _RoomData(room_gains=[], template_handle=5)

        audit = extractor.get_internal_gains_audit(room)
        self.assertEqual(audit["items"], [])
        self.assertEqual(audit["status"], "OK")

    def test_read_back_error_is_fail_closed(self):
        extractor = self._extractor({5: _Template([{"type_str": "people"}])})
        room = _RaisingRoomData(room_gains=[], template_handle=5)

        audit = extractor.get_internal_gains_audit(room)
        self.assertEqual(audit["status"], "NOT_CHECKABLE")
        self.assertEqual(audit["items"], [])

    def test_empty_room_air_exchanges_fall_back_to_the_template(self):
        template_air = [{"type_str": "outdoor_air"}, {"type_str": "infiltration"}]
        extractor = self._extractor({5: _Template([], air_exchanges=template_air)})
        room = _RoomData(room_gains=[], template_handle=5, room_air=[])

        self.assertEqual(extractor.get_air_exchanges(room), template_air)

    def test_room_level_air_exchanges_take_priority(self):
        room_air = [{"type_str": "outdoor_air"}]
        extractor = self._extractor(
            {5: _Template([], air_exchanges=[{"type_str": "infiltration"}])}
        )
        room = _RoomData(room_gains=[], template_handle=5, room_air=room_air)

        self.assertEqual(extractor.get_air_exchanges(room), room_air)


if __name__ == "__main__":
    unittest.main()
