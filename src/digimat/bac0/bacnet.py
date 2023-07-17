#!/bin/python

import pkg_resources

# import time
import logging
import logging.handlers
import re
import unicodedata

from prettytable import PrettyTable

from digimat.units import Units

import BAC0
# BAC0.bacpypes.basetypes.EngineeringUnits

units=Units()


# Help to build a local node
# https://pythoninthebuilding.wordpress.com/


class ObjectVariableMounter(object):
    def __init__(self, parent):
        self._parent=parent

    def strip(self, text):
        try:
            text = str(text, 'utf-8')
        except:
            pass

        text = unicodedata.normalize('NFD', text)
        text = text.encode('ascii', 'ignore')
        text = text.decode("utf-8")
        return str(text)

    def normalize(self, text):
        try:
            text = self.strip(text)
            text = re.sub('[ ]+\'', '_', text)
            text = re.sub('[^0-9a-zA-Z_-]', '', text)
            return text
        finally:
            return text

    def mount(self, obj):
        try:
            tag=self.normalize(obj.name)
            if tag and not hasattr(self._parent, tag):
                setattr(self._parent, tag, obj)
        except:
            pass


class BACPoint(object):
    def __init__(self, bac0point, index=None):
        self._bac0point=bac0point
        self._index=index
        self.onInit()

    def onInit(self):
        pass

    def isWritable(self):
        return False

    def priority(self, priority=None):
        # to be overriden
        return None

    def activePriority(self):
        p=self.priority()
        if p:
            return p[2]

    def reloadBacnetProperties(self):
        self._bac0point.update_bacnet_properties()

    @property
    def properties(self):
        return self._bac0point.properties

    @property
    def bacnetproperties(self):
        return self._bac0point.bacnet_properties

    def bacnetProperty(self, name):
        try:
            return self.bacnetproperties[name]
        except:
            pass

    @property
    def index(self):
        return self._index

    @property
    def name(self):
        return self.properties.name

    @property
    def label(self):
        return None

    @property
    def type(self):
        return self.properties.type

    @property
    def address(self):
        return int(self.properties.address)

    @property
    def description(self):
        return self.properties.description

    def isOutOfService(self):
        if self.bacnetProperty('outOfService'):
            return True
        return False

    @property
    def unit(self):
        unit=self._bac0point.units
        return unit

    @property
    def unitNumber(self):
        try:
            return BAC0.bacpypes.basetypes.EngineeringUnits(self.unit).get_long()
        except:
            pass

    def digUnit(self):
        if self.isMultiState():
            return units.multistate()
        if self.isBinary():
            return units.digital()

        unit=self.unitNumber
        if unit==BAC0.bacpypes.basetypes.EngineeringUnits.degreesCelsius:
            return units.getByName('C')
        if unit==BAC0.bacpypes.basetypes.EngineeringUnits.percent:
            return units.getByName('%')
        if unit==BAC0.bacpypes.basetypes.EngineeringUnits.pascals:
            return units.getByName('pa')

        # TODO: add more units...
        return units.none()

    def digUnitStr(self):
        try:
            return units.getByNumber(self.digUnit())
        except:
            pass

    def digDecimals(self):
        if self.isAnalog():
            unit=self.unitNumber
            if unit==BAC0.bacpypes.basetypes.EngineeringUnits.degreesCelsius:
                return 1
        return 0

    def isBinary(self):
        if 'binary' in self.type:
            return True
        return False

    def isAnalog(self):
        if 'analog' in self.type:
            return True
        return False

    def isMultiState(self):
        if 'multiState' in self.type:
            return True
        return False

    @property
    def state(self):
        try:
            if type(self.value)==float:
                return '%.02f' % self.value
        except:
            pass
        return self.value

    @property
    def value(self):
        try:
            # value=self.bacnetproperties['presentValue']
            # FIXME: presentValue property doesn't seems to be refreshed by BAC0.
            # Using ".value" may generate BACnet traffic
            value=self._bac0point.value
            return value
        except:
            pass

    @value.setter
    def value(self, value):
        try:
            self.write(value)
        except:
            pass

    def isCOV(self):
        if self._bac0point.cov_registered:
            return True
        return False

    def cov(self, ttl=300):
        if ttl<=0:
            ttl=60
        self._bac0point.subscribe_cov(confirmed=True, lifetime=ttl, callback=None)

    def covCancel(self):
        self._bac0point.cancel_cov()

    def read(self, prop='presentValue'):
        return self._bac0point.read_property(prop)

    def refresh(self):
        self._bac0point.value
        return self.value

    def __repr__(self):
        return '<%s(%s:%s#%s=%s %s)>' % (self.__class__.__name__,
            self.name,
            self.type, self.address,
            self.state, self.unit)

    def dump(self):
        t=PrettyTable()
        t.field_names=['property', 'value']
        t.align['property']='l'
        t.align['value']='l'
        t.add_row(['name', self.name])
        t.add_row(['description', self.description])
        t.add_row(['type', self.type])
        # t.add_row(['isBinary', self.isBinary()])
        # t.add_row(['isAnalog', self.isAnalog()])
        # t.add_row(['isMultiState', self.isMultiState()])
        t.add_row(['address', self.address])
        t.add_row(['value', self.value])
        if self.state!=self.value:
            t.add_row(['state', self.state])
        if self.isMultiState():
            labels=self.labels
            if labels:
                index=1
                for l in labels:
                    t.add_row(['state[%d]' % index, l])
                    index+=1
        unit=self.unit
        if self.digUnitStr():
            unit += " (%s)" % self.digUnitStr()
        t.add_row(['unit', unit])
        t.add_row(['COV', self.isCOV()])
        t.add_row(['OutOfService', self.isOutOfService()])
        if self.isWritable():
            try:
                for priority in range(1, 16+1):
                    p=self.priority(priority)
                    if p:
                        t.add_row(['PriorityArray[%d]' % p[2], '%s:%s' % (p[1], str(p[0]))])
            except:
                pass
            try:
                default=self.default
                if default:
                    t.add_row(['Default', str(default)])
            except:
                pass

        if self._index is not None:
            t.add_row(['index', self.index])
        print(t)

    def _str2keys(self, keys):
        if keys:
            return str(keys).lower().split()

    def match(self, keys):
        if keys:
            keys=self._str2keys(keys)
            for key in keys:
                if key not in self.name.lower() and key not in self.description.lower():
                    return False
            return True
        return True

    def poll(self, delay=20):
        self._bac0point.poll(delay)

    def pollStop(self):
        self.poll(0)


