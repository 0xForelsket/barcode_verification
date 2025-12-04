# Network Configuration Guide

This guide covers network setup for the Barcode Verification System.

---

## 📋 Network Requirements

| Requirement | Details |
|-------------|---------|
| **Port** | 8000 (TCP) |
| **Protocol** | HTTP (HTTPS optional via reverse proxy) |
| **Bandwidth** | Minimal (<1 Mbps per client) |
| **Latency** | <100ms recommended for responsive UI |

---

## 🔧 Basic Network Setup

### Finding Your Device's IP Address

**Windows:**
```cmd
ipconfig
```
Look for "IPv4 Address" under your network adapter (usually something like `192.168.1.xxx`).

**Linux/Raspberry Pi:**
```bash
hostname -I
```
or
```bash
ip addr show | grep inet
```

### Accessing from Other Devices

Once the application is running:
- **Local access**: `http://localhost:8000`
- **Network access**: `http://<device-ip>:8000`

Example: If your device IP is `192.168.1.100`, other devices can access:
- Operator screen: `http://192.168.1.100:8000`
- Monitor screen: `http://192.168.1.100:8000/monitor`
- History: `http://192.168.1.100:8000/history`

---

## 📌 Static IP Configuration

A static IP is recommended so URLs don't change when the device restarts.

### Windows Static IP

