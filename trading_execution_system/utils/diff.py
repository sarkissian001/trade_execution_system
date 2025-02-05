def compute_differences(old: dict, new: dict) -> dict:
    diffs = {}
    for key in set(old.keys()).union(new.keys()):
        old_val = old.get(key)
        new_val = new.get(key)
        if old_val != new_val:
            diffs[key] = {"old": old_val, "new": new_val}
    return diffs
