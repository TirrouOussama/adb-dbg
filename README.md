# adb-dbg

A lightweight Android process debugger that automatically monitors an Android application's PID and reconnects Logcat whenever the process restarts.

## Features

- Automatically detects connected Android devices.
- Selects the device automatically when only one is connected.
- Supports explicit device selection when multiple devices are connected.
- Monitors Android application processes.
- Supports secondary Android processes (`PACKAGE:SERVICE`).
- Automatically reconnects Logcat when a process terminates or restarts.
- Detects unexpected Logcat termination and reconnects.
- Clean shutdown with Ctrl+C.

## Requirements

- Python 3.9+
- Android Debug Bridge (ADB)
- At least one authorized Android device connected through ADB.

ADB must be available in your system PATH.

## Installation

Clone the repository:

```bash
git clone https://github.com/TirrouOussama/adb-dbg.git
cd adb-dbg
```

## Usage

### Automatic device selection

```bash
adb-dbg PACKAGE
```

Example:

```bash
adb-dbg org.awfer.awferrides
```

### Secondary process

```bash
adb-dbg PACKAGE SERVICE
```

Example:

```bash
adb-dbg org.awfer.awferdriver tripd
```

### Explicit device selection

```bash
adb-dbg DEVICE PACKAGE [SERVICE]
```

Example:

```bash
adb-dbg RZCX31JLK1N org.awfer.awferdriver tripd
```

### Help

```bash
adb-dbg --help
```

## How it works

1. Detects authorized ADB devices.
2. Selects the target device.
3. Finds the Android process using `pidof`.
4. Attaches Logcat to the process PID.
5. Monitors the PID every 0.5 seconds.
6. Detects process termination or restart.
7. Reconnects Logcat using the new PID.
8. If the process is not running, waits until it becomes available.

## Controls

- `Ctrl+C`: Stop the debugger.

## License

MIT License. See [LICENSE](LICENSE).