class BACPointInput(BACPoint):
    pass


class BACPointWritable(BACPoint):
    def isWritable(self):
        return True

    def write(self, value, prop='presentValue', priority=''):
        try:
            return self._bac0point.write(value, prop=prop)
        except:
            pass
        return None

    def reloadPriorityArray(self):
        self._bac0point.read_priority_array()

    def priority(self, priority=None):
        if priority:
            try:
                p=self._bac0point.priority(priority)
                if p:
                    # value, valueType, level
                    return p[1], p[0], priority
                return
            except:
                pass

        for priority in range(1, 16+1):
            try:
                p=self.priority(priority)
                if p:
                    # value, valueType, level
                    return p[1], p[0], priority
            except:
                pass

    def relinquish(self, priority, reload=False):
        try:
            if priority:
                self.write(value="null", priority=priority)
                if reload:
                    self.reloadPriorityArray()
        except:
            pass

    def relinquishAll(self):
        for i in range(1, 16+1):
            self.relinquish(i, reload=False)
        self.reloadPriorityArray()

    @property
    def default(self):
        try:
            return self.bacnetProperty('relinquishDefault')
        except:
            pass

    @default.setter
    def default(self, value):
        try:
            self._bac0point.default(value)
        except:
            pass


class BACPointOutput(BACPointWritable):
    pass


