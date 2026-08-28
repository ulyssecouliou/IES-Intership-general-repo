"""Read-only inspection of partially created Swiss reference-model profiles.

Run this inside VEScripts before restoring the disposable VE project.  It does
not call any setter or save method and therefore cannot mutate the project.
"""

import pprint

import iesve


REFERENCE_PREFIX = "SIA_REF_"


def _identity(profile_id, profile):
    reference = getattr(profile, "reference", None)
    name = getattr(profile, "name", None)
    return str(reference or name or profile_id)


def run():
    project = iesve.VEProject.get_current_project()
    print("Project: {}".format(project.name))
    print("READ-ONLY PROFILE INSPECTION")
    found = 0
    for collection_index, collection in enumerate(project.profiles()):
        for profile_id, profile in collection.items():
            identity = _identity(profile_id, profile)
            if not identity.startswith(REFERENCE_PREFIX):
                continue
            found += 1
            print("--- profile {} ---".format(found))
            print("collection_index: {}".format(collection_index))
            print("profile_id: {!r}".format(profile_id))
            print("identity: {!r}".format(identity))
            print("python_type: {!r}".format(type(profile)))
            try:
                data = profile.get_data()
                print("data_type: {!r}".format(type(data)))
                print("data_repr:")
                pprint.pprint(data, width=140)
            except Exception as exc:
                print("get_data_error: {!r}".format(exc))
    print("Reference profiles found: {}".format(found))
    print("Inspection complete; no project data was changed.")


if __name__ == "__main__":
    run()
