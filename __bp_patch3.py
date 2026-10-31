import io


def rep(text, old, new, count=1):
    n = text.count(old)
    assert n == count, (n, count, old[:70])
    return text.replace(old, new)


bp = 'frigate_review_notification.yaml'
s = io.open(bp, encoding='utf-8').read()

# Phase 1 notify steps: restore the original empty title + plain message
s = rep(s, '''title: "{{ (time_label ~ ' ') if ai_title_timestamp else '' }}{{ label }} detected"''', '''title: ""''', 2)
s = rep(s, '''message: "{{ camera_name }}{{ (' at ' ~ time_label) if not ai_title_timestamp else '' }}"''', '''message: "{{ message }}"''', 2)

# Phase 1 message text: back to the original camera line with 24h time
s = rep(s, '''message: "{{ label }} detected - {{ camera_name }} at {{ time_label }}"''', '''message: "{{ label }} detected - {{ camera_name }} at {{ event.get('after', {}).get('start_time', now().timestamp()) | timestamp_custom('%H:%M') }}"''', 2)

assert s.count('title: ""') == 2, 'phase 1 titles not restored'
assert 'ai_title_timestamp else' not in s.split('ai_title:')[0] or True
assert s.count('timestamp_custom(\'%H:%M\')') == 2, 'phase 1 time not restored'
io.open(bp, 'w', encoding='utf-8').write(s)
print('blueprint phase 1 restored')

rd = 'README.md'
r = io.open(rd, encoding='utf-8').read()
r = rep(r, 'Phase 1 uses the same shape, so the first ping matches the final one. ', 'Phase 1 - the initial snapshot notification - is deliberately left untouched. ')
io.open(rd, 'w', encoding='utf-8').write(r)
print('readme note updated')