class BACPointValue(BACPointWritable):
    pass


class BACPointBinary(BACPoint):
    def isBinary(self):
        return True

    def isAnalog(self):
        return False

    def isMultiState(self):
        return False

    def isOn(self):
        if self.value=='active':
            return True
        return False

    def isOff(self):
        return not self.isON()

    def bool(self):
        return self.isON()


class BACPointAnalog(BACPoint):
    def isBinary(self):
        return False

    def isAnalog(self):
        return True

    def isMultiState(self):
        return False

    def fahrenheitToCelcius(self, value):
        return (value-32.0)*5.0/9.0

    def celciusToFahrenheit(self, value):
        return (value*9.0/5.9)+32.0

    def toCelcius(self, value):
        if self.unitNumber==BAC0.bacpypes.basetypes.EngineeringUnits.degreesFahrenheit:
            return self.fahrenheitToCelcius(self.value)
        return self.value


class BACPointMultiState(BACPoint):
    def isBinary(self):
        return False

    def isAnalog(self):
        return False

    def isMultiState(self):
        return True

    @property
    def labels(self):
        try:
            return self.properties.units_state
        except:
            pass

    @BACPoint.label.getter
    def label(self):
        try:
            return self.properties.units_state[self.value-1]
        except:
            pass

    @BACPoint.state.getter
    def state(self):
        try:
            index=int(self.value)
            return '%d:%s' % (index, self.properties.units_state[index-1])
        except:
            pass
        return self.value

    def valueFromLabel(self, label):
        try:
            return self.labels.index(label)+1
        except:
            pass


class BACPointAnalogInput(BACPointAnalog, BACPointInput):
    pass


class BACPointAnalogOutput(BACPointAnalog, BACPointOutput):
    pass


class BACPointAnalogValue(BACPointAnalog, BACPointValue):
    pass


class BACPointBinaryInput(BACPointBinary, BACPointInput):
    pass


class BACPointBinaryOutput(BACPointBinary, BACPointOutput):
    def on(self):
        self.write('active')

    def off(self):
        self.write('inactive')

    def toggle(self):
        if self.isOn():
            self.off()
        else:
            self.on()


class BACPointBinaryValue(BACPointBinary, BACPointValue):
    pass


class BACPointMultiStateInput(BACPointMultiState, BACPointInput):
    pass


class BACPointMultiStateOutput(BACPointMultiState, BACPointOutput):
    def write(self, value, prop='presentValue', priority=''):
        if type(value)=='str':
            value=self.valueFromLabel(value)
        super().write(value, prop, priority)


class BACPointMultiStateValue(BACPointMultiState, BACPointValue):
    def write(self, value, prop='presentValue', priority=''):
        if type(value)=='str':
            value=self.valueFromLabel(value)
        super().write(value, prop, priority)


