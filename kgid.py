def kgids(stat, regionid):
    d={}
    if stat == "kgid_prod":
        d = {
            # "1" : "-1001427022537", #production, do not touch
            # "2" : "-1001368152378", #production, do not touch
            # "3" : "-1001368152378", #production, do not touch
            # "4" : "-1001368152378", #production, do not touch
        }
    else: # testing ids, always use this for personal tests.
        d = {
            "1" : "-1001368152378",
            "2" : "-1001368152378",
            "3" : "-1001368152378",
            "4" : "-1001368152378",
        }

    return d[regionid]