import io
import re


def flex(phrase):
    return re.compile(r'\s+'.join(re.escape(part) for part in phrase.split()) )


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

assert n == 2, 'expected 2 ai_title derivations, saw %d' % n
src = '\n'.join(out)

old_desc = "(default on): '2:04 PM Person standing on front porch' instead of 'Person standing on front porch'"
new_desc = "(default on): the time is appended to the end of the title - 'Person standing on front porch at 2:04 PM'"
pat = flex(old_desc)
assert len(pat.findall(src)) == 1, 'blueprint description phrase not found exactly once'
src = pat.sub(lambda m: new_desc, src, count=1)

assert src.count("' at ' ~ time_label") == 2
io.open(bp, 'w', encoding='utf-8').write(src)
print('blueprint updated')

rd = 'README.md'
r = io.open(rd, encoding='utf-8').read()
old_rd = 'Titles render as `2:04 PM Person standing on front porch near driveway` instead of `Person standing on front porch near driveway`.'
new_rd = 'Titles render as `Person standing on front porch near driveway at 2:04 PM` - the time is appended to the end of the AI title, never in front of it.'
assert old_rd in r, 'readme bullet not found'
r = r.replace(old_rd, new_rd)
assert 'Person standing on front porch near driveway at 2:04 PM' in r
io.open(rd, 'w', encoding='utf-8').write(r)
print('readme updated')