class BACPoints(object):
    def __init__(self, points=None, filterOutOfService=False):
        self._points=[]
        self._pointByName={}
        self._indexByName={}
        self.add(points, filterOutOfService)

    def add(self, points, filterOutOfService=True):
        if points is None:
            return

        if isinstance(points, BACPoints):
            points=[point for point in points._points]
        else:
            if type(points) != list:
                points=[points]

        for point in points:
            assert(isinstance(point, BACPoint))
            if self.getByName(point.name):
                continue

            if not point.isOutOfService():
                index=len(self._points)
                point._index=index
                self._points.append(point)
                self._pointByName[point.name]=point
                self._indexByName[point.name]=index

    def __iadd__(self, point):
        self.add(point)
        return self

    @property
    def points(self, keys=None):
        return self._points

    def pointsMatching(self, keys=None):
        if self._points:
            return [p for p in self._points if p.match(keys)]

    def match(self, keys):
        return [p for p in self.points if p.match(keys)]

    def type(self, objectType):
        return [p for p in self.points if p.type==objectType]

    def analogInput(self, address):
        for p in self._points:
            if p.type=='analogInput' and p.address==address:
                return p

    def analogOutput(self, address):
        for p in self._points:
            if p.type=='analogOutput' and p.address==address:
                return p

    def binaryInput(self, address):
        for p in self._points:
            if p.type=='binaryInput' and p.address==address:
                return p

    def binaryOutput(self, address):
        for p in self._points:
            if p.type=='binaryOutput' and p.address==address:
                return p

    def analogValue(self, address):
        for p in self._points:
            if p.type=='analogValue' and p.address==address:
                return p

    def binaryValue(self, address):
        for p in self._points:
            if p.type=='binaryValue' and p.address==address:
                return p

    def multiStateValue(self, address):
        for p in self._points:
            if p.type=='multiStateValue' and p.address==address:
                return p

    def __repr__(self):
        return '<%s(%d points)>' % (self.__class__.__name__, len(self.points))

    def count(self):
        return len(self._points)

    def __len__(self):
        return self.count()

    def __iter__(self):
        return iter(self._points)

    def getByName(self, name):
        try:
            return self._pointByName[name]
        except:
            pass

    def getByIndex(self, index):
        try:
            return self._points[int(index)]
        except:
            pass

    def __getitem__(self, index):
        item=self.getByIndex(index) or self.getByName(index)
        if not item:
            try:
                item=self.match(index)[0]
            except:
                pass
        return item

    def index(self, name):
        try:
            return self._indexByName[name]
        except:
            pass

    def dump(self, keys=None):
        if type(keys)==list:
            points=keys
        else:
            points=self.pointsMatching(keys)
        if points:
            t=PrettyTable()
            t.field_names=['#', 'class', 'name', 'description', 'type', 'address', 'value', 'unit', 'COV', 'OoS', 'PRI']
            t.align['name']='l'
            t.align['class']='l'
            t.align['description']='l'
            t.align['type']='l'
            t.align['address']='r'
            t.align['value']='r'
            t.align['unit']='l'
            t.align['prio']='l'
            for p in points:
                unit=p.unit
                if p.digUnitStr():
                    unit=p.digUnitStr()
                t.add_row([self.index(p.name),
                           self.__class__.__name__,
                           p.name, p.description,
                           p.type, p.address,
                           p.state, unit,
                           p.isCOV(), p.isOutOfService(), p.activePriority()])
            print(t)

    def refresh(self, keys=None):
        points=self.match(keys)
        if self._points:
            for p in points:
                p.refresh()

    def cov(self, ttl=300):
        if self._points:
            for p in self._points:
                p.cov(ttl)

    def covCancel(self):
        if self._points:
            for p in self._points:
                p.covCancel()

    def poll(self, delay=60):
        for point in self._points:
            point.poll(delay)

    def pollStop(self):
        self.poll(0)

    def mountPointNamesAsVariables(self):
        """Create object variables mapped to each corresponding point's name"""
        mounter=ObjectVariableMounter(self)
        for point in self.points:
            mounter.mount(point)

    def relinquishAll(self):
        """Reset priority array of each writable objects"""
        for point in self.points:
            if point.isWritable():
                point.relinquishAll()


class BACBag(BACPoints):
    def __init__(self, device, points=None):
        self._device=device
        super().__init__(points=points)

    def __repr__(self):
        return '<%s[%s](%d points)>' % (self.__class__.__name__, self.device.name,
            len(self._points))

    @property
    def device(self):
        return self._device


