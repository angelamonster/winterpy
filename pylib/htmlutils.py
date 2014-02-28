import re
import copy

from lxml import html

def _br2span_inplace(el):
  for br in el.iterchildren(tag='br'):
    sp = html.Element('span')
    sp.text = '\n'
    sp.tail = br.tail
    el.replace(br, sp)

def extractText(el):
  el = copy.copy(el)
  _br2span_inplace(el)
  return el.text_content()

def iter_text_and_br(el):
  for i in el.iterchildren():
    if i.tag == 'br':
      yield '\n'
    if i.tail:
      yield i.tail

def un_jsescape(s):
    '''%xx & %uxxxx -> char, opposite of Javascript's escape()'''
    return re.sub(
        r'%u([0-9a-fA-F]{4})|%([0-9a-fA-F]{2})',
        lambda m: chr(int(m.group(1) or m.group(2), 16)),
        s
    )

def entityunescape(string):
  '''HTML entity decode'''
  from html.entities import entitydefs

  def sharp2uni(m):
    '''&#...; ==> unicode'''
    s = m.group(0)[2:-1]
    if s.startswith('x'):
      return chr(int('0'+s, 16))
    else:
      return chr(int(s))

  string = re.sub(r'&#[^;]+;', sharp2uni, string)
  string = re.sub(r'&[^;]+;', lambda m: entitydefs[m.group(0)[1:-1]], string)
  return string

def parse_document_from_requests(url, session, *, encoding=None):
  '''
  ``encoding``: override detected encoding
  '''
  r = session.get(url)
  if encoding:
    r.encoding = encoding

  # fromstring handles bytes well
  # http://stackoverflow.com/a/15305248/296473
  parser = html.HTMLParser(encoding=encoding or r.encoding)
  doc = html.fromstring(r.content, base_url=url, parser=parser)
  doc.make_links_absolute()

  return doc
