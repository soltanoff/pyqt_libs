# -*- coding: utf-8 -*-
from collections import defaultdict


def buildTrees(edges):
    u""" Построение дерева по списку ребер
    :type edges: list[tuple[collections.Hashable, collections.Hashable]]
    :param edges: список ребер: [ ... (дочерний узел, родительский узел), ... ]
    :rtype: dict[collections.Hashable, dict] """
    trees = defaultdict(dict)
    for child, parent in edges:
        trees[parent][child] = trees[child]
    return trees


def buildTree(edges):
    u""" Построение дерева по списку ребер
    :param edges: список ребер: [ ... (дочерний узел, родительский узел), ... ]
    :type edges: list[(collections.Hashable, collections.Hashable)]
    :rtype: dict[collections.Hashable, dict] """
    trees = defaultdict(dict)
    for child, parent in edges:
        trees[parent][child] = trees[child]
    children, parents = zip(*edges)
    roots = set(parents).difference(children)
    return dict((root, trees[root]) for root in roots)


def iterTree(tree):
    u""" Обход дерева в глубину
    :type tree: dict[collections.Hashable, dict]
    :rtype: collections.Iterable """
    for item, subTree in tree.iteritems():
        yield item
        for childItem in iterTree(subTree):
            yield childItem


def listTree(tree):
    u""" Обход дерева в глубину
    :type tree: dict
    :rtype: list """
    return list(iterTree(tree))
