"""
snmp_scan.py
- Scans x.x.x.1..254 (derived from --network) and queries a single OID.
- Supports SNMP v2c and SNMP v3 (noAuthNoPriv / authNoPriv / authPriv)
- Windows-friendly: closes SNMP dispatcher to avoid "Event loop is closed" warnings.
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

# ============================
# Defaults
# ============================
DEFAULT_COMMUNITY = "admin"
DEFAULT_OID = "1.3.6.1.4.1.4515.1.3.6.1.1.1.2.0"


# ============================
# SNMP v3 maps
# ============================
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
    "AES": usmAesCfb128Protocol,
    "AES128": usmAesCfb128Protocol,
    "AES192": usmAesCfb192Protocol,
    "AES256": usmAesCfb256Protocol,
}


# ============================
# Helpers
# ============================
def parse_network_to_base(network: str) -> str:
    """
    Accepts:
      - "172.16.40.0"
      - "172.16.40.0/24"
    Returns base like "172.16.40"
    """
    if "/" in network:
        net = ipaddress.ip_network(network, strict=False)
        addr = str(net.network_address)
    else:
        addr = str(ipaddress.ip_address(network))

    return ".".join(addr.split(".")[:3])


def build_v3_user_data(args: argparse.Namespace) -> UsmUserData:
    auth_proto = AUTH_PROTOS.get((args.auth_proto or "NONE").upper())
    priv_proto = PRIV_PROTOS.get((args.priv_proto or "NONE").upper())

    if args.sec_level == "noAuthNoPriv":
        return UsmUserData(userName=args.user)

    if args.sec_level == "authNoPriv":
        return UsmUserData(
            userName=args.user,
            authKey=args.auth_key,
            authProtocol=auth_proto,
        )

    return UsmUserData(
        userName=args.user,
        authKey=args.auth_key,
        authProtocol=auth_proto,
        privKey=args.priv_key,
        privProtocol=priv_proto,
    )


# ============================
# Core SNMP logic
# ============================
async def snmp_get_value(
    ip: str,
    oid: str,
    timeout: float,
    retries: int,
    engine,
    security,
) -> Optional[Tuple[str, str]]:
    try:
        error_indication, error_status, _, var_binds = await getCmd(
            engine,
            security,
            UdpTransportTarget((ip, 161), timeout=timeout, retries=retries),
            ContextData(),
            ObjectType(ObjectIdentity(oid)),
        )

        if error_indication or error_status:
            return None

        for _, val in var_binds:
            s = str(val).strip().strip('"')
            if not s or "nosuch" in s.lower():
                return None
            return ip, s

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

    async def worker(i: int):
        async with sem:
            return await snmp_get_value(
                f"{base}.{i}",
                oid,
                timeout,
                retries,
                engine,
                security,
            )

    tasks = [asyncio.create_task(worker(i)) for i in range(1, 255)]
    results = await asyncio.gather(*tasks)

    engine.transportDispatcher.closeDispatcher()

    found = [r for r in results if r]
    found.sort(key=lambda x: tuple(map(int, x[0].split("."))))
    return found


# ============================================================
# ✅ PROGRAMMATIC API (used by FastAPI)
# ============================================================
async def scan_network(
    network: str,
    community: str = DEFAULT_COMMUNITY,
    oid: str = DEFAULT_OID,
    timeout: float = 1.0,
    retries: int = 1,
    max_concurrent: int = 100,
) -> List[Tuple[str, str]]:
    """
    Programmatic SNMP scan (v2c).
    Returns: List[(ip, productName)]
    """
    base = parse_network_to_base(network)
    security = CommunityData(community, mpModel=1)

    return await scan_subnet(
        base=base,
        oid=oid,
        timeout=timeout,
        retries=retries,
        max_concurrent=max_concurrent,
        security=security,
    )


# ============================
# CLI entrypoint (unchanged)
# ============================
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
    p = argparse.ArgumentParser()
    p.add_argument("-n", "--network", required=True)
    p.add_argument("-v", "--version", choices=["2c", "3"], default="2c")
    p.add_argument("-c", "--community", default=DEFAULT_COMMUNITY)
    p.add_argument("-o", "--oid", default=DEFAULT_OID)

    args = p.parse_args()

    base = parse_network_to_base(args.network)
    security = CommunityData(args.community, mpModel=1)

    rows = asyncio.run(
        scan_subnet(
            base,
            args.oid,
            1.0,
            1,
            100,
            security,
        )
    )

    print_table(rows)


if __name__ == "__main__":
    main()
