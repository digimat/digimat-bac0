#!/bin/python
import BAC0

from prettytable import PrettyTable

from .bacpoint import BACPoint
from .bacpoint import BACPointBinaryInput
from .bacpoint import BACPointBinaryOutput
from .bacpoint import BACPointBinaryValue
from .bacpoint import BACPointAnalogInput
from .bacpoint import BACPointAnalogOutput
from .bacpoint import BACPointAnalogValue
from .bacpoint import BACPointMultiStateInput
from .bacpoint import BACPointMultiStateOutput
from .bacpoint import BACPointMultiStateValue

from .bacpoints import BACPoints
from .bacpoints import BACPointsBag


class BACDevice(object):
    """Represent a remote BACnet device. Should be created from the BAC object, with something like bacnet.declareObject(...)
    """
    def __init__(self, parent, did, address, index=0, poll=15, filterOutOfService=False, objectList=None):
        # assert(isinstance(parent, BAC))
        self._parent=parent
        self._did=int(did)
        self._address=address
        self._index=index
        self.logger.info('Creating device %s:%d' % (address, did))
        # FIXME: By default, BAC0 will read the object list from the controller
        # and define every points found inside the device as points.
        # This behaviour may not be optimal in all use cases.
        # BAC0 allows you to provide a custom object list when creating the device.
        # https://bac0.readthedocs.io/en/latest/controller.html
        # Real problem for slow devices !!!
        # objects=[('analogValue', 9)]
        # This can take some time on slow devices (i.e. MSTP) with a lot of points
        self._bac0device=BAC0.device(address, did, parent.bac0, poll=poll, history_size=None, object_list=objectList)
        self._points=BACPoints()
        self._loadDevicePoints(filterOutOfService)

    def __repr__(self):
        return '<%s:%d:%s(%s:%s), %d points)>' % (self.__class__.__name__,
            self._did, str(self.index),
            self.vendorName, self.modelName,
            len(self._points))

    def _loadDevicePoints(self, filterOutOfService=True):
        for bac0point in self._bac0device.points:
            if filterOutOfService and bac0point.bacnet_properties['outOfService']:
                continue

            ptype=bac0point.properties.type
            if ptype=='binaryInput':
                point=BACPointBinaryInput(self, bac0point)
            elif ptype=='binaryOutput':
                point=BACPointBinaryOutput(self, bac0point)
            elif ptype=='analogInput':
                point=BACPointAnalogInput(self, bac0point)
            elif ptype=='analogOutput':
                point=BACPointAnalogOutput(self, bac0point)
            elif ptype=='binaryValue':
                point=BACPointBinaryValue(self, bac0point)
            elif ptype=='analogValue':
                point=BACPointAnalogValue(self, bac0point)
            elif ptype=='multiStateInput':
                point=BACPointMultiStateInput(self, bac0point)
            elif ptype=='multiStateOutput':
                point=BACPointMultiStateOutput(self, bac0point)
            elif ptype=='multiStateValue':
                point=BACPointMultiStateValue(self, bac0point)
            else:
                self.logger.warning('unable to match a specific BACPoint() class for type %s' % ptype)
                point=BACPoint(self, bac0point)

            # if BACPoint is already existing, it will not be added
            self._points.add(point)

    @property
    def logger(self):
        return self._parent.logger

    @property
    def bac0(self):
        """reference to the BAC0 main object (readonly)
        """
        return self._parent.bac0

    @property
    def bac0device(self):
        """reference to the BAC0 device object associated to this device (readonly)
        """
        return self._bac0device

    @property
    def points(self):
        """BACPoints object of this device containing every registered BACPoint (readonly)
        """
        return self._points

    @property
    def properties(self):
        try:
            return self._bac0device.bacnet_properties
        except:
            pass

    def getProperty(self, name, update=False):
        """return the requested bacnet property value (with a pre-read if update if True)
        """
        try:
            # using .bacnet_properties object property implies a refresh with BAC0
            # value=self._bac0device.bacnet_properties[name].
            value=self._bac0device._bacnet_properties(False)[name]
            if update or value is None:
                # print("DEBUG:REFRESH", name)
                value=self._bac0device._bacnet_properties(True)[name]
            return value
        except:
            pass

    def updateProperties(self):
        """force a re-read of the properties of this device (will generate bacnet traffic)
        """
        self._bac0device.update_bacnet_properties()

    @property
    def name(self):
        """return the name property of the device"""
        return self.getProperty('objectName')

    @property
    def index(self):
        """return index (i.e. table index position) of this device as registered in the BAC parent's object table
        """
        return self._index

    @property
    def systemStatus(self):
        """return the actual device status of the device (will send a systemStatus property read to the device)
        """
        return self.getProperty('systemStatus', True)

    @property
    def vendorName(self):
        """return the vendorName property of the device
        """
        return self.getProperty('vendorName')

    @property
    def vendorIdentifier(self):
        """return the vendorId property of the device
        """
        return self.getProperty('vendorIdentifier')

    @property
    def modelName(self):
        """return the modelName property of the device
        """
        return self.getProperty('modelName')

    @property
    def description(self):
        """return the description property of the device
        """
        return self.getProperty('description')

    def isSegmentationSupported(self):
        """return True if the device supports message data segmentation
        """
        return self._bac0device.segmentation_supported

    @property
    def did(self):
        """return the deviceId"""
        return self._did

    @property
    def address(self):
        """return the address of the device (can be an ip or something like "2000:3")
        """
        return self._address

    def ping(self):
        """send a request to the device to check if it's alive (responding)
        """
        return self._bac0device.ping()

    def poll(self, delay=15):
        """Register a device task that poll each all points on this device
        """
        self.pollStop()
        self._bac0device.poll(delay=delay)

    def pollStop(self):
        """Unregister the device point's polling task
        """
        self._bac0device.poll(command='stop')

    def isPolled(self):
        """return True if this device seems to be polled (periodic read of each registered point)
        """
        if self._bac0device.properties.pollDelay:
            return True
        return False

    def cov(self, ttl=300):
        self.points.cov(ttl)

    def covCancel(self):
        self.points.covCancel()

    def count(self):
        """return the number of registered points
        """
        return self.points.count()

    def __len__(self):
        return self.count()

    def __getitem__(self, key):
        try:
            return self.points[key]
        except:
            pass

    def refresh(self, keys=None):
        """force refresh of devices registered points (calling self.points.refresh())
        """
        self.points.refresh(keys)

    def __iter__(self):
        return iter(self.points)

    def dump(self):
        """dump device informations
        """
        t=PrettyTable()
        t.field_names=['property', 'value']
        t.align['property']='l'
        t.align['value']='l'
        t.add_row(['address', self.address])
        t.add_row(['id', self.did])
        t.add_row(['name', self.name])
        t.add_row(['description', self.description])
        t.add_row(['systemStatus', self.systemStatus])  # generate traffic
        t.add_row(['vendorName', self.vendorName])
        t.add_row(['vendorIdentifier', self.vendorIdentifier])
        t.add_row(['points', self.points.count()])
        t.add_row(['segmentationSupported', str(self.isSegmentationSupported())])
        for ptype in ['analogInput', 'analogOutput', 'binaryInput', 'binaryOutput', 'analogValue', 'binaryValue', 'multiStateValue']:
            points=self.points.type(ptype)
            if points:
                t.add_row([ptype, len(points)])

        print(t)

    def readPropertyRaw(self, prop):
        """send a native bacpypes/read request on the device (i.e prop=('analogValue', 1, 'presentValue'))
        """
        return self._bac0device.read_property(prop)

    def writePropertyRaw(self, prop, value, priority=16):
        """send a native bacpypes/write request on the device (i.e prop=('analogValue', 1, 'presentValue'))
        """
        return self._bac0device.write_property(prop)

    def bag(self, key=None):
        """create a BACPointsBag object (a kind of point's view or points collection) associated to this device"""
        bag=BACPointsBag(self)
        if key:
            if key=='*':
                bag.add(self.points)
            else:
                points=self.points.match(key)
                if points:
                    bag.add(points)
        return bag


if __name__ == "__main__":
    pass