1. Open **Settings** → **Network & Internet** → **Ethernet** (or **WiFi**)
2. Click your connection → **Properties** → **Edit** (under IP assignment)
3. Change to **Manual**
4. Enter:
   - IP address: `192.168.1.100` (use an unused IP in your range)
   - Subnet prefix length: `24`
   - Gateway: `192.168.1.1` (your router's IP)
   - Preferred DNS: `192.168.1.1` or `8.8.8.8`

### Raspberry Pi Static IP

Edit `/etc/dhcpcd.conf`:
```bash
sudo nano /etc/dhcpcd.conf
```

Add at the end:
```
interface eth0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1 8.8.8.8

# For WiFi, use wlan0 instead of eth0
interface wlan0
static ip_address=192.168.1.101/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1 8.8.8.8
```

Apply changes:
```bash
sudo systemctl restart dhcpcd
```

---

## 🔥 Firewall Configuration

### Windows Firewall

To allow incoming connections on port 8000:

1. Open **Windows Defender Firewall**
2. Click **Advanced settings**
3. Click **Inbound Rules** → **New Rule...**
4. Select **Port** → **Next**
5. Select **TCP**, enter `8000` → **Next**
6. Select **Allow the connection** → **Next**
7. Check appropriate networks (Domain, Private, Public) → **Next**
8. Name it "Barcode Verification System" → **Finish**

**PowerShell (run as Administrator):**
```powershell
New-NetFirewallRule -DisplayName "Barcode Verification System" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow
```

### Linux Firewall (UFW)

```bash
# Allow port 8000
sudo ufw allow 8000/tcp

# Verify
sudo ufw status
```

### Linux Firewall (iptables)

```bash
sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
sudo iptables-save | sudo tee /etc/iptables.rules
```

---

## 🏢 Enterprise Network Considerations

### VLAN Segmentation

If your production floor is on a separate VLAN:
1. Ensure the barcode verification device is on the production VLAN
2. Allow cross-VLAN traffic to port 8000 if monitors need access from office VLAN
3. Or place the device on a VLAN accessible from both areas

### Network Diagram Example

```
┌─────────────────────────────────────────────────────────────────┐
│                         PRODUCTION FLOOR                         │
│  ┌─────────────────┐    ┌─────────────────┐                      │
│  │ Barcode Scanner │    │ Touchscreen     │                      │
│  │  (USB to Pi)    │───▶│ Display         │                      │
│  └─────────────────┘    │ (Operator UI)   │                      │
│                         └────────┬────────┘                      │
│                                  │ USB                           │
│                         ┌────────▼────────┐                      │
│                         │ Raspberry Pi    │                      │
│                         │ 192.168.1.100   │                      │
│                         │ Port 8000       │                      │
│                         └────────┬────────┘                      │
└──────────────────────────────────│───────────────────────────────┘
                                   │ Ethernet
                          ┌────────▼────────┐
                          │ Network Switch  │
                          └────────┬────────┘
                                   │
         ┌─────────────────────────┼─────────────────────────┐
         │                         │                         │
┌────────▼────────┐    ┌───────────▼───────────┐    ┌───────▼───────┐
│ Office PC       │    │ Supervisor Tablet     │    │ Production    │
│ /monitor view   │    │ /monitor view         │    │ Dashboard     │
│ 192.168.1.50    │    │ 192.168.1.60          │    │ (Large Screen)│
└─────────────────┘    └───────────────────────┘    └───────────────┘
```

### DNS / Hostname Setup (Optional)

Instead of using IP addresses, you can set up a hostname:

**Windows (local hosts file):**
Edit `C:\Windows\System32\drivers\etc\hosts`:
```
192.168.1.100    barcode-line1
```

Now access via: `http://barcode-line1:8000`

**Linux:**
Edit `/etc/hosts`:
```
192.168.1.100    barcode-line1
```

---

## 🌐 Remote Access Options

### Option 1: VPN (Recommended for Security)

If IT needs to access remotely:
1. Connect to company VPN
2. Access device at its internal IP: `http://192.168.1.100:8000`

### Option 2: Reverse Proxy with HTTPS

For secure remote access without VPN:

**Using nginx (on the Pi or a separate server):**
```nginx
server {
    listen 443 ssl;
    server_name barcode.yourcompany.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Option 3: Cloudflare Tunnel (Zero Trust)

For more advanced setups, Cloudflare Tunnel can expose the service securely without opening firewall ports.

---

## 🔌 Network Troubleshooting

### Can't Access from Network

1. **Check if app is running:**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Check if listening on all interfaces:**
   The app should start with `--host 0.0.0.0` (not `127.0.0.1`)

3. **Check firewall:**
   ```bash
   # Windows
   netsh advfirewall firewall show rule name="Barcode Verification System"
   
   # Linux
   sudo ufw status
   ```

4. **Check network connectivity:**
   ```bash
   # From client machine, ping the server
   ping 192.168.1.100
   ```

5. **Check port is open:**
   ```bash
   # From client machine
   telnet 192.168.1.100 8000
   # or
   nc -zv 192.168.1.100 8000
   ```

### Slow Network Performance

1. **Check latency:**
   ```bash
   ping 192.168.1.100
   ```
   Should be <10ms on local network.

2. **Check bandwidth:**
   The application uses minimal bandwidth. If slow, check for network congestion.

3. **Use wired connection:**
   Ethernet is more reliable than WiFi in industrial environments with electrical noise.

### Connection Drops

1. **Check WiFi signal strength** (if using WiFi)
2. **Check for IP conflicts** (two devices with same IP)
3. **Check cable quality** (damaged Ethernet cables)
4. **Check switch/router logs** for errors

---

## 📊 Network Monitoring

### Check Active Connections

```bash
curl http://192.168.1.100:8000/health
```

Look for `sse_connections` in the response - shows how many devices are connected.

### Monitor Network Traffic

**Windows:**
```powershell
Get-NetTCPConnection -LocalPort 8000 | Select-Object LocalAddress, RemoteAddress, State
```

**Linux:**
```bash
ss -tuln | grep 8000
netstat -an | grep 8000
```

---

## 🏭 Multi-Line Deployment

When deploying to multiple production lines:

| Line | IP Address | Hostname | URL |
|------|------------|----------|-----|
| Line 1 | 192.168.1.100 | barcode-line1 | http://barcode-line1:8000 |
| Line 2 | 192.168.1.101 | barcode-line2 | http://barcode-line2:8000 |
| Line 3 | 192.168.1.102 | barcode-line3 | http://barcode-line3:8000 |

**Tip:** Set `LINE_NAME` environment variable on each device so the UI shows which line you're viewing.

---

## ✅ Network Checklist

Before deployment, verify:

- [ ] Device has static IP address
- [ ] Port 8000 is open in firewall
- [ ] Can access from operator touchscreen
- [ ] Can access from supervisor's desk
- [ ] Can access from any production dashboard
- [ ] Health endpoint responds: `curl http://<ip>:8000/health`
- [ ] DNS/hostname configured (optional but recommended)

---

*For more details on deployment, see [DEPLOYMENT.md](DEPLOYMENT.md) or [WINDOWS_SETUP.md](WINDOWS_SETUP.md)*
