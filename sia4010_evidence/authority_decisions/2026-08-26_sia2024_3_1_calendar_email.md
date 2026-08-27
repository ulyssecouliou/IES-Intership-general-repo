# SIA 2024 category 3.1 annual-calendar authority decision

- Received: 2026-08-26
- Authority: Prof. Gerhard Zweifel
- Medium: direct written email response supplied by the validation candidate
- Scope: native annual profile calendar for SIA 4010 Test 2A and the Test 1
  diagnostic chain using SIA 2024:2021 category 3.1

## Questions and answers retained as controlled evidence

1. Weekly mapping: Monday through Friday are use days; Saturday and Sunday are
   rest days.
2. Calendar origin: 1 January is Saturday.
3. Exceptions: no public holidays or other exception days.
4. The 261 use days follow directly from the Saturday/Sunday rest-day mapping
   and the stated calendar origin.
5. Hour convention: source hour labels are ordinal hour-ending labels. Hour 1
   represents the interval after midnight through 01:00 (described in the
   response as 00:01-01:00).
6. Annual occupancy simultaneity: multiply the hourly occupancy values directly
   by 0.80.
7. Calendar length: non-leap, 365 days.

## Normalized implementation rule

- Calendar length: 365 days / 8760 hours
- 1 January weekday: Saturday
- Use weekdays: Monday-Friday
- Rest weekdays: Saturday-Sunday
- Holiday exceptions: none
- Hour labels: hour-ending ordinal values 1-24
- Occupancy transformation: `hourly_occupancy * 0.80`

This decision resolves the calendar and hour-boundary interpretation. Native
VE daily/weekly/yearly profile construction, assignment and read-back remain
technical qualification steps and are not SIA validation results.
