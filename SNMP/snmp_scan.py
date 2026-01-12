"""
snmp_scan.py
- Scans x.x.x.1..254 (derived from --network) and queries a single OID.
- Supports SNMP v2c and SNMP v3 (noAuthNoPriv / authNoPriv / authPriv)
- Windows-friendly: closes SNMP dispatcher to avoid "Event loop is closed" warnings.

Install:
  py -m pip install pysnmp

Examples:
  # SNMP v2c
  py snmp_scan.py -n 172.16.40.0 -v 2c -c admin

  # SNMP v3 (noAuthNoPriv)
  py snmp_scan.py -n 172.16.40.0 -v 3 --user myuser --sec-level noAuthNoPriv

  # SNMP v3 (authNoPriv)
  py snmp_scan.py -n 172.16.40.0 -v 3 --user myuser --sec-level authNoPriv \
      --auth-proto SHA --auth-key "AuthPass123"

  # SNMP v3 (authPriv)
  py snmp_scan.py -n 172.16.40.0 -v 3 --user myuser --sec-level authPriv \
      --auth-proto SHA --auth-key "AuthPass123" \
      --priv-proto AES --priv-key "PrivPass123"
"""

import argparse
import asyncio
import ipaddress
from typing import Optional, Tuple, List

from pysnmp.hlapi.asyncio import (
    SnmpEngine,
    CommunityData,
    UsmUserData,
    UdpTransportTarget,
    ContextData,
    ObjectType,
    ObjectIdentity,
    getCmd,
)

from pysnmp.hlapi import (
    usmNoAuthProtocol,
    usmHMACMD5AuthProtocol,
    usmHMACSHAAuthProtocol,
    usmHMAC128SHA224AuthProtocol,
    usmHMAC192SHA256AuthProtocol,
    usmHMAC256SHA384AuthProtocol,
    usmHMAC384SHA512AuthProtocol,
    usmNoPrivProtocol,
    usmDESPrivProtocol,
    usm3DESEDEPrivProtocol,
    usmAesCfb128Protocol,
    usmAesCfb192Protocol,
    usmAesCfb256Protocol,
)

DEFAULT_COMMUNITY = "admin"
DEFAULT_OID = "1.3.6.1.4.1.4515.1.3.6.1.1.1.2.0"


AUTH_PROTOS = {
    "NONE": usmNoAuthProtocol,
    "MD5": usmHMACMD5AuthProtocol,
    "SHA": usmHMACSHAAuthProtocol,
    "SHA224": usmHMAC128SHA224AuthProtocol,
    "SHA256": usmHMAC192SHA256AuthProtocol,
    "SHA384": usmHMAC256SHA384AuthProtocol,
    "SHA512": usmHMAC384SHA512AuthProtocol,
}

PRIV_PROTOS = {
    "NONE": usmNoPrivProtocol,
    "DES": usmDESPrivProtocol,
    "3DES": usm3DESEDEPrivProtocol,
    "AES": usmAesCfb128Protocol,     # common shorthand
    "AES128": usmAesCfb128Protocol,
    "AES192": usmAesCfb192Protocol,
    "AES256": usmAesCfb256Protocol,
}


def parse_network_to_base(network: str) -> str:
    """
    Accepts:
      - "172.16.40.0"  (treated as /24 base)
      - "172.16.40.0/24"
    Returns base like "172.16.40"
    """
    try:
        if "/" in network:
            net = ipaddress.ip_network(network, strict=False)
            addr = str(net.network_address)
        else:
            addr = str(ipaddress.ip_address(network))

        parts = addr.split(".")
        return ".".join(parts[:3])
    except ValueError:
        raise argparse.ArgumentTypeError('Wrong format. Use like "10.30.6.0" or "10.30.6.0/24"')


def build_v3_user_data(args: argparse.Namespace) -> UsmUserData:
    sec_level = args.sec_level

    auth_proto_key = (args.auth_proto or "NONE").upper()
    priv_proto_key = (args.priv_proto or "NONE").upper()

    auth_proto = AUTH_PROTOS.get(auth_proto_key)
    priv_proto = PRIV_PROTOS.get(priv_proto_key)

    if auth_proto is None:
        raise SystemExit(f"Unsupported --auth-proto {args.auth_proto}. Use one of: {', '.join(AUTH_PROTOS)}")
    if priv_proto is None:
        raise SystemExit(f"Unsupported --priv-proto {args.priv_proto}. Use one of: {', '.join(PRIV_PROTOS)}")

    user = args.user

    if sec_level == "noAuthNoPriv":
        return UsmUserData(userName=user)

    if sec_level == "authNoPriv":
        if not args.auth_key:
            raise SystemExit("SNMPv3 authNoPriv requires --auth-key")
        return UsmUserData(
            userName=user,
            authKey=args.auth_key,
            authProtocol=auth_proto,
        )

    # authPriv
    if not args.auth_key:
        raise SystemExit("SNMPv3 authPriv requires --auth-key")
    if not args.priv_key:
        raise SystemExit("SNMPv3 authPriv requires --priv-key")

    # If user picked authPriv but left priv proto NONE, force error (priv must exist)
    if priv_proto_key == "NONE":
        raise SystemExit("SNMPv3 authPriv requires --priv-proto (e.g. AES/AES128/AES256/DES)")

    return UsmUserData(
        userName=user,
        authKey=args.auth_key,
        authProtocol=auth_proto,
        privKey=args.priv_key,
        privProtocol=priv_proto,
    )


