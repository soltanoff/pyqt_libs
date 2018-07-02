# -*- coding: utf-8 -*-


class Node(object):
    def __init__(self, itemId=None, parent=None):
        self.id = itemId
        self.parent = parent  # type: Node | None
        self.children = []  # type: list[Node]

    def __iter__(self):
        return iter(self.children)

    def addChild(self, childId):
        childNode = Node(childId, self)
        self.children.append(childNode)
        return childNode

    def getDistances(self):
        def updateDistances(item, distMap, current=0):
            if item.id in distMap: return
            distMap[item.id] = current
            if item.parent:
                updateDistances(item.parent, distMap, current + 1)
            for child in item.children:
                updateDistances(child, distMap, current + 1)

        distances = {}
        updateDistances(self, distances)
        return distances
