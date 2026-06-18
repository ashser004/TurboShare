# TurboShare

High-speed, secure, and reliable local peer-to-peer file sharing application.

TurboShare lets you transfer files locally between your Windows PC and mobile devices instantly without using internet data.
The application focuses on **low latency**, **high speed**, and **zero friction** (browser-based receiving).

---

## Features

* **Zero-Install Client:** The receiver (mobile device) does not need to install any app—just scan the QR code and use any modern browser.
* **Double Verification Check:** Secure transient 6-digit PIN and manual confirm/reject handshake controls.
* **Safe Transfer Bypass:** Optional setting to skip PIN checks and manual verifications in secure networks.
* **Real-time Stats:** Server-sent live transfer progress, elapsed duration, speed metrics, and ETA.
* **Dynamic IP Locking:** Locks credentials to the receiver's IP address to prevent middleman hijacking.
* **Multi-file Chunked Streaming:** Streams files in 2MB blocks with MD5 integrity validation.
* **Session Logs & Viewer:** Persistent session-level log manager and interactive monospaced viewer.
* **Modern Premium Styling:** Curated harmonious dark themes, micro-animations, and animated success overlays.

---

## How It Works

TurboShare does **not upload your files to the internet or cloud**.

Instead:

1. The sender (PC) acts as a local HTTP and SSE (Server-Sent Events) server.
2. The receiver (phone) connects directly to the PC over the local area network.
3. Files are chunked and streamed directly over the connection.

This means:

* No internet data usage
* Maximize bandwidth utilization of your local Wi-Fi or hotspot
* Secure, private, and fully offline-capable

---

## Installation

### Option 1 – Install Setup (Recommended)

1. Download the latest `TurboShare_Setup.exe` from the **Releases** section of this repository.
2. Run the installer on your Windows PC.
3. Follow the wizard steps to complete the installation.

---

### Option 2 – Build From Source

Requirements:

* Python 3.11+
* PySide6 & aiohttp (pip dependencies)

Steps:

```bash
# Clone the repository
git clone https://github.com/ashser004/TurboShare.git
cd TurboShare

# Install dependencies
pip install -r requirements.txt
```

Run the application:

```bash
python -m src.main
```

---

## Usage Guide

### 1. Choose Transfer Mode

Open the app on your PC and choose:
* **Send**: Share files from your PC to a phone.
* **Receive**: Download files from a phone to your PC's Downloads directory.

---

### 2. Connect the Device

The PC will generate a **QR code** and a local **session URL**.
Scan the QR code or type the URL into your phone's web browser (make sure both devices are on the same Wi-Fi network).

---

### 3. Verify Credentials

If **Safe Transfer** is enabled:
1. Enter the 6-digit PIN displayed on your PC into the phone's web browser.
2. Tap **Confirm** on the phone.

---

### 4. Verify & Approve Handshake

The PC will display the connecting device info (Browser, OS, and local IP address).
Verify the credentials and click **Confirm Send** (or **Confirm Receive**).

---

### 5. Transfer Files

* **Send Mode:** The phone browser automatically downloads the files queue to your phone's Downloads directory.
* **Receive Mode:** Tap to select files on your phone browser, type the PIN, and click send. Files are streamed and assembled directly in the PC's Downloads folder.

---

## Data Usage & Privacy

TurboShare operates completely offline within your local network. No external servers are involved, and files are never streamed over the internet.

---

## Device Requirements & Media Support

* **PC:** Modern PC running **Windows 10 or Windows 11**.
* **Mobile:** Any smartphone or tablet running a modern web browser (Chrome, Safari, Firefox, Edge, etc.) connected to the same local network or Wi-Fi hotspot.

---

## Future Roadmap

TurboShare is actively evolving. The following improvements are planned for upcoming releases:

### Planned Features

* **Cross-platform Desktop Clients**
  Support for macOS and Linux native applications.

* **Multi-device Transfers**
  Allowing a single PC to send files to multiple mobile clients simultaneously.

* **Wi-Fi Direct Support**
  Direct device-to-device sharing without requiring an active access point or router.

---

## Contributing

Contributions are welcome.

You can:
* Report bugs or issues
* Suggest improvements or design patterns
* Submit pull requests

Please ensure your changes follow the existing project structure and linting requirements.

---

## License

TurboShare is licensed under the **MIT License**.

See the LICENSE file for full terms.

© 2026 Ashmith