class BACDevice(object):
    def __init__(self, parent, did, ip, index=0, poll=60):
        assert(isinstance(parent, BAC))
        self._parent=parent
        self._did=int(did)
        self._ip=ip
        self._index=index
        self.logger.info('Creating device %s:%d' % (ip, did))
        self._device=BAC0.device(ip, did, parent.bac0, poll=poll, history_size=None)
        self._points=BACPoints()
        self.loadDevicePoints()

    def __repr__(self):
        return '<%s:%d#%s(%s:%s, %s, %d points)>' % (self.__class__.__name__,
            self._did, str(self.index),
            self.vendorName, self.modelName, self.systemStatus,
            len(self._points))

    def loadDevicePoints(self):
        for bac0point in self._device.points:
            ptype=bac0point.properties.type
            # print(ptype)
            if ptype=='binaryInput':
                point=BACPointBinaryInput(bac0point)
            elif ptype=='binaryOutput':
                point=BACPointBinaryOutput(bac0point)
            elif ptype=='analogInput':
                point=BACPointAnalogInput(bac0point)
            elif ptype=='analogOutput':
                point=BACPointAnalogOutput(bac0point)
            elif ptype=='binaryValue':
                point=BACPointBinaryValue(bac0point)
            elif ptype=='analogValue':
                point=BACPointAnalogValue(bac0point)
            elif ptype=='multiStateInput':
                point=BACPointMultiStateInput(bac0point)
            elif ptype=='multiStateOutput':
                point=BACPointMultiStateOutput(bac0point)
            elif ptype=='multiStateValue':
                point=BACPointMultiStateValue(bac0point)
            else:
                self.logger.warning('unable to match a specific BACPoint() class for type %s' % ptype)
                point=BACPoint(bac0point)

            self._points.add(point)

    @property
    def logger(self):
        return self._parent.logger

    @property
    def bac0(self):
        return self._parent.bac0

    @property
    def points(self):
        return self._points

    @property
    def properties(self):
        try:
            return self._device.bacnet_properties
        except:
            pass

    def getProperty(self, name):
        try:
            return self.properties[name]
        except:
            pass

    @property
    def name(self):
        return self.getProperty('objectName')

    @property
    def index(self):
        return self._index

    @property
    def systemStatus(self):
        return self.getProperty('systemStatus')

    @property
    def vendorName(self):
        return self.getProperty('vendorName')

    @property
    def vendorIdentifier(self):
        return self.getProperty('vendorIdentifier')

    @property
    def modelName(self):
        return self.getProperty('modelName')

    @property
    def description(self):
        return self.getProperty('description')

    def isSegmentationSupported(self):
        return self._device.segmentation_supported

    @property
    def did(self):
        return self._did

    @property
    def ip(self):
        return self._ip

    def ping(self):
        return self._device.ping()

    def poll(self, delay):
        self._device.poll(delay)

    def pollStop(self):
        self._device.poll(0)

    def count(self):
        return self.points.count()

    def __len__(self):
        return self.count()

    def __getitem__(self, key):
        try:
            return self.points[key]
        except:
            pass

    def refresh(self, keys=None):
        self.points.refresh(keys)

    def __iter__(self):
        return iter(self.points)

    def dump(self):
        t=PrettyTable()
        t.field_names=['property', 'value']
        t.align['property']='l'
        t.align['value']='l'
        t.add_row(['ip', self.ip])
        t.add_row(['id', self.did])
        t.add_row(['name', self.name])
        t.add_row(['description', self.description])
        t.add_row(['systemStatus', self.systemStatus])
        t.add_row(['vendorName', self.vendorName])
        t.add_row(['vendorIdentifier', self.vendorIdentifier])
        t.add_row(['points', self.points.count()])
        t.add_row(['segmentationSupported', str(self.isSegmentationSupported())])
        for ptype in ['analogInput', 'analogOutput', 'binaryInput', 'binaryOutput', 'analogValue', 'binaryValue', 'multiStateValue']:
            points=self.points.type(ptype)
            if points:
                t.add_row([ptype, len(points)])

        print(t)

    def bag(self, key=None):
        bag=BACBag(self)
        if key:
            if key=='*':
                bag.add(self.points)
            else:
                points=self.points.match(key)
                if points:
                    bag.add(points)
        return bag


