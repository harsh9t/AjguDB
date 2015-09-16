#!/usr/bin/env python
import os
from shutil import rmtree
from unittest import TestCase

from ajgudb import AjguDB

from ajgudb import gremlin


class DatabaseTestCase(TestCase):

    def setUp(self):
        try:
            rmtree('/tmp/ajgudb')
        except OSError:
            pass
        os.makedirs('/tmp/ajgudb')
        self.graph = AjguDB('/tmp/ajgudb')

    def tearDown(self):
        self.graph.close()
        rmtree('/tmp/ajgudb')

    def test_create_vertex(self):
        v = self.graph.vertex.create('test')
        self.assertTrue(v)

    def test_idem(self):
        v = self.graph.vertex.create('test')
        idem = self.graph.vertex.get(v.uid)
        self.assertEqual(v, idem)

    def test_get_or_create(self):
        v = self.graph.vertex.get_or_create('test')
        self.assertIsNotNone(v)

    def test_get_or_create_twice(self):
        v1 = self.graph.vertex.get_or_create(label='test', key='value')
        v2 = self.graph.vertex.get_or_create(label='test', key='value')
        self.assertEqual(v1, v2)

    def test_create_and_get_vertex(self):
        v1 = self.graph.vertex.create('test')
        v2 = self.graph.vertex.get(v1.uid)
        self.assertTrue(v1, v2)

    def test_create_with_properties_and_get_vertex(self):
        v = self.graph.vertex.create('test', key='value')
        v = self.graph.vertex.get(v.uid)

        self.assertEqual(v['key'], 'value')

    def test_create_modify_and_get_edge(self):
        start = self.graph.vertex.create('test')
        end = self.graph.vertex.create('test')
        edge = start.link('edge', end, hello='world')

        edge = self.graph.edge.get(edge.uid)

        self.assertTrue(edge['hello'] == 'world')
        self.assertEqual(edge.start(), start)
        self.assertEqual(edge.end(), end)

    def test_create_edge_and_check_vertices_edges(self):
        start = self.graph.vertex.create('start')
        end = self.graph.vertex.create('end')
        start.link('edge', end)

        # retrieve start and end
        start = self.graph.vertex.get(start.uid)
        end = self.graph.vertex.get(end.uid)

        self.assertTrue(start.outgoings())
        self.assertTrue(end.incomings())


class TestGremlin(TestCase):

    def setUp(self):
        try:
            rmtree('/tmp/ajgudb')
        except OSError:
            pass
        os.makedirs('/tmp/ajgudb')
        self.graph = AjguDB('/tmp/ajgudb')

    def tearDown(self):
        self.graph.close()
        rmtree('/tmp/ajgudb')

    def test_where(self):
        seed = self.graph.vertex.create('seed')
        seed.link('test', self.graph.vertex.create('one'), ok=True)
        seed.link('test', self.graph.vertex.create('two'), ok=True)
        seed.link('test', self.graph.vertex.create('one'), ok=False)
        query = gremlin.query(gremlin.outgoings, gremlin.where(ok=True))
        count = len(list(query(self.graph, seed)))
        self.assertEqual(count, 2)

    def test_skip(self):
        seed = self.graph.vertex.create('seed')
        seed.link('test', self.graph.vertex.create('one'))
        seed.link('test', self.graph.vertex.create('two'))
        seed.link('test', self.graph.vertex.create('one'))
        query = gremlin.query(gremlin.outgoings, gremlin.skip(2))
        count = len(list(query(self.graph, seed)))
        self.assertEqual(count, 1)

    def test_limit(self):
        seed = self.graph.vertex.create('seed')
        seed.link('test', self.graph.vertex.create('one'))
        seed.link('test', self.graph.vertex.create('two'))
        seed.link('test', self.graph.vertex.create('one'))
        query = gremlin.query(gremlin.outgoings, gremlin.limit(2))
        count = len(list(query(self.graph, seed)))
        self.assertEqual(count, 2)

    # def test_paginator(self):
    #     seed = self.graph.vertex('seed')
    #     list(map(lambda x: seed.link('test', self.graph.vertex()), range(20)))
    #     self.assertEqual(seed.outgoings().paginator(5).count(), 5)
    #     self.assertEqual(seed.outgoings().paginator(5).count(), 5)

    def test_outgoings(self):
        seed = self.graph.vertex.create('test')
        other = self.graph.vertex.create('test')
        seed.link('test', other)
        other.link('test', self.graph.vertex.create('test'))
        other.link('test', self.graph.vertex.create('test'))
        query = gremlin.query(gremlin.outgoings, gremlin.end, gremlin.outgoings, gremlin.count)
        self.assertEqual(query(self.graph, seed), 2)

    def test_incomings(self):
        seed = self.graph.vertex.create('test')
        other = self.graph.vertex.create('test')
        link = seed.link('test', other)
        query = gremlin.query(gremlin.incomings, gremlin.get)
        self.assertEqual(query(self.graph, other), [link])

    def test_incomings_two(self):
        seed = self.graph.vertex.create('test')
        other = self.graph.vertex.create('test')
        seed.link('test', other)
        query = gremlin.query(gremlin.incomings, gremlin.start, gremlin.get)
        self.assertEqual(query(self.graph, other), [seed])

    def test_path(self):
        seed = self.graph.vertex.create('test')
        other = self.graph.vertex.create('test')
        link = seed.link('test', other)
        query = gremlin.query(
            gremlin.incomings,
            gremlin.start,
            gremlin.path(2),
            gremlin.each(gremlin.get),
            gremlin.value,
        )
        path = next(query(self.graph, other))
        self.assertEqual(path, [seed, link, other])

    def test_incomings_three(self):
        seed = self.graph.vertex.create('test')
        other = self.graph.vertex.create('test')
        seed.link('test', other)
        end = self.graph.vertex.create('test')
        other.link('test', end)
        query = gremlin.query(gremlin.incomings, gremlin.start, gremlin.incomings, gremlin.start, gremlin.get)
        self.assertEqual(query(self.graph, end), [seed])

    def test_order(self):
        seed = self.graph.vertex.create('test')
        seed.link('test', self.graph.vertex.create('test', value=5))
        seed.link('test', self.graph.vertex.create('test', value=4))
        seed.link('test', self.graph.vertex.create('test', value=1))

        query = gremlin.query(gremlin.outgoings, gremlin.end, gremlin.key('value'), gremlin.value)
        # the order is not guaranteed..
        self.assertEqual(set(query(self.graph, seed)), set([5, 4, 1]))

        query = gremlin.query(gremlin.outgoings, gremlin.end, gremlin.key('value'), gremlin.sort(), gremlin.value)
        self.assertEqual(list(query(self.graph, seed)), [1, 4, 5])

    def test_unique(self):
        seed = self.graph.vertex.create('test')
        seed.link('test', self.graph.vertex.create('test', value=1))
        seed.link('test', self.graph.vertex.create('test', value=1))
        seed.link('test', self.graph.vertex.create('test', value=1))
        query = gremlin.query(gremlin.outgoings, gremlin.end, gremlin.key('value'), gremlin.unique, gremlin.value)
        results = list(query(self.graph, seed))
        self.assertEqual(results, [1])
