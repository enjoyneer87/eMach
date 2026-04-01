import traceback

try:
    import plantuml
    print("OK", plantuml.__file__)
    print("attrs", [x for x in dir(plantuml) if "Plant" in x or "encode" in x or "deflate" in x])
except Exception:
    traceback.print_exc()