class BAC(object):
    def __init__(self, localObjName='Digimat-BAC0', deviceId=None,
                 modelName='Digimat BAC0 Python Node',
                 vendorId=892, vendorName='Digimat',
                 description='https://pypi.org/project/digimat.bac0/', location='Veyrier, CH',
                 network=None, router=None,
                 logServer='localhost', logLevel=logging.DEBUG):

        logger=logging.getLogger("BAC(%s)" % network)
        logger.setLevel(logLevel)
        socketHandler = logging.handlers.SocketHandler(logServer, logging.handlers.DEFAULT_TCP_LOGGING_PORT)
        logger.addHandler(socketHandler)
        self._logger=logger

        self._bac0=None
        self._cacheWhois=None
        self.BAC0LogDisable()

        ifaces=self.getInterfaces([network])
        if ifaces:
            try:
                network=ifaces[0]
            except:
                pass

        if not network:
            interfaces=self.getInterfaces(['eth0', 'en0', 'en1'])
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
                                 vendorId=vendorId, vendorName=vendorName, description=description, location=location,
                                 ip=self._network, bbmdAddress=self._router, bbmdTTL=900)
        else:
            self.logger.info('Starting BAC0 with network %s' % self._network)
            self._bac0=BAC0.lite(localObjName=localObjName, deviceId=deviceId, firmwareRevision=firmwareRevision,
                                 vendorId=vendorId, vendorName=vendorName, description=description, location=location,
                                 ip=self._network)

        if self._bac0:
            self.logger.info('Using BAC0 v%s' % BAC0.version)
            self.logger.info('BAC0:%s' % self._bac0)
            self.logger.info('Using digimat.bac0 v%s' % self.version)

        self._devices={}
        self._devicesByName={}
        self._devicesByIp={}
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
        """return any declared device from id, name, ip or index"""
        try:
            return self._devices[int(did)]
        except:
            pass
        try:
            return self._devicesByName[did]
        except:
            pass
        try:
            return self._devicesByIp[did]
        except:
            pass
        try:
            return self._devicesByIndex[did]
        except:
            pass

    def devices(self, key=None):
        return self._devices.values()

    def whois(self, useCache=False, autoDeclareDevices=False):
        if self._bac0:
            if not self._cacheWhois or not useCache:
                self._cacheWhois=self._bac0.whois()
            items=self._cacheWhois
            if items and autoDeclareDevices:
                for item in items:
                    self.declareDevice(item[1], item[0])
            return items

    def discover(self, useCache=False):
        return self.whois(useCache=useCache, autoDeclareDevices=True)

    def declareDevice(self, did, ip=None, poll=60):
        device=self.device(did)
        if device is None:
            if ip is None:
                addresses=self.whois()
                if addresses:
                    for address in addresses:
                        if address[1]==did:
                            ip=address[0]
            if did and ip:
                device=BACDevice(self, did, ip, index=len(self._devices), poll=poll)
                self._devices[did]=device
                self._devicesByName[device.name]=device
                self._devicesByIp[ip]=device
                self._devicesByIndex[device.index]=device
        return device

    def __getitem__(self, key):
        """return any declared device from id, name or ip"""
        return self.device(key)

    def dump(self):
        devices=self.devices()
        if devices:
            t=PrettyTable()
            t.field_names=['#', 'name', 'id', 'ip', 'vendor', 'model', ' status', 'description', '#points']
            t.align['*']='l'
            t.align['name']='l'
            t.align['vendor']='l'
            t.align['model']='l'
            t.align['description']='l'
            for device in devices:
                t.add_row([device.index, device.name, device.did, device.ip,
                           device.vendorName, device.modelName, device.systemStatus,
                           device.description,
                           device.points.count()])
            print(t)

    def __iter__(self):
        return iter(self._devices.values())


if __name__=='__main__':
    pass
