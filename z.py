import iWell

token = iWell.init()
field = iWell.well_group(token)
print(field)
st = iWell.single_well_group(token,field['SOUTH TEXAS'])
print(sorted(st))