===================
Python digimat.bac0
===================

This is a Python 3 module basically providing a wrapper around the [BAC0] (https://bac0.readthedocs.io/en/latest/) module, 
itself using [bacpypes] (https://github.com/JoelBender/bacpypes), allowing to access and browse BACnet/IP networks. The main goal of this module id to provide
a simple way to discover/browse/interact with BACnet/IP devices on a network, especially from a terminal session. This module can be used interactively or within an application. Install this module with a *pip install -U digimat.bac0* command.

.. code-block:: python

    >>> from digimat.bac0 import BAC
    >>> bacnet=BAC(network='192.168.0.84/24')


Congratulations ! You just have launched a BACnet/IP node binded to your LAN card (ip 192.168.0.84, netmask 255.255.255.0). The underlying BAC0 module has started a thread managing
the remote bacnet nodes (understand remote "BACnet servers") you will declare to your node. You have to provide the ip ("ip/networkSize") that will be used to send/receive 
every BACnet UDP messages. Under Linux/MacOS hots, this can be done automagically if you have installed the [netifaces] (https://pypi.org/project/netifaces/) module (install it with *pip install -U netifaces*). If so, you can
ommit the *network* parameter (we will try to guess the ip address of you network card)

.. code-block:: python

    >>> bacnet=BAC() # return a BAC object
    >>> bacnet
    <BAC:192.168.0.84/24(0 devices)>


If needed, you can give a bbmd router ('ipAddress[:port]') to the constructor

.. code-block:: python

    >>> bacnet=BAC(router='192.168.2.1')


Now, assuming that your network settings are correct, you can start discovering the network

.. code-block:: python

    >>> bacnet.whois()      # return a list of devices detected on the network
   [('192.168.0.15', 8015), ('192.168.0.80', 4000)]


The *whois()* method returns a list of remote BACnet/IP servers detected on the network (ip/deviceId). You can then can add to your node thoses remote *devices* (BACnet servers)

.. code-block:: python

    >>> device=bacnet.declareDevice(8015, '192.168.0.15')
    >>> device=bacnet.declareDevice(8015, ip='192.168.0.15', poll=60) # with polling time specified (default is to poll it every 15s)


In fact, if the device is detected by the whois(), you can declare a node based on it's id or it's ip address

.. code-block:: python

    >>> device=bacnet.declareDevice(8015) # return a BACDevice object
    >>> device=bacnet.declareDevice('192.168.0.15') # equivalent
    >>> device
    <BACDevice:8015#0(Digimat:Digimat3_CPU_Bridge, operational, 66 points)>

    >>> bacnet.discover() # this will magically declare every device reported by whois()


Every BAC* object has a .dump() method, very useful in interactive sessions

.. code-block:: python

    >>> bacnet.dump()
    +---+---------+------+--------------+---------+---------------------+-------------+-------------+---------+
    | # | name    |  id  |      ip      | vendor  | model               |    status   | description | #points |
    +---+---------+------+--------------+---------+---------------------+-------------+-------------+---------+
    | 0 | s_112_1 | 8015 | 192.168.0.15 | Digimat | Digimat3_CPU_Bridge | operational | S+T         |    66   |
    +---+---------+------+--------------+---------+---------------------+-------------+-------------+---------+

    >>> device.dump()
    +-----------------------+--------------+
    | property              | value        |
    +-----------------------+--------------+
    | ip                    | 192.168.0.15 |
    | id                    | 8015         |
    | name                  | s_112_1      |
    | description           | S+T          |
    | systemStatus          | operational  |
    | vendorName            | Digimat      |
    | vendorIdentifier      | 892          |
    | points                | 66           |
    | segmentationSupported | True         |
    | analogInput           | 16           |
    | analogOutput          | 8            |
    | binaryInput           | 31           |
    | binaryOutput          | 11           |
    +-----------------------+--------------+


Once a device has been declared, you can retrieve it with bacnet.device(...) or directly with a bacnet[...] request. You can use either the index (0), the name (s_112_1), the id (8105) or the ip (192.168.0.15) 
to retrieve your device from the BAC object. If you redeclare a device already existing, it will be simply returns the existing one (no duplication).

You will have to dig a bit into the *BAC* and *BACDevice* objects to find avalaible methods and properties. It's now time to access to the points (variables) of our device, all provided
by the device.points property, returning a *BACPoints* object

.. code-block:: python

    >>> points=device.points
    >>> points
    <BACPoints(66 points)>

    >>> points.dump()
    +----+---------------------+-------------------------------------------------------------------------+--------------+---------+--------------------+----------+------+-------+-------+------+
    | #  | name                | description                                                             | type         | address |              value | state    | unit |  COV  |  OoS  | PRI  |
    +----+---------------------+-------------------------------------------------------------------------+--------------+---------+--------------------+----------+------+-------+-------+------+
    | 0  | r_112_1_cio_13056_0 | sonde exterieure                                                        | analogInput  |   13056 |  31.57793617248535 | 31.58    | C    | False | False | None |
    | 1  | r_112_1_cio_13057_0 | sonde depart chaudiere                                                  | analogInput  |   13057 |  26.29434585571289 | 26.29    | C    | False | False | None |
    | 2  | r_112_1_cio_13058_0 | sonde depart radiateurs                                                 | analogInput  |   13058 | 31.489280700683594 | 31.49    | C    | False | False | None |
    | 3  | r_112_1_cio_13059_0 | sonde depart chauffage de sol                                           | analogInput  |   13059 | 27.392995834350586 | 27.39    | C    | False | False | None |
    | 4  | r_112_1_cio_13060_0 | pot.physique consigne depart chauffage de sol (-10;+10C)                | analogInput  |   13060 |  4.917219638824463 | 4.92     | C    | False | False | None |
    | 5  | r_112_1_cio_13061_0 | pot.physique consigne depart radiateurs (-10;+10C)                      | analogInput  |   13061 |  2.920119047164917 | 2.92     | C    | False | False | None |
    | 6  | r_112_1_cio_13062_0 | sonde ambiance bureau direction rez                                     | analogInput  |   13062 |  26.65079689025879 | 26.65    | C    | False | False | None |
    | 7  | r_112_1_cio_13063_0 | pot.temperature bureau direction rez                                    | analogInput  |   13063 | 21.572412490844727 | 21.57    | C    | False | False | None |
    | 8  | r_112_1_cio_13064_0 | sonde ambiance bureau direction cote hall rez                           | analogInput  |   13064 | 26.797283172607422 | 26.80    | C    | False | False | None |
    | 9  | r_112_1_cio_13065_0 | pot.temperature bureau direction cote hall rez                          | analogInput  |   13065 |  21.72866439819336 | 21.73    | C    | False | False | None |
    | 10 | r_112_1_cio_13066_0 | sonde ambiance salle de conferences                                     | analogInput  |   13066 | 28.223087310791016 | 28.22    | C    | False | False | None |
    | 11 | r_112_1_cio_13067_0 | sonde ambiance temperature bureau comptabilite  rez                     | analogInput  |   13067 | 26.503700256347656 | 26.50    | C    | False | False | None |
    | 12 | r_112_1_cio_13068_0 | sonde ambiance bureau schematique s-sol                                 | analogInput  |   13068 | 24.297245025634766 | 24.30    | C    | False | False | None |
    | 13 | r_112_1_cio_13069_0 | pot.temperature bureau schematique s-sol                                | analogInput  |   13069 |               21.0 | 21.00    | C    | False | False | None |
    | 14 | r_112_1_cio_13070_0 | sonde ambiance bureau individuel s-sol                                  | analogInput  |   13070 | 25.986724853515625 | 25.99    | C    | False | False | None |
    | 15 | r_112_1_cio_13071_0 | pot.temperature bureau individuel s-sol                                 | analogInput  |   13071 |   20.4005184173584 | 20.40    | C    | False | False | None |
    | 16 | r_112_1_cio_18176_0 | vanne depart radiateurs                                                 | analogOutput |   18176 |                0.0 | 0.00     | %    | False | False |  16  |
    | 17 | r_112_1_cio_18177_0 | vanne depart general chauffage de sol                                   | analogOutput |   18177 |                0.0 | 0.00     | %    | False | False |  16  |
    | 18 | r_112_1_cio_18178_0 | vannes depart chauffage de sol bureau direction rez                     | analogOutput |   18178 |                0.0 | 0.00     | %    | False | False |  16  |
    | 19 | r_112_1_cio_18179_0 | vanne depart chauffage de sol bureau direction cote hall rez            | analogOutput |   18179 |                0.0 | 0.00     | %    | False | False |  16  |
    | 20 | r_112_1_cio_18180_0 | vanne depart chauffage de sol bureau comptabilite rez                   | analogOutput |   18180 |                0.0 | 0.00     | %    | False | False |  16  |
    | 21 | r_112_1_cio_18181_0 | vanne depart chauffage de sol bureau schematique s-sol                  | analogOutput |   18181 |                0.0 | 0.00     | %    | False | False |  16  |
    | 22 | r_112_1_cio_18182_0 | vanne depart chauffage de sol bureau individuel s-sol                   | analogOutput |   18182 |                0.0 | 0.00     | %    | False | False |  16  |
    | 23 | r_112_1_cio_18183_0 | consigne puissance bruleur                                              | analogOutput |   18183 | 4.9988555908203125 | 5.00     | %    | False | False |  16  |
    | 24 | r_112_1_cio_256_0   | circulateur depart radiateurs                                           | binaryInput  |     256 |           inactive | arret    | None | False | False | None |
    | 25 | r_112_1_cio_257_0   | thermique circulateur depart radiateurs                                 | binaryInput  |     257 |           inactive | normal   | None | False | False | None |
    | 26 | r_112_1_cio_258_0   | circulateur depart chauffage de sol                                     | binaryInput  |     258 |           inactive | arret    | None | False | False | None |
    | 27 | r_112_1_cio_259_0   | thermique circulateur depart chauffage de sol                           | binaryInput  |     259 |           inactive | normal   | None | False | False | None |
    | 28 | r_112_1_cio_260_0   | coffret pompe fosse eaux usees chaufferie                               | binaryInput  |     260 |           inactive | normal   | None | False | False | None |
    | 29 | r_112_1_cio_261_0   | effraction bureau direction rez (capteur a fil)                         | binaryInput  |     261 |           inactive | hors     | None | False | False | None |
    | 30 | r_112_1_cio_262_0   | effraction bureau comptabilite rez (capteur a fil)                      | binaryInput  |     262 |           inactive | hors     | None | False | False | None |
    | 31 | r_112_1_cio_263_0   | effraction bureau schematique chaufferie + saleve s-sol (capteur a fil) | binaryInput  |     263 |           inactive | hors     | None | False | False | None |
    | 32 | r_112_1_cio_264_0   | effraction stock s-sol (capteur a fil)                                  | binaryInput  |     264 |           inactive | hors     | None | False | False | None |
    | 33 | r_112_1_cio_265_0   | effraction bureau construction rez (capteur a fil)                      | binaryInput  |     265 |           inactive | hors     | None | False | False | None |
    | 34 | r_112_1_cio_266_0   | alarme feu sur canal 1 recepteur (transmetteurs a ondes)                | binaryInput  |     266 |           inactive | normal   | None | False | False | None |
    | 35 | r_112_1_cio_267_0   | effraction divers detecteurs IR interieur (capteurs sans fil)           | binaryInput  |     267 |           inactive | hors     | None | False | False | None |
    | 36 | r_112_1_cio_268_0   | mouvement divers detecteurs IR exterieur (capteurs sans fil)            | binaryInput  |     268 |           inactive | hors     | None | False | False | None |
    | 37 | r_112_1_cio_269_0   | effraction porte d'entree rez (capteur a fil)                           | binaryInput  |     269 |           inactive | hors     | None | False | False | None |
    | 38 | r_112_1_cio_270_0   | interrupteur a cle 1 (activation du systeme de surveillance)            | binaryInput  |     270 |           inactive | hors     | None | False | False | None |
    | 39 | r_112_1_cio_271_0   | sabotage interrupteur a cle                                             | binaryInput  |     271 |           inactive | hors     | None | False | False | None |
    | 40 | r_112_1_cio_272_0   | fusibles de commande                                                    | binaryInput  |     272 |           inactive | en ordre | None | False | False | None |
    | 41 | r_112_1_cio_273_0   | delestage SI tbl. Tableau chaufferie                                    | binaryInput  |     273 |           inactive | hors     | None | False | False | None |
    | 42 | r_112_1_cio_274_0   | temperature depart chauffage de sol                                     | binaryInput  |     274 |           inactive | normale  | None | False | False | None |
    | 43 | r_112_1_cio_275_0   | temperature gas cheminee                                                | binaryInput  |     275 |           inactive | normale  | None | False | False | None |
    | 44 | r_112_1_cio_276_0   | alarme feu chaufferie (capteur a fil)                                   | binaryInput  |     276 |           inactive | normal   | None | False | False | None |
    | 45 | r_112_1_cio_277_0   | interrupteur a cle 2 - poussoir (quittance sirene) (hors-service)       | binaryInput  |     277 |           inactive | hors     | None | False | False | None |
    | 46 | r_112_1_cio_278_0   | niveau haut fosse eau pluviale cote jardin                              | binaryInput  |     278 |           inactive | normal   | None | False | False | None |
    | 47 | r_112_1_cio_279_0   | effraction salle de conferences rez (capteur a fil)                     | binaryInput  |     279 |           inactive | hors     | None | False | False | None |
    | 48 | r_112_1_cio_512_0   | Thermique pompe de fosse eau pluviale cote parking                      | binaryInput  |     512 |           inactive | normal   | None | False | False | None |
    | 49 | r_112_1_cio_513_0   | Pompe de fosse eau pluviale cote parking                                | binaryInput  |     513 |           inactive | arret    | None | False | False | None |
    | 50 | r_112_1_cio_514_0   | Interrupteur pompe de fosse eau pluviale cote parking                   | binaryInput  |     514 |             active | sur auto | None | False | False | None |
    | 51 | r_112_1_cio_515_0   | niveau haut fosse eau pluviale cote parking                             | binaryInput  |     515 |           inactive | normal   | None | False | False | None |
    | 52 | r_112_1_cio_516_0   | Surveillance tension coffret fosse eau pluviale cote parking            | binaryInput  |     516 |           inactive | normal   | None | False | False | None |
    | 53 | r_112_1_cio_534_0   | entree test 1                                                           | binaryInput  |     534 |             active | en       | None | False | False | None |
    | 54 | r_112_1_cio_535_0   | entree TEST 2                                                           | binaryInput  |     535 |             active | en       | None | False | False | None |
    | 55 | r_112_1_cio_7937_0  | cmd.bouilleur                                                           | binaryOutput |    7937 |           inactive | hors     | None | False | False |  16  |
    | 56 | r_112_1_cio_7938_0  | cmd.circulateur depart radiateurs                                       | binaryOutput |    7938 |           inactive | hors     | None | False | False |  16  |
    | 57 | r_112_1_cio_7939_0  | cmd.circulateur depart chauffage de sol                                 | binaryOutput |    7939 |           inactive | hors     | None | False | False |  16  |
    | 58 | r_112_1_cio_7941_0  | cmd.ventilateur extraction local chaufferie s-sol                       | binaryOutput |    7941 |             active | en       | None | False | False |  16  |
    | 59 | r_112_1_cio_8192_0  | cmd.feu tournant                                                        | binaryOutput |    8192 |           inactive | hors     | None | False | False |  16  |
    | 60 | r_112_1_cio_8193_0  | cmd.sirene                                                              | binaryOutput |    8193 |           inactive | hors     | None | False | False |  16  |
    | 61 | r_112_1_cio_8194_0  | cmd.tonalite sirene                                                     | binaryOutput |    8194 |           inactive | hors     | None | False | False |  16  |
    | 62 | r_112_1_cio_8195_0  | cmd.led activation (rouge)                                              | binaryOutput |    8195 |           inactive | hors     | None | False | False |  16  |
    | 63 | r_112_1_cio_8196_0  | cmd.PAC salle de conferences                                            | binaryOutput |    8196 |           inactive | hors     | None | False | False |  16  |
    | 64 | r_112_1_cio_8197_0  | cmd.radiateur electrique salle de conferences                           | binaryOutput |    8197 |           inactive | hors     | None | False | False |  16  |
    | 65 | r_112_1_cio_8198_0  | TEST LCH                                                                | binaryOutput |    8198 |           inactive | hors     | None | False | False |  16  |
    +----+---------------------+-------------------------------------------------------------------------+--------------+---------+--------------------+----------+------+-------+-------+------+

    >>> device.points.dump('sonde') # output can be filtered (by part of names or descriptions)
    +----+---------------------+-----------------------------------------------------+-------------+---------+--------------------+-------+------+-------+-------+------+
    | #  | name                | description                                         | type        | address |              value | state | unit |  COV  |  OoS  | PRI  |
    +----+---------------------+-----------------------------------------------------+-------------+---------+--------------------+-------+------+-------+-------+------+
    | 0  | r_112_1_cio_13056_0 | sonde exterieure                                    | analogInput |   13056 |  31.62188148498535 | 31.62 | C    | False | False | None |
    | 1  | r_112_1_cio_13057_0 | sonde depart chaudiere                              | analogInput |   13057 |  26.29434585571289 | 26.29 | C    | False | False | None |
    | 2  | r_112_1_cio_13058_0 | sonde depart radiateurs                             | analogInput |   13058 | 31.489280700683594 | 31.49 | C    | False | False | None |
    | 3  | r_112_1_cio_13059_0 | sonde depart chauffage de sol                       | analogInput |   13059 | 27.392995834350586 | 27.39 | C    | False | False | None |
    | 6  | r_112_1_cio_13062_0 | sonde ambiance bureau direction rez                 | analogInput |   13062 |  26.64103126525879 | 26.64 | C    | False | False | None |
    | 8  | r_112_1_cio_13064_0 | sonde ambiance bureau direction cote hall rez       | analogInput |   13064 | 26.787517547607422 | 26.79 | C    | False | False | None |
    | 10 | r_112_1_cio_13066_0 | sonde ambiance salle de conferences                 | analogInput |   13066 | 28.232852935791016 | 28.23 | C    | False | False | None |
    | 11 | r_112_1_cio_13067_0 | sonde ambiance temperature bureau comptabilite  rez | analogInput |   13067 | 26.503700256347656 | 26.50 | C    | False | False | None |
    | 12 | r_112_1_cio_13068_0 | sonde ambiance bureau schematique s-sol             | analogInput |   13068 |   24.3167781829834 | 24.32 | C    | False | False | None |
    | 14 | r_112_1_cio_13070_0 | sonde ambiance bureau individuel s-sol              | analogInput |   13070 | 26.016021728515625 | 26.02 | C    | False | False | None |
    +----+---------------------+-----------------------------------------------------+-------------+---------+--------------------+-------+------+-------+-------+------+


Each point of the *BACPoints* object is accessible by it's index, type or a part of *something belonging* to it 

.. code-block:: python

    >>> point=points[8]
    >>> point
    <BACPointAnalogInput(r_112_1_cio_13064_0:analogInput#13064=26.51 degreesCelsius)>

    >>> point.dump()
    +--------------+-----------------------------------------------+
    | property     | value                                         |
    +--------------+-----------------------------------------------+
    | class        | BACPointAnalogInput                           |
    | name         | r_112_1_cio_13064_0                           |
    | description  | sonde ambiance bureau direction cote hall rez |
    | type         | analogInput                                   |
    | address      | 13064                                         |
    | value        | 26.57267189025879                             |
    | state        | 26.57                                         |
    | unit         | degreesCelsius (C)                            |
    | COV          | False                                         |
    | OutOfService | False                                         |
    | index        | 8                                             |
    +--------------+-----------------------------------------------+

    >>> point=device.points.analogInput(13056)
    >>> point=bacnet[8015].points.analogOuput(18181)

    >>> points['sonde hall'] # return the first object matching to this
    <BACPointAnalogInput(r_112_1_cio_13064_0:analogInput#13064=26.55 degreesCelsius)>

    >>> point=point['r_112_1_cio_13067_0']
    >>> point=point['13067']


Points are exposed through *BACPoint* objects (generic class), derived in BACPointBinaryInput, BACPointBinaryOutput, BACPointAnalogInput, BACPointAnalogOutput, BACPointBinaryValue, BACPointAnalogValue, 
BACPointMultiStateInput, BACPointMultiStateOutput, BACPointMultiStateValue objects, each providing specialized BACPoint extensions. You will have to dig a bit into theses objects to learn what helper they provide. Using
[bpython] (https://bpython-interpreter.org/) interactive interpreter with it's autocompletion feature is a very convenient way to discover thoses object (with the actual lack of documentation)

.. code-block:: python

    >>> point.
    ┌───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
    │ activePriority               address                      bacnetProperty               bacnetproperties             celciusToFahrenheit          cov                                          │
    │ covCancel                    description                  digDecimals                  digUnit                      digUnitStr                   dump                                         │
    │ fahrenheitToCelcius          index                        isAnalog                     isBinary                     isCOV                        isMultiState                                 │
    │ isOutOfService               isWritable                   label                        match                        name                         onInit                                       │
    │ poll                         pollStop                     priority                     properties                   read                         refresh                                      │
    │ reloadBacnetProperties       state                        toCelcius                    type                         unit                         unitNumber                                   │
    │ value                                                                                                                                                                                         │
    └───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

    >>> point.value
    26.699626922607422
    >>> point.unit
    'degreesCelsius'

    >>> point.value=12.0 # if a point is writable, this will change it's value
    >>> point.write(12.0, priority=8)
    >>> point.write(12.0, prop='presentValue', priority=8)

    # for binary values
    >>> point.on()
    >>> point.off()
    >>> point.toggle()

    # for multiState values
    >>> point.state
    >>> point.label
    >>> point.labels


A device automatically refresh it's points every 15s (the device's polling time could be specified at object creation/declaration). You can stop this with device.pollStop() or adjust the polling period with device.poll(60). This is the device polling global setting. Every point may also be polled individually with point.poll(10) and point.pollStop(). Of course you may wish to set an individual poll for each point of the device with deice.points.poll(60). But a global device.poll() is a more efficient way to do it.
Refresh may also be done throug COV (Change Of Value) mechanism. By default, COV is not enabled on a device. You can enable COV subscriptions on a point with point.cov(), and disable it with point.covCancel(). This can also be done on each points with device.points.cov(). By default, the COV timeout is set to 300s. The poll and/or COV mechanism ensure the autorefresh of the points values. If needed, a point can be refreshed manually with point.refresh(). As suspected, the device.refresh() or device.points.refresh() does this globally.

If a *BACPoint* object doesn't expose something that would be useful, either ask it (we will try to add this support) or use the underlying ._bac0point object which is the BAC0's Point object (https://bac0.readthedocs.io/en/latest/BAC0.core.devices.html#BAC0.core.devices.Points.Point) associated to this point.
If a *BACDevice* object doesn't expose something that would be useful, you can use the underlying ._bac0device BAC0 device object (https://github.com/ChristianTremblay/BAC0/blob/master/BAC0/core/devices/Device.py).
If the *BAC* object doesn't expose something that would be useful, you can use the underlying ._bac0 BAC0 application object (https://github.com/ChristianTremblay/BAC0/blob/master/BAC0/scripts/Lite.py).

The module provide a simple BACnet browser application you can start with "python -i -m digimat.bac0 [--ip "192.168.0.84/24"] [--router x.x.x.x] [--debug]". This will launch the following application

.. code-block:: python

    parser=argparse.ArgumentParser(description='BACnet/IP browser')
    parser.add_argument('--router', dest='router', type=str, help='BBMD router address')
    parser.add_argument('--network', dest='network', type=str, help='optional ip/netsize of the BACnet/IP interface')
    parser.add_argument('--debug', dest='debug', action='store_true', help='enable debug/verbose mode')
    args=parser.parse_args()

    bacnet=BAC(network=args.network, router=args.router)
    if args.debug:
        bacnet.BAC0LogDebug()

    if bacnet.discover():
        bacnet.dump()


When launched interactively (-i), you'll have a working *bacnet* variable (a BAC object) ready to be used in just one command line.

We will try to add objects and methods docstring as soon as possible to help the use of theses objects. Please let us know (fhess@st-sa.ch) is this is useful for someone (for us it is).
