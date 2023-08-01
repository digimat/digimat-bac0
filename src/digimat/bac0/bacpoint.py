#!/bin/python

import datetime
from prettytable import PrettyTable

from digimat.units import Units

import BAC0

# BAC0.bacpypes.basetypes.EngineeringUnits

digimatUnits=Units()


class BACPoint(object):
    """Represent BACnet's point of a BACDevice. Every BACPoint is stored in a parent's BACPoints object. BACPoint objects are created by the BACDevice object
    """
    def __init__(self, device, bac0point, index=None):
        # assert(isinstance(device, BACDevice))
        self._device=device
        self._bac0point=bac0point
        self._index=index
        self._onInit()

    def _onInit(self):
        # to be overridden
        pass

    def isWritable(self):
        """return True if the point seems to be writable
        """
        return False

    def _normalizeValue(self, value):
        """Convert a point value to it's internal "BAC0/bacpypes" attended representation.
        """
        # to be overriden
        return value

    def priority(self, priority=None):
        # to be overriden
        return None

    @property
    def bac0point(self):
        """reference to the BAC0's point object
        """
        return self._bac0point

    @property
    def label(self):
        # to be overriden
        return None

    @property
    def labels(self):
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
    def type(self):
        return self.properties.type

    @property
    def address(self):
        return int(self.properties.address)

    @property
    def descriptor(self):
        return '%s%d' % (self.type, self.address)

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
            return digimatUnits.multistate()
        if self.isBinary():
            return digimatUnits.digital()

        unit=self.unitNumber
        if unit==BAC0.bacpypes.basetypes.EngineeringUnits.degreesCelsius:
            return digimatUnits.getByName('C')
        if unit==BAC0.bacpypes.basetypes.EngineeringUnits.percent:
            return digimatUnits.getByName('%')
        if unit==BAC0.bacpypes.basetypes.EngineeringUnits.pascals:
            return digimatUnits.getByName('pa')

        # TODO: add more units...
        return digimatUnits.none()

    def digUnitStr(self):
        try:
            return digimatUnits.getByNumber(self.digUnit())
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
    def value(self):
        """"property that return the actual value (presentValue), i.e. the last refreshed value"""
        try:
            # WARNING
            # Using ".value" may generate BACnet traffic
            # Using ".lastValue" return the last known value (without traffic)
            # This suppose that either COV or POLLING is active
            if self.isBinary():
                return self._bac0point.boolValue
            value=self._bac0point.lastValue
            if type(value) is str and ':' in value:
                return int(value.split(":")[0])
            return self._bac0point.lastValue
        except:
            pass

    @value.setter
    def value(self, value):
        try:
            self.write(value)
        except:
            pass

    def strvalue(self):
        """return the value expressed as a string (for display purposes)"""
        value=self.value
        if type(value) is str:
            return value
        if type(value) is bool:
            if value:
                return 1
            return 0
        if type(value) is float:
            return '%.6g' % value
        return str(value)

    def age(self):
        """return the age of the last value refresh (seconds)"""
        try:
            t0=self._bac0point.lastTimestamp
            td=datetime.datetime.now()-t0.replace(tzinfo=None)
            return td.total_seconds()
        except:
            pass

    def boolValue(self):
        # to be overriden
        return bool(self.value)

    def isCOV(self):
        if self._bac0point.cov_registered:
            return True
        return False

    def isAutoRefreshed(self):
        if self.isCOV() or self._device.isPolled():
            return True

    def cov(self, ttl=300):
        if ttl==0:
            self.covCancel()
        else:
            if ttl<=0:
                ttl=60
            self._bac0point.subscribe_cov(confirmed=True, lifetime=ttl, callback=None)

    def covCancel(self):
        self._bac0point.cancel_cov()

    def read(self, prop='presentValue'):
        return self._bac0point.read_property(prop)

    def refresh(self):
        self.reloadBacnetProperties()
        if self.isWritable():
            self.reloadPriorityArray()
        self._bac0point.value

    def __repr__(self):
        svalue=str(self.value)
        # if self.label:
            # svalue += ':%s' % self.label
        if self.unit:
            svalue += ' %s' % self.unit
        return '<%s(%s:%s#%s=%s)>' % (self.__class__.__name__,
            self.name,
            self.type, self.address,
            svalue)

    def dump(self):
        t=PrettyTable()
        t.field_names=['property', 'value']
        t.align['property']='l'
        t.align['value']='l'
        t.add_row(['class', self.__class__.__name__])
        t.add_row(['name', self.name])
        t.add_row(['description', self.description])
        t.add_row(['type', self.type])
        t.add_row(['address', self.address])
        t.add_row(['descriptor', self.descriptor])
        t.add_row(['value', self.value])
        t.add_row(['age', self.age()])
        try:
            t.add_row(['boolValue', self.boolValue()])
        except:
            pass
        if self.label:
            t.add_row(['label', self.label])
        labels=self.labels
        if labels:
            index=1
            for label in labels:
                t.add_row(['label[%d]' % index, label])
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
                if key not in self.name.lower() and key not in self.description.lower() and key not in self.type.lower():
                    return False
            return True
        return True

    def poll(self, delay=15):
        """Register a polling task on this point"""
        self.pollStop()
        self._bac0point.poll(command='start', delay=delay)

    def pollStop(self):
        """Unregister polling task on this point"""
        self._bac0point.poll(command='stop')


