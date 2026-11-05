
"""Android process debugger with automatic PID reconnection."""

import argparse
import shutil
import subprocess
import sys
import time


def get_devices(adb):
    """Return authorized ADB device serials."""

    result = subprocess.run(
        [adb, "devices"],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError("Unable to retrieve ADB devices.")

    devices = []

    for line in result.stdout.splitlines()[1:]:
        fields = line.split()

        if len(fields) >= 2 and fields[1] == "device":
            devices.append(fields[0])

    return devices


def get_process_pid(adb, device, process):
    """Return the first PID belonging to the Android process."""

    result = subprocess.run(
        [adb, "-s", device, "shell", "pidof", process],
        capture_output=True,
        text=True,
    )

    output = result.stdout.strip().replace("\r", "")

    if not output:
        return None

    return output.split()[0]


def stop_logcat(logcat):
    """Stop the current logcat subprocess."""

    if logcat is None or logcat.poll() is not None:
        return

    logcat.terminate()

    try:
        logcat.wait(timeout=2)
    except subprocess.TimeoutExpired:
        logcat.kill()
        logcat.wait()


def build_parser():
    parser = argparse.ArgumentParser(
        prog="adb-dbg",
        description=(
            "Monitor an Android process and automatically reconnect "
            "logcat when its PID changes."
        ),
        usage=(
            "adb-dbg [-h] PACKAGE [SERVICE]\n"
            "       adb-dbg [-h] DEVICE PACKAGE [SERVICE]"
        ),
        epilog=(
            "Examples:\n"
            "  adb-dbg org.awfer.awferrides\n"
            "  adb-dbg org.awfer.awferdriver tripd\n"
            "  adb-dbg DEVICE_SERIAL com.example.anyapp\n"
            "  adb-dbg DEVICE_SERIAL com.example.anyapp service"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "arguments",
        nargs="*",
        metavar="ARG",
    )

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    arguments = args.arguments

    if not arguments:
        parser.error("Missing application package.")

    if len(arguments) > 3:
        parser.error("Too many arguments.")

    adb = shutil.which("adb")

    if adb is None:
        print(
            "ERROR: ADB is not installed or not in PATH.",
            file=sys.stderr,
        )
        return 1

    try:
        devices = get_devices(adb)
    except (OSError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if not devices:
        print(
            "ERROR: No connected or authorized ADB devices.",
            file=sys.stderr,
        )
        return 1

    device = None
    package = None
    service = ""

    # Explicit device selection.
    if arguments[0] in devices:
        if len(arguments) < 2:
            parser.error("Missing application package after device serial.")

        device = arguments[0]
        package = arguments[1]
        service = arguments[2] if len(arguments) == 3 else ""

    else:
        if len(devices) > 1:
            print(
                "ERROR: Multiple ADB devices connected.",
                file=sys.stderr,
            )
            print("\nSpecify a device:", file=sys.stderr)

            for serial in devices:
                print(f"  {serial}", file=sys.stderr)

            print(
                f"\nExample:\n  adb-dbg {devices[0]} "
                f"{arguments[0]}",
                file=sys.stderr,
            )
            return 1

        if len(arguments) == 3:
            parser.error(
                "Invalid device serial. "
                "Use DEVICE PACKAGE [SERVICE]."
            )

        device = devices[0]
        package = arguments[0]
        service = arguments[1] if len(arguments) == 2 else ""

    process = f"{package}:{service}" if service else package

    print("======================================")
    print("       ANDROID PROCESS DEBUGGER")
    print("======================================")
    print(f"Device:  {device}")
    print(f"Package: {package}")
    print(f"Process: {process}")
    print("======================================")

    logcat = None

    try:
        while True:
            try:
                pid = get_process_pid(adb, device, process)
            except OSError as exc:
                print(f"ADB error: {exc}", file=sys.stderr)
                time.sleep(1)
                continue

            if not pid:
                print(
                    f"[{time.strftime('%H:%M:%S')}] "
                    f"Waiting for {process}...",
                    flush=True,
                )
                time.sleep(1)
                continue

            print()
            print(f"[{time.strftime('%H:%M:%S')}] ATTACHED")
            print(f"Process: {process}")
            print(f"PID:     {pid}")
            print("--------------------------------------", flush=True)

            try:
                logcat = subprocess.Popen(
                    [
                        adb,
                        "-s",
                        device,
                        "logcat",
                        "-v",
                        "threadtime",
                        f"--pid={pid}",
                    ]
                )
            except OSError as exc:
                print(f"ERROR: Unable to start logcat: {exc}")
                time.sleep(1)
                continue

            while True:
                time.sleep(0.5)

                try:
                    current_pid = get_process_pid(
                        adb,
                        device,
                        process,
                    )
                except OSError:
                    current_pid = None

                if current_pid != pid:
                    print()
                    print(
                        f"[{time.strftime('%H:%M:%S')}] "
                        "PROCESS CHANGED"
                    )
                    print(f"Old PID: {pid}")
                    print(f"New PID: {current_pid or 'DEAD'}")
                    print("Reconnecting...")
                    break

                if logcat.poll() is not None:
                    print("Logcat exited. Reconnecting...")
                    break

            stop_logcat(logcat)
            logcat = None

    except KeyboardInterrupt:
        print("\nDebugger stopped.")

    finally:
        stop_logcat(logcat)

    return 0


if __name__ == "__main__":
    sys.exit(main())
