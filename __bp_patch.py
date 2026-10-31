import io
import hashlib
import sys

p = 'frigate_review_notification.yaml'
s = io.open(p, encoding='utf-8').read()

before = hashlib.sha256(s.encode()).hexdigest()
print('input sha256 :', before)
assert before == '1da4fdd97b57291c56e477ec88988268040bc9ea8d11d855209daf81855dfbc4', 'unexpected base file'


def rep(old, new, count=1):
    global s
    n = s.count(old)
    assert n == count, (n, count, old[:70])
    s = s.replace(old, new)


rep('''    update_sub_label:
      name: Update notification when sub-label changes''', '''    summary_max_chars:
      name: AI summary max length (characters)
      description: >-
        Truncate the AI shortSummary used as the notification body. 0 disables
        truncation. Frigate's review schema enforces 70-140 characters server
        side, so this only changes what the phone displays - never the model
        or the latency. 60-70 reads as roughly one line on a phone.
      default: 70
      selector:
        number:
          min: 0
          max: 140
          step: 5
          mode: box
    ai_title_timestamp:
      name: Prefix titles with the review start time
      description: >-
        Renders titles as '8:20 AM Person seen at Front Door' instead of
        'Person seen at Front Door'. The time comes from the review's own
        start_time (server side), never from the model.
      default: true
      selector:
        boolean:
    update_sub_label:
      name: Update notification when sub-label changes''')

rep('  genai_send_delay: !input genai_send_delay',
    '  genai_send_delay: !input genai_send_delay\n  summary_max_chars: !input summary_max_chars\n  ai_title_timestamp: !input ai_title_timestamp')

rep('  genai_title: ""\n  genai_summary: ""',
    '  genai_title: ""\n  genai_summary: ""\n  ai_title: ""\n  ai_summary: ""')

rep('''              genai_summary: "{{ metadata.get('shortSummary', '') }}"''', '''              genai_summary: "{{ metadata.get('shortSummary', '') }}"
              review_start: "{{ event.get('after', {}).get('start_time') or now().timestamp() }}"
              time_label: "{{ review_start | float(0) | timestamp_custom('%I:%M %p') | regex_replace('^0', '') }}"
              ai_title: "{{ (time_label ~ ' ') if ai_title_timestamp else '' }}{{ genai_title }}"
              ai_summary: "{{ genai_summary | truncate(summary_max_chars | int(0), false, '…', 0) if (genai_summary and (summary_max_chars | int(0)) > 0) else genai_summary }}"''')

rep('''              camera_name: "{{ event.get('after', {}).get('camera', '') }}"\n              notification_channel:''', '''              camera_name: "{{ event.get('after', {}).get('camera', '') }}"
              review_start: "{{ event.get('after', {}).get('start_time') or now().timestamp() }}"
              time_label: "{{ review_start | float(0) | timestamp_custom('%I:%M %p') | regex_replace('^0', '') }}"
              notification_channel:''', 1)

rep('''message: "{{ label }} detected - {{ camera_name }} at {{ event.get('after', {}).get('start_time', now().timestamp()) | timestamp_custom('%H:%M') }}"''',
    'message: "{{ label }} detected - {{ camera_name }} at {{ time_label }}"', 2)

rep('''                        title: ""\n                        message: "{{ message }}"''', '''                        title: "{{ (time_label ~ ' ') if ai_title_timestamp else '' }}{{ label }} detected"
                        message: "{{ camera_name }}{{ (' at ' ~ time_label) if not ai_title_timestamp else '' }}"''')

rep('''                              title: ""\n                              message: "{{ message }}"''', '''                              title: "{{ (time_label ~ ' ') if ai_title_timestamp else '' }}{{ label }} detected"
                              message: "{{ camera_name }}{{ (' at ' ~ time_label) if not ai_title_timestamp else '' }}"''')

rep('''                        title: "{{ genai_title }}"\n                        message: "{{ genai_summary if genai_summary else '' }}"''', '''                        title: "{{ ai_title }}"
                        message: "{{ ai_summary if ai_summary else '' }}"''')

rep('''                                  title: "{{ genai_title if (genai_done | default(false)) else '' }}"\n                                  message: "{{ genai_summary if genai_summary else message }}"''', '''                                  title: "{{ ai_title if (genai_done | default(false)) else '' }}"
                                  message: "{{ ai_summary if ai_summary else message }}"''', 2)

rep('''                            genai_summary: "{{ genai_meta.get('shortSummary', '') if got_genai else (genai_summary | default('')) }}"''', '''                            genai_summary: "{{ genai_meta.get('shortSummary', '') if got_genai else (genai_summary | default('')) }}"
                            ai_title: "{{ (time_label ~ ' ') if ai_title_timestamp else '' }}{{ genai_title }}"
                            ai_summary: "{{ genai_summary | truncate(summary_max_chars | int(0), false, '…', 0) if (genai_summary and (summary_max_chars | int(0)) > 0) else genai_summary }}"''')

rep('  name: Frigate Review Notification (2026-10-07)',
    '  name: Frigate Review Notification (2026-10-31)')

io.open(p, 'w', encoding='utf-8').write(s)

after = hashlib.sha256(s.encode()).hexdigest()
print('output sha256:', after)
if after != 'b860d7a18b2f2be223d59bf312d8f5ada93d7945f1a50781e449bf2d22d13ba9':
    print('ERROR: output does not match the validated blueprint', file=sys.stderr)
    sys.exit(1)
print('OK: blueprint patched and verified')
