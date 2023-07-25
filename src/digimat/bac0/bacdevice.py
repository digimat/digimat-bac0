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
from .bacpoints import BACBag


class BACDevice(object):
    def __init__(self, parent, did, address, index=0, poll=15, filterOutOfService=False):
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
        objects=None
        self._bac0device=BAC0.device(address, did, parent.bac0, poll=poll, history_size=None, object_list=objects)
        self._points=BACPoints()
        self.loadDevicePoints(filterOutOfService)

    def __repr__(self):
        return '<%s:%d#%s(%s:%s, %d points)>' % (self.__class__.__name__,
            self._did, str(self.index),
            self.vendorName, self.modelName,
            len(self._points))

    def loadDevicePoints(self, filterOutOfService=True):
        for bac0point in self._bac0device.points:
            if filterOutOfService and bac0point.bacnet_properties['outOfService']:
                continue

            ptype=bac0point.properties.type
            # FIXME: dont' recreate BACPoint if already here
            # Allow load() more than one time
            # print(ptype)
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
            return self._bac0device.bacnet_properties
        except:
            pass

    def getProperty(self, name, update=False):
        try:
            # using .bacnet_properties object property implies a refresh with BAC0
            # value=self._bac0device.bacnet_properties[name].
            value=self._bac0device._bacnet_properties(False)[name]
            if update or value is None:
                print("DEBUG:REFRESH", name)
                value=self._bac0device._bacnet_properties(True)[name]
            return value
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
        return self.getProperty('systemStatus', True)

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
        return self._bac0device.segmentation_supported

    @property
    def did(self):
        return self._did

    @property
    def address(self):
        return self._address

    def ping(self):
        return self._bac0device.ping()

    def poll(self, delay=15):
        """Register a device task that poll each all points on this device"""
        self.pollStop()
        self._bac0device.poll(delay=delay)

    def pollStop(self):
        """Unregister the device polling task"""
        self._bac0device.poll(command='stop')

    def isPolled(self):
        if self._bac0device.properties.pollDelay:
            return True
        return False

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


if __name__ == "__main__":
    pass
