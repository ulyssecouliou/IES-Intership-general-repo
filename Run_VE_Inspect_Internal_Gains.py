"""Focused read-only inspection of all current VE casual gains."""

import pprint

import iesve


def run():
    project = iesve.VEProject.get_current_project()
    print("Project: {}".format(project.name))
    print("READ-ONLY INTERNAL-GAIN INSPECTION")
    gains = list(project.casual_gains())
    print("Gain count: {}".format(len(gains)))
    for index, gain in enumerate(gains, start=1):
        print("--- gain {} ---".format(index))
        print("python_type: {!r}".format(type(gain)))
        print("id: {!r}".format(getattr(gain, "id", None)))
        try:
            pprint.pprint(dict(gain.get()), width=150)
        except Exception as exc:
            print("get_error: {!r}".format(exc))
    print("Inspection complete; no project data was changed.")


if __name__ == "__main__":
    run()
