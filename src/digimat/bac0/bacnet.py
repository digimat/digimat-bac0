#!/bin/python

import pkg_resources

# import time
import logging
import logging.handlers

from prettytable import PrettyTable

from digimat.units import Units

import BAC0
# BAC0.bacpypes.basetypes.EngineeringUnits


from .bacpoint import BACPoint
from .bacpoints import BACPoints
from .bacdevice import BACDevice


# Help to build a local node
# https://pythoninthebuilding.wordpress.com/
# https://github.com/ChristianTremblay/BAC0/blob/master/tests/conftest.py


class BAC(object):
    def __init__(self, deviceId=None,
                 network=None,
                 router=None,
                 localObjName='Digimat-BAC0',
                 modelName='Digimat BAC0 Python Node',
                 vendorId=892, vendorName='Digimat',
                 description='https://pypi.org/project/digimat.bac0/',
                 location='Probably on planet earth',
                 logServer='localhost', logLevel=logging.DEBUG):

        logger=logging.getLogger("BAC(%s)" % network)
        logger.setLevel(logLevel)
        socketHandler = logging.handlers.SocketHandler(logServer, logging.handlers.DEFAULT_TCP_LOGGING_PORT)
        logger.addHandler(socketHandler)
        self._logger=logger

        self._bac0=None
        self.BAC0LogDisable()

        ifaces=self.getInterfaces([network])
        if ifaces:
            try:
                network=ifaces[0]
            except:
                pass

        if not network:
            en=['en%d' % n for n in range(16)]
            ifaces=['eth0', 'eth1', 'eth2']
            ifaces.extend(en)
            interfaces=self.getInterfaces(ifaces)
            if interfaces:
                for address in interfaces:
                    self.logger.info('Found local interface [%s]' % address)
                    if '127.0.0.1' in address:
                        continue
                    network=address
                    break
            else:
                print('Please specify your network IP/MASK or install netifaces module (pip install netifaces)!')
                print("i.e. bacnet=BAC(network='192.168.0.84/24', ...)")
                raise Exception('No IP/MASK given')

        self._network=network
        self._router=router

        firmwareRevision="%s (BAC0 %s)" % (self.version, BAC0.version)

        if router:
            self.logger.info('Starting BAC0 with network %s@%s' % (self._network, self._router))
            self._bac0=BAC0.lite(localObjName=localObjName, deviceId=deviceId, firmwareRevision=firmwareRevision,
                                 vendorId=vendorId, vendorName=vendorName, modelName=modelName, description=description, location=location,
                                 ip=self._network, bbmdAddress=self._router, bbmdTTL=900)
        else:
            self.logger.info('Starting BAC0 with network %s' % self._network)
            self._bac0=BAC0.lite(localObjName=localObjName, deviceId=deviceId, firmwareRevision=firmwareRevision,
                                 vendorId=vendorId, vendorName=vendorName, modelName=modelName, description=description, location=location,
                                 ip=self._network)

        if self._bac0:
            self.logger.info('Using BAC0 v%s' % BAC0.version)
            self.logger.info('BAC0:%s' % self._bac0)
            self.logger.info('Using digimat.bac0 v%s' % self.version)

        self._devices={}
        self._devicesByName={}
        self._devicesByAddress={}
        self._devicesByIndex={}

        self.open()

    def __repr__(self):
        return '<%s:%s(%d devices)>' % (self.__class__.__name__, self._network, len(self._devices))

    def getVersion(self):
        try:
            distribution=pkg_resources.get_distribution('digimat.bac0')
            return distribution.parsed_version
        except:
            pass

    @property
    def version(self):
        return self.getVersion()

    def BAC0LogLevel(self, level='info'):
        BAC0.log_level(level)

    def BAC0LogDisable(self):
        self.BAC0LogLevel('silence')

    def BAC0LogDebug(self):
        self.BAC0LogLevel('debug')

    def BAC0LogInfo(self):
        self.BAC0LogLevel('info')

    def BAC0LogCritical(self):
        self.BAC0LogLevel('critical')

    def getInterfaces(self, ifnames=None):
        ifaces=[]
        try:
            import netifaces
            import ipcalc
            try:
                if not ifnames:
                    ifnames=netifaces.interfaces()
                for i in ifnames:
                    try:
                        iface = netifaces.ifaddresses(i).get(netifaces.AF_INET)
                        if iface is not None:
                            # print(iface)
                            net=ipcalc.Network('%s/%s' % (iface[0]['addr'], iface[0]['netmask']))
                            ifaces.append(str(net))
                    except:
                        pass
            except:
                pass
        except:
            self.logger.warning('Strongly consider installing netifaces+ipcalc modules (pip install netifaces ipcalc)')
            self.logger.warning('Without, local interfaces have to be manually declared at node creation')
            return None

        return ifaces

    @property
    def logger(self):
        return self._logger

    @property
    def bac0(self):
        return self._bac0

    def open(self):
        if self._bac0:
            self.whois()

    def close(self):
        if self._bac0:
            self._bac0.disconnect()

    def device(self, did):
        """return any declared device from id, name, address or index"""
        try:
            return self._devices[int(did)]
        except:
            pass
        try:
            return self._devicesByName[did]
        except:
            pass
        try:
            return self._devicesByAddress[did]
        except:
            pass
        try:
            return self._devicesByIndex[did]
        except:
            pass

    def devices(self, key=None):
        return self._devices.values()

    def whois(self, network='*:*', autoDeclareDevices=False):
        if self._bac0:
            items=self._bac0.whois(network)

            if items and autoDeclareDevices:
                for item in items:
                    self.declareDevice(item[1], item[0])
            return items

    def discover(self, network='*:*'):
        return self.whois(network, autoDeclareDevices=True)

    def declareDevice(self, did, address=None, poll=15, filterOutOfService=False):
        device=self.device(did)
        if device is None:
            if address is None:
                addresses=self.whois()
                if addresses:
                    for adr in addresses:
                        if adr[1]==did:
                            address=adr[0]
            if did and address:
                device=BACDevice(self, did, address, index=len(self._devices), poll=poll, filterOutOfService=filterOutOfService)
                self._devices[did]=device
                self._devicesByName[device.name]=device
                self._devicesByAddress[address]=device
                self._devicesByIndex[device.index]=device
        return device

    def __getitem__(self, key):
        """return any declared device from id, name or address"""
        return self.device(key)

    def dump(self):
        devices=self.devices()
        if devices:
            t=PrettyTable()
            t.field_names=['#', 'name', 'id', 'address', 'vendor', 'model', 'description', '#points']
            t.align['*']='l'
            t.align['name']='l'
            t.align['vendor']='l'
            t.align['model']='l'
            t.align['description']='l'
            for device in devices:
                t.add_row([device.index, device.name, device.did, device.address,
                           device.vendorName, device.modelName,
                           device.description,
                           device.points.count()])
            print(t)

    def __iter__(self):
        return iter(self._devices.values())


if __name__=='__main__':
    pass
