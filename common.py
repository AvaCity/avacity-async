def get_prefix(location):
    prefix = location.split("_")[0]
    if prefix == "house":
        return "h"
    elif prefix == "work":
        return "w"
    elif prefix == "clan":
        return "c"
    else:
        return "o"
