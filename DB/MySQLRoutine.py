# -*- coding: utf-8 -*-
from DB.BaseDBRoutine import CDatabaseRoutineMap, CDatabaseRoutine
from Utils.Forcing import forceString


class CMySqlRoutineMap(CDatabaseRoutineMap):
    def __init__(self, db, routineType):
        CDatabaseRoutineMap.__init__(self, db, routineType)
        self._load()

    def _load(self):
        table = self._db.table('INFORMATION_SCHEMA.ROUTINES')
        typeNameMap = {
            CDatabaseRoutine.FUNCTION: 'FUNCTION',
            CDatabaseRoutine.PROCEDURE: 'PROCEDURE'
        }
        cols = [
            table['ROUTINE_NAME'],
            table['ROUTINE_TYPE']
        ]
        cond = [
            table['ROUTINE_SCHEMA'].eq(self._db.db.databaseName()),
            table['ROUTINE_TYPE'].eq(typeNameMap[self._routineType])
        ]
        self._routineMap = dict((forceString(rec.value('ROUTINE_NAME')),
                                 CDatabaseRoutine(self._db, forceString(rec.value('ROUTINE_NAME')), self._routineMap))
                                for rec in self._db.iterRecordList(table, cols, cond))
