#!/usr/bin/env python3

import sys
import re
import io
from email import header

from simplelex import Token, Lex
from mailutils import decode_multiline_header

reply = Token(r'R[Ee]:\s?|[回答][复覆][：:]\s?', 're')
ottag = Token(r'\[OT\]\s?', 'ot', flags=re.I)
tag = Token(r'\[([\w._/ -]+)[^]]*\]\s?', 'tag')
lex = Lex((reply, ottag, tag))

def reformat(s):
  tokens, left = lex.parse(s)
  if not tokens:
    return

  isre = False
  tags = []
  ot = False
  usertag = []
  for tok in tokens:
    if tok.idtype == 're':
      isre = True
    elif tok.idtype == 'ot':
      ot = True
    elif tok.idtype == 'tag':
      tag = tok.match.group(1)
      tag_text = tag.lower()
      if tag_text.endswith('lug') or tag_text == 'wine-zh' or not tags:
        if tag_text not in tags:
          tags.append(tok.match.group(1))
      elif tag in tags:
        continue
      else:
        usertag.append(tok.data)
    else:
      sys.exit('error: unknown idtype: %s' % tok.idtype)

  if isre:
    ret = 'Re: '
  else:
    ret = ''
  if tags:
    tags.sort()
    ret += '[' + ']['.join(tags) + '] '
  if ot:
    ret += '[OT]'
  ret += ''.join(usertag) + left
  if ret != s:
    return ret

def stripSeq(input):
  subject = None
  while True:
    try:
      l = next(input)
    except StopIteration:
      return

    if l.startswith('Subject: '):
      # Subject appears
      subject = l
      continue
    elif subject and l[0] in ' \t':
      # Subject continues
      subject += l
    elif subject:
      # Subject ends
      s = subject[9:]
      s = decode_multiline_header(s)
      reformatted = reformat(s)
      if not reformatted:
        yield subject
      else:
        yield 'Subject: ' + header.Header(reformatted, 'utf-8').encode() + '\n'
      subject = None
      yield l
    elif l.strip() == '':
      yield l
      # mail body
      yield from input
    else:
      yield l

if __name__ == '__main__':
  stdout = io.TextIOWrapper(sys.stdout.buffer,
                            encoding='utf-8', errors='surrogateescape')
  stdin = io.TextIOWrapper(sys.stdin.buffer,
                           encoding='utf-8', errors='surrogateescape')
  stdout.writelines(stripSeq(iter(stdin)))
