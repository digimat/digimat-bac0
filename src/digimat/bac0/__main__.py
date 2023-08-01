import argparse
from digimat.bac0 import BAC

parser=argparse.ArgumentParser(description='BACnet/IP browser')
parser.add_argument('--router', dest='router', type=str, help='BBMD router address')
parser.add_argument('--network', dest='network', type=str, help='optional ip/netsize of the BACnet/IP interface')
parser.add_argument('--debug', dest='debug', action='store_true', help='enable debug/verbose mode')
parser.add_argument('--discover', dest='discover', action='store_true', help='launch a discover on startup')
args=parser.parse_args()

bacnet=BAC(network=args.network, router=args.router)
if args.debug:
    bacnet.BAC0LogDebug()

if args.discover:
    bacnet.discover()

print("I have created this `bacnet` variable for you:")
print(bacnet)

if bacnet.count()>0:
    bacnet.dump()
