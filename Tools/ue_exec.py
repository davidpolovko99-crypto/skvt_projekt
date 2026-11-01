"""Run Python code inside the running Unreal Editor via Python Remote Execution.

Usage:
    python Tools/ue_exec.py "import unreal; print(unreal.SystemLibrary.get_engine_version())"
    python Tools/ue_exec.py -f path/to/script.py
"""
import argparse
import sys
import time

sys.path.append(r"D:\UE_5.5\Engine\Plugins\Experimental\PythonScriptPlugin\Content\Python")
import remote_execution  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("code", nargs="?", help="Python code to execute")
    parser.add_argument("-f", "--file", help="Python file to execute")
    parser.add_argument("--timeout", type=float, default=5.0, help="Seconds to wait for an editor")
    args = parser.parse_args()

    if args.file:
        with open(args.file, encoding="utf-8") as f:
            code = f.read()
    elif args.code:
        code = args.code
    else:
        parser.error("pass code or --file")

    remote = remote_execution.RemoteExecution()
    remote.start()
    try:
        deadline = time.time() + args.timeout
        while not remote.remote_nodes and time.time() < deadline:
            time.sleep(0.1)
        if not remote.remote_nodes:
            print("No Unreal Editor found. Is it running with remote execution enabled?", file=sys.stderr)
            return 1

        remote.open_command_connection(remote.remote_nodes[0]["node_id"])
        result = remote.run_command(code, unattended=True, exec_mode=remote_execution.MODE_EXEC_FILE)
        for entry in result.get("output", []):
            print(entry["output"], end="" if entry["output"].endswith("\n") else "\n")
        if not result.get("success"):
            print(result.get("result", ""), file=sys.stderr)
            return 1
        return 0
    finally:
        remote.stop()


if __name__ == "__main__":
    sys.exit(main())
