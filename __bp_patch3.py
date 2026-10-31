import io

bp = 'frigate_review_notification.yaml'
src = io.open(bp, encoding='utf-8').read()
lines = src.split('\n')

ORIG = '''message: "{{ label }} detected - {{ camera_name }} at {{ event.get('after', {}).get('start_time', now().timestamp()) | timestamp_custom('%H:%M') }}"'''
CUR_TITLE = 'title: "{{ (time_label'
CUR_MSG = 'message: "{{ camera_name }}'
CUR_P1 = '''message: "{{ label }} detected - {{ camera_name }} at {{ time_label }}"'''

n_title = n_msg = n_p1 = 0
out = []
for line in lines:
    st = line.strip()
    ind = line[:len(line) - len(st)]
    if st.startswith(CUR_TITLE):
        out.append(ind + 'title: ""')
        n_title += 1
    elif st.startswith(CUR_MSG):
        out.append(ind + 'message: "{{ message }}"')
        n_msg += 1
    elif st == CUR_P1:
        out.append(ind + ORIG)
        n_p1 += 1
    else:
        out.append(line)

print('titles=%d messages=%d p1_text=%d' % (n_title, n_msg, n_p1))
assert (n_title, n_msg, n_p1) == (2, 2, 2), 'unexpected match counts'

io.open(bp, 'w', encoding='utf-8').write('\n'.join(out))
print('blueprint phase 1 restored')

rd = 'README.md'
r = io.open(rd, encoding='utf-8').read()
old_note = 'Phase 1 uses the same shape, so the first ping matches the final one. '
assert old_note in r, 'readme note not found'
r = r.replace(old_note, 'Phase 1 - the initial snapshot notification - is deliberately left untouched. ')
io.open(rd, 'w', encoding='utf-8').write(r)
print('readme note updated')
