# Hardware Shopping List

Estimated total: **$250–$450** depending on options chosen.

---

## Core Components (Required)

| Item | Description | Est. Price | Notes |
|------|-------------|------------|-------|
| Raspberry Pi 4 Model B (2GB) | Main controller | $45–55 | 2GB is sufficient; 4GB if running other apps |
| MicroSD Card (32GB) | Boot drive | $8–12 | Get Class 10 / A1 rated for reliability |
| Raspberry Pi Power Supply | Official 5V 3A USB-C | $12–15 | Don't cheap out—poor power causes crashes |
| 7" Touchscreen Display | Operator interface | $55–75 | Official Pi display or HDMI alternative |
| USB Barcode Scanner | Reads labels | $25–80 | See scanner recommendations below |
| Case/Enclosure | Protects Pi + display | $15–30 | Get one that fits both Pi and screen |

**Subtotal (Core): ~$160–265**

---

## GPIO / Alarm Components (Optional but Recommended)

| Item | Description | Est. Price | Notes |
|------|-------------|------------|-------|
| 4-Channel Relay Module | Controls alarm/lights | $8–12 | 5V relay board, opto-isolated preferred |
| 12V Alarm Buzzer/Horn | Audible fail alert | $8–15 | Get 100+ dB for noisy warehouse |
| LED Tower Light (Red/Green) | Visual pass/fail indicator | $20–35 | 24V industrial stack light |
| 12V/24V Power Supply | Powers buzzer and lights | $10–15 | Match voltage to your buzzer/lights |
| Jumper Wires (F-F) | Connect Pi to relay | $5–8 | 40-pin ribbon or individual Dupont wires |
| Terminal Block Connectors | Clean wiring connections | $5–10 | Optional but makes wiring cleaner |

**Subtotal (GPIO): ~$55–95**

---

## Mounting & Installation

| Item | Description | Est. Price | Notes |
|------|-------------|------------|-------|
| Adjustable Monitor Arm/Mount | Position display for operator | $15–30 | VESA mount or RAM mount style |
| Scanner Mounting Bracket | Fixed position scanning | $10–20 | Or use gooseneck/magnetic mount |
| DIN Rail + Enclosure | Industrial mounting for relay/PSU | $15–25 | Optional for cleaner install |
| Cable Management | Wire conduit, zip ties | $5–10 | Keep wires tidy and protected |

**Subtotal (Mounting): ~$45–85**

---

## Barcode Scanner Recommendations

| Model | Type | Price | Best For |
|-------|------|-------|----------|
| **Netum NT-1228** | Handheld USB | $25–35 | Budget option, good for testing |
| **Symcode MJ-2090** | Handheld USB | $30–40 | Reliable, fast decode |
| **Netum NT-2012** | Fixed mount USB | $45–60 | Hands-free fixed scanning |
| **Honeywell Voyager 1200g** | Handheld USB | $80–120 | Industrial grade, very durable |
| **Zebra DS2208** | Handheld USB | $100–150 | Premium, reads damaged barcodes well |

> **Tip:** Any scanner that works in "keyboard wedge" mode (types barcode + Enter) will work. Most USB scanners do this by default.

---

## Optional Upgrades

| Item | Description | Est. Price | Why You Might Want It |
|------|-------------|------------|----------------------|
| Raspberry Pi 4 (4GB) | More RAM | $55–65 | If running database or web server locally |
| UPS/Battery Backup | Power protection | $30–50 | Prevents data loss on power blips |
| USB WiFi Dongle | Backup connectivity | $10–15 | If built-in WiFi is unreliable |
| Ethernet Cable (Cat6) | Wired network | $5–10 | More reliable than WiFi in warehouses |
| Keyboard + Mouse | For setup/troubleshooting | $15–25 | Wireless combo kit |
| Industrial Enclosure (IP65) | Dust/water protection | $40–80 | For harsh environments |
| Second Display | Remote monitoring | $50–100 | Mount at end of line or supervisor desk |

---

## Sample Configurations

### Budget Build (~$250)

| Component | Choice | Price |
|-----------|--------|-------|
| Raspberry Pi 4 (2GB) | Standard | $45 |
| 32GB MicroSD | SanDisk | $10 |
| Power Supply | Official | $12 |
| 7" Touchscreen | Generic HDMI | $55 |
| USB Scanner | Netum NT-1228 | $30 |
| Relay Module | 4-channel | $10 |
| Buzzer | 12V piezo | $8 |
| 12V Power Supply | Wall adapter | $10 |
| Jumper Wires | Pack of 40 | $6 |
| Basic Case | 3D printed or acrylic | $15 |
| Misc (cables, mounts) | — | $20 |
| **Total** | | **~$221** |

### Production Build (~$400)

| Component | Choice | Price |
|-----------|--------|-------|
| Raspberry Pi 4 (4GB) | More headroom | $55 |
| 64GB MicroSD (A2) | Faster, more storage | $15 |
| Power Supply | Official | $12 |
| 7" Touchscreen | Official Pi display | $70 |
| USB Scanner | Honeywell 1200g | $90 |
| Relay Module | 4-channel opto-isolated | $12 |
| LED Stack Light | Red/Green 24V | $30 |
| 24V Power Supply | DIN rail mount | $15 |
| Industrial Enclosure | Wall-mount box | $35 |
| Mounting Hardware | RAM mount + brackets | $30 |
| Jumper/Wiring | Quality cables | $15 |
| **Total** | | **~$379** |

---

## Where to Buy

| Vendor | Best For | Link |
|--------|----------|------|
| Amazon | Quick shipping, everything | amazon.com |
| Adafruit | Quality Pi accessories | adafruit.com |
| SparkFun | Electronic components | sparkfun.com |
| Digi-Key | Industrial components | digikey.com |
| AliExpress | Budget options (slow shipping) | aliexpress.com |
| Micro Center | In-store pickup (US) | microcenter.com |

---

## Network Requirements (New in v3.0)

Since this is now a web-based system, you'll want:

| Requirement | Reason |
|-------------|--------|
| WiFi or Ethernet | Pi needs network for remote monitoring |
| Static IP (recommended) | So monitor URLs don't change |
| Port 5000 open | Default web server port |

To set a static IP on the Pi, edit `/etc/dhcpcd.conf`:

```
interface wlan0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1 8.8.8.8
```

---

## Quick Start Checklist

- [ ] Raspberry Pi 4 + power supply + SD card
- [ ] Display (touchscreen recommended)
- [ ] USB barcode scanner
- [ ] Network connection (WiFi or Ethernet)
- [ ] Relay module (if using alarms)
- [ ] Buzzer or stack light
- [ ] Power supply for buzzer/lights
- [ ] Jumper wires
- [ ] Mounting hardware

---

*Prices estimated as of 2024. Actual prices may vary.*
