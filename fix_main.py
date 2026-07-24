with open('app/main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_index = None
end_index = None

for i, line in enumerate(lines):
    if line.startswith('CAMPUS_STATE_SQL = """'):
        start_index = i
    if line.startswith('AGENT_INFORMATION_COLUMNS = {'):
        # Find the end of this dict
        for j in range(i, len(lines)):
            if lines[j].strip() == '}':
                end_index = j
                break
        break

if start_index is not None and end_index is not None:
    import_stmt = "from app.schema import (\n    CAMPUS_STATE_SQL, SPACE_SYSTEM_SQL, DEFAULT_SPACES, DEFAULT_ENV, ENV_COLUMN_TYPES,\n    AGENT_NEWS_SQL, EXTERNAL_INFORMATION_SQL, AGENT_PROFILE_SQL, PROFILE_COLUMN_TYPES,\n    SOCIAL_SYSTEM_SQL, BEHAVIOR_SYSTEM_SQL, RELATIONSHIP_DYNAMIC_COLUMNS,\n    LONG_TERM_GOAL_COLUMNS, AGENT_INFORMATION_COLUMNS\n)\n"
    
    new_lines = lines[:start_index] + [import_stmt] + lines[end_index+1:]
    
    with open('app/main.py', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print("Replaced lines {} to {} with imports.".format(start_index, end_index))
else:
    print("Could not find start or end index")
