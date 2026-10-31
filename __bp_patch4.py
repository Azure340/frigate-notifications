import io

bp = 'frigate_review_notification.yaml'
src = io.open(bp, encoding='utf-8').read()
lines = src.split('\n')

CUR = 'ai_title: "{{ (time_label'
NEW = '''ai_title: "{{ genai_title }}{{ (' at ' ~ time_label) if ai_title_timestamp else '' }}"'''

n = 0
out = []
for line in lines:
    st = line.strip()
    ind = line[:len(line) - len(st)]
    if st.startswith(CUR):
        out.append(ind + NEW)
        n += 1
    else:
        out.append(line)

print('ai_title lines rewritten: %d' % n)
assert n == 2, 'expected 2 ai_title derivations'

src = '\n'.join(out)

OLD_BP = "(default on): '2:04 PM Person standing on front porch' instead of 'Person standing on front porch'"
NEW_BP = "(default on): the time is appended to the end of the title - 'Person standing on front porch at 2:04 PM'"
assert OLD_BP in src, 'blueprint description text not found'
src = src.replace(OLD_BP, NEW_BP)

assert src.count("' at ' ~ time_label") == 2
io.open(bp, 'w', encoding='utf-8').write(src)
print('blueprint updated')

rd = 'README.md'
r = io.open(rd, encoding='utf-8').read()
OLD_RD = 'Titles render as `2:04 PM Person standing on front porch near driveway` instead of `Person standing on front porch near driveway`.'
NEW_RD = 'Titles render as `Person standing on front porch near driveway at 2:04 PM` - the time is appended to the end of the AI title, never in front of it.'
assert OLD_RD in r, 'readme bullet not found'
r = r.replace(OLD_RD, NEW_RD)
io.open(rd, 'w', encoding='utf-8').write(r)
print('readme updated')
