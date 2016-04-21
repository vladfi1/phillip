def getField(obj, field):
    if isinstance(field, str):
        return getattr(obj, field)
    else:
        return obj[field]

def setField(obj, field, val):
    if isinstance(field, str):
        setattr(obj, field, val)
    else:
        obj[field] = val

def getPath(obj, path):
    for field in path:
        obj = getField(obj, field)
    return obj

# doesn't work with empty path :(
def setPath(obj, path, val):
    obj = getPath(obj, path[:-1])
    setField(obj, path[-1], val)

