from .bacpoint import BACPoint
from .bacpoints import BACPointsBag

import BAC0
import xml.etree.ElementTree as ET


from digimat.bac0 import BACPoint


class XMLRemoteCommand(object):
    def __init__(self, station, module, bag=None):
        super().__init__()
        self._station=int(station)
        self._module=int(module)
        self._root=ET.fromstring("<Command/>")
        self._station=station
        self._item=0
        self.load(bag)

    def load(self, bag):
        if bag:
            assert(isinstance(bag, BACBag))
            for point in bag:
                self.add(point)

    def skip(self, count=1):
        self._item+=count

    def next(self):
        return self.skip(1)

    def go(self, item):
        self._item=item

    def add(self, point, item=None):
        assert(isinstance(point, BACPoint))
        item=ET.SubElement(self._root, 'BaseObject')
        item.set('station', str(self._station))
        item.set('number', str(self._item))

        baci=ET.SubElement(item, 'RSCBACI')
        baci.set('installed', '1')
        baci.set('chModule', str(self._module))
        baci.set('chService', str(BAC0.bacpypes.basetypes.ServicesSupported.bitNames['readProperty']))
        baci.set('wPropertyId', str(BAC0.bacpypes.basetypes.PropertyIdentifier.presentValue))
        baci.set('wObjectType', str(BAC0.bacpypes.basetypes.ObjectTypesSupported.bitNames[point.type]))
        baci.set('dwObjectInstance', str(point.address))
        baci.set('chUnit', str(point.digUnit()))
        baci.set('chUpdateDelay', '15')

        general=ET.SubElement(item, 'General')
        general.set('mainLabel', '%s %s' % (point.name, point.description))
        if point.isMultiState():
            labels=point.labels
            if labels:
                strlabels='X;' + ';'.join(labels)
                general.set('multiStateLabels', strlabels)
        elif point.isBinary():
            labels=point.labels
            if labels:
                general.set('lowLabel', labels[0])
                general.set('highLabel', labels[1])

        general.set('decimals', str(point.digDecimals()))

        self.skip()

    def tostring(self):
        return ET.tostring(self._root)

    def write(self, fname):
        try:
            with open(fname, 'wb') as f:
                f.write(self.tostring())
            return True
        except:
            pass


  # <BaseObject category="RSBACI" station="2" number="162">
    # <RSCBACI installed="1" applyDefaultValue="1" chModule="18" chUpdateDelay="15" chUnit="1" chService="1" wObjectType="0" dwObjectInstance="8" wPropertyId="85" dwPropertyIndex="4294967295" />
    # <General mainLabel="temperature ambiance" mainLabelLow="trop basse" mainLabelNormal="normale" mainLabelHigh="trop haute" />
  # </BaseObject>
