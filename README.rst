===================
Python digimat.bac0
===================

This is a Python 3 module basically providing a wrapper around the BAC0 module allowing to access and browse BACnet/IP networks.

.. code-block:: python

    >>> from digimat.bac0 import BAC
    >>> bacnet=BAC('192.168.0.84/24')

Congratulations ! You just have launched a BACnet/IP node binded to your LAN card. If needed you can specify a BBDM router like this

.. code-block:: python

    >>> bacnet=BAC('192.168.0.84/24', router='192.168.2.1')

Now you can start discovering the network

.. code-block:: python

    >>> bacnet.whois()      # return a list of devices detected on the network
    >>> device=bacnet.declareDevice(deviceId, deviceIp)  # this is how to declare manually a device
    >>> bacnet.dump()
    >>> device.dump()

Accessing devices points

.. code-block:: python

    >>> points=device.points
    >>> points.dump()
    >>> point=points[56]
    >>> point=points['pointname']
    >>> point.dump()

And so on...

This module provides class BAC(), BACPoints(), BACPoint()
This doc is a minimal draft. Good luck.
