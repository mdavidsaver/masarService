import sys
import unittest
import sqlite3
import os

from masarclient import masarClient
from pymasarsqlite.service.serviceconfig import (saveServiceConfig, retrieveServiceConfigs, retrieveServiceConfigPVs, saveServicePvGroup, retrieveServicePvGroups)
from pymasarsqlite.pvgroup.pvgroup import (savePvGroup, retrievePvGroups)
from pymasarsqlite.pvgroup.pv import (saveGroupPvs, retrieveGroupPvs)
from pymasarsqlite.service.service import (saveService)
from pymasarsqlite.masardata.masardata import (checkConnection, saveServiceEvent)
from masarclient.channelRPC import epicsExit

'''

Unittests for masarService/python/masarclient/masarClient.py

'''


class TestMasarClient(unittest.TestCase):

    def setUp(self):
        channel = 'masarService'
        self.mc = masarClient.client(channelname=channel)
        #DB SETUP
        __sqlitedb__ = os.environ["MASAR_SQLITE_DB"]
        try:
            conn = sqlite3.connect(__sqlitedb__)
            cur = conn.cursor()
            __sql__ = None
            if __sql__ is None:
                from pymasarsqlite.db.masarsqlite import SQL
            else:
                sqlfile = open(__sql__)
                SQL = sqlfile.read()
            if SQL is None:
                print ('SQLite script is empty. Cannot create SQLite db.')
                sys.exit()
            else:
                cur.executescript(SQL)
                cur.execute("PRAGMA main.page_size= 4096;")
                cur.execute("PRAGMA main.default_cache_size= 10000;")
                cur.execute("PRAGMA main.locking_mode=EXCLUSIVE;")
                cur.execute("PRAGMA main.synchronous=NORMAL;")
                cur.execute("PRAGMA main.journal_mode=WAL;")
                cur.execute("PRAGMA main.temp_store = MEMORY;")

            cur.execute('select name from sqlite_master where type=\'table\'')
            masarconf = 'SR_All_20140421'
            servicename = 'SR'
            saveService(conn, servicename, desc='machine snapshot, archiving, and retrieve service')
            saveServiceConfig(conn, servicename, masarconf, configdesc='SR description', system='SR', status='active',
                              configversion=20140421)

            pvgname = 'masarpvgroup'
            pvgdesc = 'this is my new pv group for masar service with same group name'
            pvs = ["masarExampleDoubleArray"]
            res = savePvGroup(conn, pvgname, func=pvgdesc)
            res = saveGroupPvs(conn, pvgname, pvs)
            pvgroups = retrievePvGroups(conn)
            res == saveServicePvGroup(conn, masarconf, [pvgname])
            pvlist = retrieveServiceConfigPVs(conn, masarconf, servicename=servicename)
            results = retrieveServiceConfigs(conn, servicename, masarconf)
        except sqlite3.Error, e:
            print ("Error %s:" % e.args[0])
            sys.exit(1)
        finally:
            if conn:
                conn.commit()
                conn.close()

    def tearDown(self):
        __sqlitedb__ = os.environ["MASAR_SQLITE_DB"]
        if (os.path.isfile(__sqlitedb__)):
            os.remove(__sqlitedb__)

    '''

    '''
    def testRetrieveSystemList(self):
        result = self.mc.retrieveSystemList()
        self.assertNotEqual(result, None)  # Can not be assertTrue because there is no case where it returns True
        self.assertNotEqual(result, False)  # Instead asserting both not None and not False
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], 'test')

    '''

    '''
    def testRetrieveServiceConfigs(self):
        params = {'system': 'SR'}
        result = self.mc.retrieveServiceConfigs(params)
        self.assertNotEqual(result, None)
        self.assertNotEqual(result, False)
        self.assertEqual(len(result), 6)

    def testRetrieveServiceEvents(self):
        params = {'configid': '1'}
        result = self.mc.retrieveServiceEvents(params)
        self.assertNotEqual(result, None)
        self.assertNotEqual(result, False)

    def testSaveSnapshot(self):
        params = {'configname': 'SR_All_20140421',
                  'servicename': 'SR'}
        result = self.mc.saveSnapshot(params)
        self.assertNotEqual(result, None)
        self.assertNotEqual(result, False)

    def testRetrieveSnapshot(self):
        save_params = {'configname': 'SR_All_20140421',
                  'servicename': 'SR'}
        res1 = self.mc.saveSnapshot(save_params)
        self.assertNotEqual(res1, None)
        self.assertNotEqual(res1, False)
        event_id = res1[0]
        retrieve_params = {'eventid': str(event_id)}
        result = self.mc.retrieveSnapshot(retrieve_params)
        self.assertNotEqual(result, None)
        self.assertNotEqual(result, False)

    def testApproveSnapshot(self):
        save_params = {'configname': 'SR_All_20140421',
                       'servicename': 'SR'}

        res1 = self.mc.saveSnapshot(save_params)
        self.assertNotEqual(res1, None)
        self.assertNotEqual(res1, False)  # Can not be assertTrue because there is no case where it returns True
        event_id = res1[0]
        approve_params = {'eventid': str(event_id),
                  'configname': 'SR_All_20140421',
                  'user': 'test',
                  'desc': 'this is a good snapshot, and I approved it.'}
        result = self.mc.updateSnapshotEvent(approve_params)
        self.assertNotEqual(result, None)
        self.assertNotEqual(result, False)

    def testGetLiveMachine(self):
        pvlist = ["masarExampleCharArray",
                  "masarExampleFloatArray",
                  "masarExampleShortArray",
                  "masarExampleUCharArray"]
        for i in range(len(pvlist)):
            params = {}
            for pv in pvlist[i:]:
                params[pv] = pv
                result = self.mc.getLiveMachine(params)
                self.assertNotEqual(result, None)
                #self.assertNotEqual(result, False)

    def testMasarClientLifecycle(self):
        #retrieve configs
        params = {'system': 'LTD2'}
        result = self.mc.retrieveServiceConfigs(params)
        self.assertNotEqual(result, None)
        self.assertNotEqual(result, False)
        #retrieve list
        result = self.mc.retrieveSystemList()
        self.assertNotEqual(result, None)
        self.assertNotEqual(result, False)
        #save snapshot
        params = {'configname': 'test',
                  'servicename': 'masar'}
        result = self.mc.saveSnapshot(params)
        self.assertNotEqual(result, None)
        self.assertNotEqual(result, False)
        #approve snapshot
        save_params = {'configname': 'test',
                       'servicename': 'masar'}

        res1 = self.mc.saveSnapshot(save_params)
        event_id = res1[0]
        approve_params = {'eventid': str(event_id),
                  'configname': 'test',
                  'user': 'test',
                  'desc': 'this is a good snapshot, and I approved it.'}
        result = self.mc.updateSnapshotEvent(approve_params)
        self.assertNotEqual(result, None)
        self.assertNotEqual(result, False)
        #retrieve snapshot
        save_params = {'configname': 'test',
                  'servicename': 'masar'}
        res1 = self.mc.saveSnapshot(save_params)
        event_id = res1[0]
        retrieve_params = {'eventid': str(event_id)}
        result = self.mc.retrieveSnapshot(retrieve_params)
        self.assertNotEqual(result, None)
        self.assertNotEqual(result, False)
        #retrieve events
        params = {'configid': '1'}
        result = self.mc.retrieveServiceEvents(params)
        self.assertNotEqual(result, None)
        self.assertNotEqual(result, False)
        #live machine
        pvlist = ["masarExampleCharArray",
                  "masarExampleFloatArray",
                  "masarExampleShortArray",
                  "masarExampleUCharArray"]
        params = {}
        for i in range(len(pvlist)):
            params[pvlist[i]] = pvlist[i]
            result = self.mc.getLiveMachine(params)
            self.assertNotEqual(result, None)
            self.assertNotEqual(result, False)

    if __name__ == '__main__':
        unittest.main()
