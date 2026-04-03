import re

with open('app.py', 'r') as f:
    content = f.read()

# 1. Update in `extraer_uuid_de_archivo`
search_uuid_1 = r"uuid_pattern = r'[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}'"
replace_uuid_1 = r"uuid_pattern = r'[0-9A-Fa-f]{8}[-‐][0-9A-Fa-f]{4}[-‐][0-9A-Fa-f]{4}[-‐][0-9A-Fa-f]{4}[-‐][0-9A-Fa-f]{12}'"

content = content.replace(search_uuid_1, replace_uuid_1)

# We also need to normalize the extracted UUID so it always has standard hyphens
search_normalize_1 = """                if match:
                    return match.group(0).upper()"""
replace_normalize_1 = """                if match:
                    return match.group(0).upper().replace('‐', '-')"""
content = content.replace(search_normalize_1, replace_normalize_1)


# 2. Update in Egresos ZIP upload (Fallback checking)
search_uuid_2 = r"match_global = re.search(r'[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}', zip_name_raw)"
replace_uuid_2 = r"match_global = re.search(r'[0-9A-Fa-f]{8}[-‐][0-9A-Fa-f]{4}[-‐][0-9A-Fa-f]{4}[-‐][0-9A-Fa-f]{4}[-‐][0-9A-Fa-f]{12}', zip_name_raw)"

content = content.replace(search_uuid_2, replace_uuid_2)

search_normalize_2 = """                                uuid_str = match_global.group(0).upper()"""
replace_normalize_2 = """                                uuid_str = match_global.group(0).upper().replace('‐', '-')"""
content = content.replace(search_normalize_2, replace_normalize_2)


# 3. Update in Egresos process_egreso_file (PDF scanning)
search_uuid_3 = r"match = re.search(r'[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}', text)"
replace_uuid_3 = r"match = re.search(r'[0-9A-Fa-f]{8}[-‐][0-9A-Fa-f]{4}[-‐][0-9A-Fa-f]{4}[-‐][0-9A-Fa-f]{4}[-‐][0-9A-Fa-f]{12}', text)"

content = content.replace(search_uuid_3, replace_uuid_3)

search_normalize_3 = """                                                uuid_str = match.group(0).upper()"""
replace_normalize_3 = """                                                uuid_str = match.group(0).upper().replace('‐', '-')"""
content = content.replace(search_normalize_3, replace_normalize_3)


# 4. Update potential_uuid check
search_uuid_4 = r"if re.match(r'^[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}$', potential_uuid):"
replace_uuid_4 = r"if re.match(r'^[0-9A-Fa-f]{8}[-‐][0-9A-Fa-f]{4}[-‐][0-9A-Fa-f]{4}[-‐][0-9A-Fa-f]{4}[-‐][0-9A-Fa-f]{12}$', potential_uuid):"
content = content.replace(search_uuid_4, replace_uuid_4)

search_normalize_4 = """                                uuid_str = potential_uuid.upper()"""
replace_normalize_4 = """                                uuid_str = potential_uuid.upper().replace('‐', '-')"""
content = content.replace(search_normalize_4, replace_normalize_4)

with open('app.py', 'w') as f:
    f.write(content)
