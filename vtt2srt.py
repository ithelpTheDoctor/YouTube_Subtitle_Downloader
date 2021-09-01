import re
from io import open
import html

_rec_tag_remove = re.compile('</?([^ibu]|(?!font))\\s*(\\.[^>]+)?>', re.I | re.S)
_rec_tag_clean_class = re.compile('<(\\w+)\\s*\\.[^>]+>', re.I | re.S)
_rec_tag_timestamp = re.compile('<\\s*[\\d:.]+\\s*>', re.I | re.S)

def html_unescape(s):
    return _ghp.unescape(s)


def clean_tags(s):
    s = _rec_tag_timestamp.sub('', s)
    s = _rec_tag_remove.sub('', s)
    s = _rec_tag_clean_class.sub('<\\1>', s)
    return s


def convert_vtt_to_srt_v3(vtt_text, out_file):
    
    file_content = vtt_text
    blocks = re.split('\\n\\n', file_content, flags=(re.S | re.U))
    counter = 0
    block_index = -1
    rec_cue = re.compile('([^\\n]+\\n)?([\\d:.]+ --> [\\d:.]+)( [^\\n]+)?\\n(.*?)$', flags=(re.S))
    with open(out_file, 'w', encoding='utf8') as (fo):
        for block in blocks:
            block_index += 1
            fnd = rec_cue.search(block)
            if not fnd:
                continue
            cue_id, cue_timing, cue_settings, cue_text = fnd.groups()
            fo.write('%i\n%s\n%s\n\n' % (
             counter,
             cue_timing.replace('.', ','),
             html.unescape(clean_tags(cue_text))))
            counter += 1