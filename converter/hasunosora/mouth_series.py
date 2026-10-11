"""Canonicalise complete native mouth series while retaining eye pairings."""

from copy import deepcopy


LIPS = ("close", "a", "i", "u", "e", "o")


def deduplicate_mouth_series(component):
    """Return a copy; unrelated model metadata and geometry are unchanged.

    Series identity includes every lip and its control endpoints. Equal single
    lip shapes in otherwise different series do not merge their states.
    """
    result = deepcopy(component)
    groups = result.get("expressionGroups", [])
    mouths = [group for group in groups if group.get("type") == "mouth"]
    if not mouths:
        return result
    if len(mouths) != 1:
        raise ValueError("Hasunosora requires one native mouth group")
    mouth = mouths[0]
    recipes = {pose["name"]: pose["targets"] for pose in result["morphPoses"]}

    def resolved(coefficients):
        weights = {}
        for name, coefficient in coefficients.items():
            for node, shapes in recipes[name].items():
                for shape, value in shapes.items():
                    key = (node, shape)
                    weights[key] = weights.get(key, 0) + coefficient * value
        return tuple(sorted((node, shape, value) for (node, shape), value in weights.items() if value != 0))

    def state_signature(state):
        base = state["poses"]
        controls = state.get("controls", {})
        endpoints = []
        for name, target in sorted(controls.items()):
            if name == "visemes":
                # Mouth visemes replace the complete base recipe, unlike the
                # sparse blink/speech overrides: an omitted coefficient is zero.
                endpoints.append((name, tuple((lip, resolved(mapping))
                                             for lip, mapping in sorted(target.items()))))
            else:
                endpoints.append((name, resolved(base | target)))
        return resolved(base), tuple(endpoints)

    series = {}
    for state in mouth["states"]:
        name = state["name"]
        prefix, separator, lip = name.rpartition("/")
        if separator and lip in LIPS and "visemes" in state.get("controls", {}):
            series.setdefault((prefix, "vowels"), {})[lip] = state
        else:
            series[(name, "fixed")] = {"fixed": state}

    canonical = {}
    aliases = {}
    kept = []
    pairings = {}
    for (name, kind), states in series.items():
        order = LIPS if kind == "vowels" else ("fixed",)
        if set(states) != set(order):
            raise ValueError(f"Incomplete Hasunosora mouth series: {name}")
        signature = (kind, tuple(state_signature(states[lip]) for lip in order))
        representative = canonical.get(signature)
        if representative is None:
            representative = states
            canonical[signature] = states
            kept.extend(states[lip] for lip in order)
        for lip in order:
            aliases[states[lip]["name"]] = representative[lip]["name"]
        pairings[name] = {
            "closed": representative["close" if kind == "vowels" else "fixed"]["name"],
            "open": representative["a" if kind == "vowels" else "fixed"]["name"],
        }
    mouth["states"] = kept
    for group in groups:
        if group.get("type") == "eye":
            for state in group["states"]:
                if state["name"] in pairings:
                    state["mouth"] = pairings[state["name"]]
    default = result.get("defaultExpression", {})
    for key in ("closed", "open"):
        if key in default:
            default[key] = aliases[default[key]]

    # Retained controls already refer to the representative series recipes.
    # Prune only unreferenced mouth recipes; eye/other recipes remain intact.
    referenced = set()
    for group in groups:
        for state in group["states"]:
            referenced.update(state["poses"])
            for control, mapping in state.get("controls", {}).items():
                if control == "visemes":
                    for endpoint in mapping.values():
                        referenced.update(endpoint)
                else:
                    referenced.update(mapping)
    result["morphPoses"] = [pose for pose in result["morphPoses"]
                            if not pose["name"].startswith("mouth.") or pose["name"] in referenced]
    return result
