import BAC0

# import time
import logging
import logging.handlers

from prettytable import PrettyTable

# BAC0.bacpypes.basetypes.EngineeringUnits


class BACPoint(object):
    def __init__(self, bac0point, index=None):
        self._bac0point=bac0point
        self._index=index

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
    def type(self):
        return self.properties.type

    @property
    def address(self):
        return int(self.properties.address)

    @property
    def description(self):
        return self.properties.description

    @property
    def unit(self):
        return self._bac0point.units

    @property
    def state(self):
        try:
            if 'multiState' in self.type:
                index=int(self.value)
                return '%d:%s' % (index, self.properties.units_state[index-1])
            if type(self.value)==float:
                return '%.02f' % self.value
        except:
            pass
        return self.value

    @property
    def value(self):
        try:
            return self.bacnetproperties['presentValue']
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

    def write(self, value, prop='presentValue', priority=''):
        self._bac0point.write(value, prop=prop)

    def read(self, prop='presentValue'):
        return self._bac0point.read_property(prop)

    def refresh(self):
        return self._bac0point.value

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
        t.add_row(['address', self.address])
        t.add_row(['value', self.value])
        if self.state!=self.value:
            t.add_row(['state', self.state])
        t.add_row(['unit', self.unit])
        t.add_row(['COV', self.isCOV()])
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

    def poll(self, delay=60):
        self._bac0point.poll(delay)

    def pollStop(self):
        self.poll(0)


class BACPoints(object):
    def __init__(self, points=None, filterOutOfService=True):
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

            oos=False
            if filterOutOfService:
                try:
                    if point.properties.bacnet_properties['outOfService']:
                        oos=True
                except:
                    pass

            if not oos:
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
        return self.getByIndex(index) or self.getByName(index)

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
            t.field_names=['#', 'name', 'description', 'type', 'address', 'value', 'unit', 'COV']
            t.align['name']='l'
            t.align['description']='l'
            t.align['type']='l'
            t.align['address']='r'
            t.align['value']='r'
            t.align['unit']='l'
            for p in points:
                t.add_row([self.index(p.name), p.name, p.description,
                           p.type, p.address,
                           p.state, p.unit,
                           p.isCOV()])
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


class BACBag(BACPoints):
    def __init__(self, device):
        self._device=device
        super().__init__()

    def __repr__(self):
        return '<%s[%s](%d points)>' % (self.__class__.__name__, self.device.name,
            len(self._points))

    @property
    def device(self):
        return self._device


class BACDevice(object):
    def __init__(self, parent, did, ip, poll=60):
        assert(isinstance(parent, BAC))
        self._parent=parent
        self._did=int(did)
        self._ip=ip
        self.logger.info('Creating device %s:%d' % (ip, did))
        self._device=BAC0.device(ip, did, parent.bac0, poll=poll, history_size=0)
        self._points=BACPoints()
        self.loadDevicePoints()

    def __repr__(self):
        return '<%s:%d(%s:%s, %s, %d points)>' % (self.__class__.__name__, self._did,
            self.vendorName, self.modelName, self.systemStatus,
            len(self._points))

    def loadDevicePoints(self):
        for bac0point in self._device.points:
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
        for ptype in ['analogInput', 'analogOutput', 'binaryInput', 'binaryOutput', 'analogValue', 'binaryValue', 'multiStateValue']:
            points=self.points.type(ptype)
            if points:
                t.add_row([ptype, len(points)])

        print(t)

    def bag(self):
        return BACBag(self)


class BAC(object):
    def __init__(self, network=None, router=None, logServer='localhost', logLevel=logging.DEBUG):
        logger=logging.getLogger("BAC(%s)" % network)
        logger.setLevel(logLevel)
        socketHandler = logging.handlers.SocketHandler(logServer, logging.handlers.DEFAULT_TCP_LOGGING_PORT)
        logger.addHandler(socketHandler)
        self._logger=logger

        self._bac0=None
        self._cacheWhois=None
        self.BAC0LogDisable()

        if not network:
            interfaces=self.getInterfacesIpAddress()
            if interfaces:
                for address in interfaces:
                    self.logger.info('Found local interface [%s]' % address)
                    if address=='127.0.0.1':
                        continue
                    network=address
                    break
            else:
                print('Please specify your network IP/MASK or install netifaces module (pip install netifaces)!')
                print("i.e. bacnet=BAC(network='192.168.0.84/24', ...)")
                raise Exception('No IP/MASK given')

        self._network=network
        self._router=router

        if router:
            self.logger.info('Starting BAC0 with network %s@%s' % (self._network, router))
            self._bac0=BAC0.lite(ip=network, bbmdAddress=router, bbmdTTL=900)
        else:
            self.logger.info('Starting BAC0 with network %s' % self._network)
            self._bac0=BAC0.lite(ip=self._network)

        if self._bac0:
            self.logger.info('Using BAC0 v%s' % BAC0.version)
            self.logger.info('BAC0:%s' % self._bac0)

        self._devices={}

    def __repr__(self):
        return '<%s:%s(%d devices)>' % (self.__class__.__name__, self._network, len(self._devices))

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

    def getInterfacesIpAddress(self):
        ip=[]
        try:
            import netifaces
            for i in netifaces.interfaces():
                try:
                    iface = netifaces.ifaddresses(i).get(netifaces.AF_INET)
                    if iface is not None:
                        for j in iface:
                            ip.append(j['addr'])
                except:
                    pass
        except:
            self.logger.warning('Strongly consider installing netifaces module (pip install netifaces)')
            self.logger.warning('Without, local interfaces have to be manually declared at node creation')
            return None

        return ip

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
        try:
            return self._devices[int(did)]
        except:
            pass

    def devices(self, key=None):
        return self._devices.values()

    def whois(self, autoDeclareDevices=False, useCache=True):
        if self._bac0:
            if not self._cacheWhois:
                self._cacheWhois=self._bac0.whois()
            items=self._cacheWhois
            if items and autoDeclareDevices:
                for item in items:
                    self.declareDevice(item[1], item[0])
            return items

    def discover(self):
        return self.whois(True)

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
                device=BACDevice(self, did, ip, poll=poll)
                self._devices[did]=device
        return device

    def __getitem__(self, key):
        return self.device(key)

    def dump(self):
        devices=self.devices()
        if devices:
            t=PrettyTable()
            t.field_names=['name', 'id', 'ip', 'vendor', 'model', ' status', 'description', 'points']
            t.align['*']='l'
            t.align['name']='l'
            t.align['vendor']='l'
            t.align['model']='l'
            t.align['description']='l'
            for device in devices:
                t.add_row([device.name, device.did, device.ip,
                           device.vendorName, device.modelName, device.systemStatus,
                           device.description,
                           device.points.count()])
            print(t)

    def __iter__(self):
        return iter(self._devices.values())


if __name__=='__main__':
    pass