class BACPointInput(BACPoint):
    pass


class BACPointWritable(BACPoint):
    def isWritable(self):
        return True

    def write(self, value, prop='presentValue', priority=''):
        try:
            if value=='null':
                # relinquish
                return self._bac0point.write(value, prop=prop)

            value=self._normalizeValue(value)
            return self._bac0point.write(value, prop=prop)
        except:
            pass
        return None

    def reloadPriorityArray(self):
        self._bac0point.read_priority_array()

    def priority(self, priority=None):
        if priority:
            try:
                # FIXME: This will trigger a read for every call!
                # https://github.com/ChristianTremblay/BAC0/blob/master/BAC0/core/devices/Points.py
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
        return not self.isOn()

    def boolValue(self):
        return self.isOn()

    def _normalizeValue(self, value):
        try:
            if type(value) is str:
                svalue=value.lower()
                if svalue=='on':
                    return 'active'
                if svalue=='off':
                    return 'inactive'
                if svalue=='1':
                    return 'active'
                if svalue=='0':
                    return 'inactive'
                try:
                    labels=self.labels
                    if svalue==labels[0].lower():
                        return 'inactive'
                    if svalue==labels[1].lower():
                        return 'active'
                except:
                    pass
            if type(value) is bool:
                if value:
                    return 'active'
                return 'active'
            value=bool(value)
        except:
            pass
        return 'inactive'

    @property
    def labels(self):
        try:
            return [self.bacnetProperty('inactiveText'), self.bacnetProperty('activeText')]
        except:
            pass

    @BACPoint.label.getter
    def label(self):
        try:
            labels=self.labels
            if self.isOn():
                return labels[1]
            return labels[0]
        except:
            pass


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

    def count(self):
        try:
            return len(self.labels)
        except:
            pass
        return 0

    @property
    def labels(self):
        """return multiState available labels (first label is bacnet value 1)"""
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

    def valueFromLabel(self, label):
        try:
            return self.labels.index(label)+1
        except:
            pass

    def _normalizeValue(self, value):
        try:
            if type(value) is str:
                labels=self.labels
                svalue=value.lower()
                if labels:
                    index=1
                    for label in labels:
                        if label.lower()==svalue:
                            return index
                        index+=1
            value=int(value)
        except:
            pass
        return value


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
    def on(self):
        self.write('active')

    def off(self):
        self.write('inactive')

    def toggle(self):
        if self.isOn():
            self.off()
        else:
            self.on()


class BACPointMultiStateInput(BACPointMultiState, BACPointInput):
    pass


class BACPointMultiStateOutput(BACPointMultiState, BACPointOutput):
    pass


class BACPointMultiStateValue(BACPointMultiState, BACPointValue):
    pass


if __name__=='__main__':
    pass