async def snmp_get_value(
    ip: str,
    oid: str,
    timeout: float,
    retries: int,
    engine: SnmpEngine,
    security,
) -> Optional[Tuple[str, str]]:
    """
    Returns (ip, value_as_string) if SNMP responds and value is valid.
    Returns None on timeout/noSuchObject/etc.
    """
    try:
        error_indication, error_status, error_index, var_binds = await getCmd(
            engine,
            security,
            UdpTransportTarget((ip, 161), timeout=timeout, retries=retries),
            ContextData(),
            ObjectType(ObjectIdentity(oid)),
        )

        if error_indication:
            return None

        if error_status:
            return None

        for _, val in var_binds:
            s = str(val)
            low = s.lower()
            if "no such object" in low or "nosuchobject" in low:
                return None
            out = s.strip().strip('"')
            if not out:
                return None
            return ip, out

        return None
    except Exception:
        return None


async def scan_subnet(
    base: str,
    oid: str,
    timeout: float,
    retries: int,
    max_concurrent: int,
    security,
) -> List[Tuple[str, str]]:
    sem = asyncio.Semaphore(max_concurrent)
    engine = SnmpEngine()

    async def worker(last_octet: int):
        ip = f"{base}.{last_octet}"
        async with sem:
            return await snmp_get_value(
                ip=ip,
                oid=oid,
                timeout=timeout,
                retries=retries,
                engine=engine,
                security=security,
            )

    tasks = [asyncio.create_task(worker(i)) for i in range(1, 255)]
    results = await asyncio.gather(*tasks)

    # ✅ Important on Windows: close dispatcher cleanly to avoid "Event loop is closed"
    engine.transportDispatcher.closeDispatcher()

    found = [r for r in results if r is not None]
    found.sort(key=lambda x: tuple(int(p) for p in x[0].split(".")))
    return found


def print_table(rows: List[Tuple[str, str]]):
    if not rows:
        print("No snmp devices")
        return

    ip_w = max(len("IP"), max(len(ip) for ip, _ in rows))
    val_w = max(len("ProductName"), max(len(v) for _, v in rows))

    print(f"{'IP'.ljust(ip_w)}  {'ProductName'.ljust(val_w)}")
    print(f"{'-'*ip_w}  {'-'*val_w}")
    for ip, val in rows:
        print(f"{ip.ljust(ip_w)}  {val.ljust(val_w)}")


def main():
    p = argparse.ArgumentParser(description="SNMP scan /24 subnet and print ProductName by OID.")
    p.add_argument("--network", "-n", required=True, help='Example: "172.16.40.0" or "172.16.40.0/24"')
    p.add_argument("--oid", "-o", default=DEFAULT_OID, help="OID to query")
    p.add_argument("--timeout", "-t", type=float, default=1.0, help="Timeout seconds per request (default: 1)")
    p.add_argument("--retries", "-r", type=int, default=1, help="Retries per request (default: 1)")
    p.add_argument("--threads", "-T", type=int, default=100, help="Max concurrent requests (default: 100)")

    p.add_argument("--version", "-v", choices=["2c", "3"], default="2c", help="SNMP version (2c or 3)")

    # v2c
    p.add_argument("--community", "-c", default=DEFAULT_COMMUNITY, help="SNMP v2c community (default: admin)")

    # v3
    p.add_argument("--user", help="SNMP v3 username")
    p.add_argument("--sec-level", choices=["noAuthNoPriv", "authNoPriv", "authPriv"], default="noAuthNoPriv")
    p.add_argument("--auth-proto", choices=list(AUTH_PROTOS.keys()), default="NONE")
    p.add_argument("--auth-key", help="SNMP v3 auth key / passphrase")
    p.add_argument("--priv-proto", choices=list(PRIV_PROTOS.keys()), default="NONE")
    p.add_argument("--priv-key", help="SNMP v3 privacy key / passphrase")

    args = p.parse_args()

    base = parse_network_to_base(args.network)

    if args.version == "2c":
        security = CommunityData(args.community, mpModel=1)  # v2c
    else:
        if not args.user:
            raise SystemExit("SNMPv3 requires --user")
        security = build_v3_user_data(args)

    rows = asyncio.run(
        scan_subnet(
            base=base,
            oid=args.oid,
            timeout=args.timeout,
            retries=max(0, args.retries),
            max_concurrent=max(1, args.threads),
            security=security,
        )
    )

    print_table(rows)


if __name__ == "__main__":
    main()
