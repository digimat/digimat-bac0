import time
import argparse
from digimat.bac0 import BAC

parser=argparse.ArgumentParser(description='BACnet/IP browser')
parser.add_argument('--router', dest='router', type=str, help='BBMD router address')
parser.add_argument('--network', dest='network', type=str, help='optional ip/netsize of the BACnet/IP interface')
parser.add_argument('--debug', dest='debug', action='store_true', help='enable debug/verbose mode')
args=parser.parse_args()

b=BAC(network=args.network, router=args.router)
if args.debug:
    b.BAC0LogDebug()

b.whois()
time.sleep(1)
b.whois()
time.sleep(1)
b.whois()
