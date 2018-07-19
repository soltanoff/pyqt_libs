# -*- coding: utf-8 -*-
from Types.Node import Node
from Types.tools import buildTree


class Tree(object):
    def __init__(self, root=None):
        self._root = root if root is not None else Node()  # type: Node
        self._nodeMap = {}  # type: dict[int, Node]

    def _update(self, rootItem):
        u""" :type rootItem: Node """
        self._nodeMap[rootItem.id] = rootItem
        for item in rootItem:
            self._update(item)

    @classmethod
    def fromEdges(cls, edges):
        tree = cls(root=cls.buildNodeTree(buildTree(edges)))
        tree._update(tree._root)
        return tree

    @classmethod
    def buildNodeTree(cls, tree):
        def buildSubTree(rootItem, subTree):
            for itemId, itemSubTree in subTree.iteritems():
                childItem = rootItem.addChild(itemId)
                buildSubTree(childItem, itemSubTree)

        for root_id, root_tree in tree.iteritems():
            root = Node(root_id)
            buildSubTree(root, root_tree)
            return root

        return Node()

    def searchById(self, itemId):
        return self._nodeMap.get(itemId)
