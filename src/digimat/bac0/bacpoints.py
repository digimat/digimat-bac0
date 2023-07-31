#!/bin/python

import unicodedata
import re
import os
from prettytable import PrettyTable

# import BAC0

from .bacpoint import BACPoint


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


class BACPoints(object):
    def __init__(self, points=None):
        self._points=[]
        self._pointByName={}
        self._pointByDescriptor={}
        self._indexByName={}
        self.add(points)

    def add(self, points):
        if points is None:
            return

        if isinstance(points, BACPoints):
            points=[point for point in points._points]
        else:
            if type(points) != list:
                points=[points]

        for point in points:
            assert(isinstance(point, BACPoint))
            if self.getByDescriptor(point.descriptor):
                # print("DEBUG: discarding", point)
                continue
            if self.getByName(point.name):
                continue

            index=len(self._points)
            point._index=index
            self._points.append(point)
            self._pointByName[point.name]=point
            self._pointByDescriptor[point.descriptor]=point
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

    def matchFirst(self, keys):
        for p in self._points:
            if p.match(keys):
                return p

    def type(self, objectType):
        return [p for p in self.points if p.type==objectType]

    def analogInput(self, address):
        ptype='analogInput%d' % address
        return self.getByDescriptor(ptype)

    def analogOutput(self, address):
        ptype='analogOutput%d' % address
        return self.getByDescriptor(ptype)

    def binaryInput(self, address):
        ptype='binaryInput%d' % address
        return self.getByDescriptor(ptype)

    def binaryOutput(self, address):
        ptype='binaryOutput%d' % address
        return self.getByDescriptor(ptype)

    def analogValue(self, address):
        ptype='analogValue%d' % address
        return self.getByDescriptor(ptype)

    def binaryValue(self, address):
        ptype='binaryValue%d' % address
        return self.getByDescriptor(ptype)

    def multiStateInput(self, address):
        ptype='multiStateInput%d' % address
        return self.getByDescriptor(ptype)

    def multiStateOutput(self, address):
        ptype='multiStateOutput%d' % address
        return self.getByDescriptor(ptype)

    def multiStateValue(self, address):
        ptype='multiStateValue%d' % address
        return self.getByDescriptor(ptype)

    def __repr__(self):
        return '<%s(%d points)>' % (self.__class__.__name__, len(self.points))

    def count(self):
        return len(self._points)

    def __len__(self):
        return self.count()

    def __iter__(self):
        return iter(self._points)

    def getByName(self, name):
        """search a point based on it's name"""
        try:
            return self._pointByName[name]
        except:
            pass

    def getByIndex(self, index):
        """search a point based on it's device variable index number (#)"""
        try:
            return self._points[int(index)]
        except:
            pass

    def getByDescriptor(self, ptype):
        """search a point based on it's descriptor (i.e analogInput98)"""
        try:
            return self._pointByDescriptor[ptype]
        except:
            pass

    def __getitem__(self, index):
        item=self.getByIndex(index) or self.getByName(index) or self.getByDescriptor(index)
        if not item:
            try:
                item=self.matchFirst(index)
            except:
                pass
        return item

    def index(self, name):
        try:
            return self._indexByName[name]
        except:
            pass

    def dump(self, keys=None, filterOoS=False):
        if type(keys) is list:
            points=keys
        else:
            points=self.pointsMatching(keys)
        if points:
            t=PrettyTable()
            # t.max_table_width=width=os.get_terminal_size()[0]-12
            t.field_names=['#', 'name', 'description', 'descriptor', 'value', 'label', 'age', 'COV', 'OoS']
            t.align['name']='l'
            t.align['description']='l'
            t.align['descriptor']='l'
            t.align['value']='r'
            t.align['label']='l'
            t.align['unit']='l'
            for p in points:
                if filterOoS and p.isOutOfService():
                    continue
                unit=p.unit
                try:
                    age='%ds' % p.age()
                except:
                    age='N/A'

                if p.digUnitStr():
                    unit=p.digUnitStr()
                if not unit:
                    unit=p.label  # FIXME: traffic

                t.add_row([self.index(p.name),
                           p.name,
                           p.description,   # generate traffic the first time
                           p.descriptor,
                           p.strvalue(),
                           unit,
                           age,
                           'X' if p.isCOV() else '',
                           'X' if p.isOutOfService() else ''])
            print(t)

    def quickDump(self, keys=None):
        if type(keys) is list:
            points=keys
        else:
            points=self.pointsMatching(keys)
        if points:
            t=PrettyTable()
            t.field_names=['#', 'name', 'descriptor', 'value', 'age']
            t.align['name']='l'
            t.align['descriptor']='l'
            t.align['value']='r'
            for p in points:
                try:
                    age='%ds' % p.age()
                except:
                    age='N/A'
                t.add_row([self.index(p.name),
                           p.name,
                           p.descriptor,
                           p.strvalue(),
                           age])
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

    def poll(self, delay=15):
        """Register a polling task for each point. Better do it directly on the device (and not on each device's points)"""
        for point in self._points:
            point.pollStop()
            point.poll(delay)

    def pollStop(self):
        """Unregister polling task on each point"""
        for point in self._points:
            point.pollStop()

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


class BACPointsBag(BACPoints):
    def __init__(self, device, points=None):
        # assert(isinstance(BACDevice, device))
        self._device=device
        super().__init__(points=points)

    def __repr__(self):
        return '<%s[%s](%d points)>' % (self.__class__.__name__, self.device.name,
            len(self._points))

    @property
    def device(self):
        return self._device

    def add(self, points):
        if type(points) is str:
            points=self.device.points.match(points)
        super().add(points=points)


if __name__ == "__main__":
    pass
