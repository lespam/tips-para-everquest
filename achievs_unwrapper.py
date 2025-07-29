"""
@by Sweit from the Forsaken Destiny, Xegony
"""
import pandas as pd
import os
import re

# 📍 Locate target file
current_dir = os.getcwd()
print("Current directory:", current_dir)

#our_file = os.path.abspath('../Downloads/Swagly_xegony-Achievements3.txt')
our_file = os.path.abspath('../Downloads/Sweit_xegony-Achievements.txt')
print("Target file:", our_file)

# Load raw content
with open(our_file, 'r', encoding='utf-8') as f:
    raw_lines = f.readlines()

# Extract username from filename
filename = os.path.basename(our_file)
username = filename.split('_')[0]

# 🧹 Clean and standardize rows
data = [line.strip().split('\t') for line in raw_lines if line.strip()]
max_len = max(len(row) for row in data)
data_uniform = [row + [''] * (max_len - len(row)) for row in data]

# 🎯 Classify individual rows
# Rain of Fear: Progression - 1: Category
# I	Adventurer of Fear (Group) - 2: Achievement
# I		Harbinger Glask - Calling Phantasm - 3: Quest
# I		Noble Helssen - The Madness of King Tormax - 4: Complete / Incomplete
def classify_row(row):
    row_list = row.tolist() + [''] * (4 - len(row))
    col0, col1, col2, col3 = map(str.strip, row_list[:4])

    meta = {
        'Username': username,
        'Category': col0 if not re.match(r'^[CI]$', col0) else '',
        'CategoryType': '',
        'Achievement': col1,
        'Quest': col2,
        'Progress': '',
        'Type': ''
    }

    match = re.match(r'(\d+)/(\d+)', col3)
    if match:
        current, total = map(int, match.groups())
        meta['Progress'] = "C" if (current == total) else col3
        meta['Progress'] = "I" if (current == 0 and total == 1) else col3
    elif col0 in ['C', 'I']:
        meta['Progress'] = col0

    return pd.Series(meta)

# 🧵 Transform to structured DataFrame
df_raw = pd.DataFrame(data_uniform)
annotated_df = df_raw.apply(classify_row, axis=1)

ordered_cols = ['Username', 'Category', 'CategoryType', 'Achievement', 'Quest', 'Progress', 'Type']
final_df = annotated_df[ordered_cols].replace('', pd.NA)

# 🧬 Forward-fill core fields
final_df['Category'] = final_df['Category'].ffill()
final_df['CategoryType'] = final_df['CategoryType'].ffill()
final_df['Achievement'] = final_df['Achievement'].ffill()

# 💣 Remove rows that contain neither Achievement nor Quest
final_df = final_df.dropna(subset=['Quest'], how='all')

# 🎯 Extract CategoryType and tag Type accordingly
def extract_category_type_and_type(row, all_quests):
        types = []
        cat_type = ''
            
        category_val = row['Category']
        achiev_val = row['Quest']
        
        category_val = '' if pd.isna(category_val) else str(category_val)
        achiev_val = '' if pd.isna(achiev_val) else str(achiev_val)
        
        parts = re.split(r':\s*', str(category_val), maxsplit=1)
        if len(parts) == 2:
            types.extend([parts[0].strip(), parts[1].strip()])
            cat_type = parts[1].strip()
        else:
            types.append(parts[0].strip())
            cat_type = parts[0].strip()
        
        # Check if it's an achievement of achievements
        if any(all_quests.str.contains(achiev_val, case=False, na=False, regex=False)):
            types.append('Passive')
        return pd.Series({'CategoryType': cat_type, 'Type': ', '.join(types)})

final_df[['CategoryType', 'Type']] = final_df.apply(lambda row: extract_category_type_and_type(row, final_df['Achievement']), axis=1)

# 👀 Visual check of results
print("\n🔍 Sample structured view:\n")
print(final_df[['Category', 'CategoryType', 'Achievement', 'Quest', 'Progress', 'Type']].head())

# 💾 Save
CSV_FILENAME = 'achievements_database.csv'
output_path = os.path.abspath(CSV_FILENAME)

print("\nSaving to:", output_path)
final_df.to_csv(output_path, index=False, encoding='utf-8')
print("✅ Clean CSV saved as achievements_database.csv")
