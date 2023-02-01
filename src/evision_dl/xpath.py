def string_literal(s):
    # https://www.w3.org/TR/xpath-31/#id-literals
    if "'" in s:
        return '"' + s.replace('"', '""') + '"'
    else:
        return "'" + s.replace("'", "''") + "'"
