import re
uuid_pattern = r'[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}'
s = "some text 3EAC7CFC-5DD6-4813-815A-3E6FCF5861B8 and more"
m = re.search(uuid_pattern, s)
print(m.group(0))

s2 = "another format 3eac7cfc-5dd6-4813-815a-3e6fcf5861b8 ..."
m2 = re.search(uuid_pattern, s2)
print(m2.group(0).upper())
