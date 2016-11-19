"""hypertext

Usage:
  hypertext conceptnet load [--database=DATABASE] FILENAME
  hypertext conceptnet search [--database=DATABASE] QUERY...
  hypertext wikidata load [--database=DATABASE] FILENAME
  hypertext wikidata search [--database=DATABASE] QUERY...
  hypertext it [--database=DATABASE] FILENAME

Options:
  -h --help               Show this screen
  --database=DATABASE     Database directory [Default: /tmp]
"""
import re
import sys
import zlib
from mmap import PAGESIZE

from docopt import docopt

from ajgudb import AjguDB
from ajgudb import Vertex


# This is a generator that yields *decompressed* chunks from
# a gzip file. This is also called a stream or lazy list.
# It's done like so to avoid to have the whole file into memory
def gzip_to_chunks(filename):
    decompressor = zlib.decompressobj(zlib.MAX_WBITS + 16)
    with open(filename,'rb') as f:
        chunk = f.read(PAGESIZE)

        while chunk:
          out = decompressor.decompress(chunk)
          yield out
          chunk = f.read(PAGESIZE)

        out = decompressor.flush()

        yield out

def chunks_to_rows(chunks):
    row = ''
    for chunk in chunks:
        for char in chunk:
            if char == '\n':
                yield row.split('\t')
                row = ''
            else:
                row += char
    if row:
        # yield the very last row if any
        yield row.split('\t')


COOL = re.compile(r'^/c/en/[\w_]+$')

def wordify(concept):
    return concept[len('/c/en/'):].replace('_', ' ')

if __name__ == '__main__':
    args = docopt(__doc__)
    graph = AjguDB(args['--database'], logging=True)
    if args['conceptnet'] and args['load']:
        edges = chunks_to_rows(gzip_to_chunks(args['FILENAME']))
        for edge in edges:
            _, relation, start, end, _ = edge
            # index only cool concepts
            if COOL.search(start) and COOL.search(end):
                with graph.transaction():
                    # get or create start
                    start = Vertex(ref=start, concept=wordify(start))
                    new, start = graph.get_or_create(start)
                    if new:
                        graph.index(start, start['concept'])
                    # get or create end
                    end = Vertex(ref=end, concept=wordify(end))
                    new, end = graph.get_or_create(end)
                    if new:
                        graph.index(end, end['concept'])

                    edge = start.link(end, relation=relation)
                    graph.save(edge)

    if args['conceptnet'] and args['search']:
        query = args['QUERY']
        query = ' '.join(query)
        for uid, score in graph.like(query):
            msg = '%s\t(uid: %s)\t(score: %s)'
            concept = graph.get(uid)['concept'] 
            print msg % (concept, uid, score)
    graph.close()