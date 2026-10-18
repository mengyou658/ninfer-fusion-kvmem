#!/usr/bin/env python3
import sys
import paramiko

HOST = "192.168.1.5"
USER = "yun"
PASSWORD = "admin"


def connect():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(
        HOST,
        username=USER,
        password=PASSWORD,
        timeout=20,
        allow_agent=False,
        look_for_keys=False,
    )
    return client


def sftp_put(local, remote, mode=0o755):
    t = paramiko.Transport((HOST, 22))
    t.connect(username=USER, password=PASSWORD)
    sftp = paramiko.SFTPClient.from_transport(t)
    sftp.put(local, remote)
    sftp.chmod(remote, mode)
    sftp.close()
    t.close()


def _exec(cmd, timeout=300, as_root=False):
    client = connect()
    if as_root:
        cmd = "echo admin | su -c %s root" % repr(cmd)
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", "replace")
    err = stderr.read().decode("utf-8", "replace")
    code = stdout.channel.recv_exit_status()
    client.close()
    sys.stdout.buffer.write(out.encode("utf-8", "replace"))
    if err:
        sys.stderr.buffer.write(err.encode("utf-8", "replace"))
    return code


def root(cmd, timeout=300):
    return _exec(cmd, timeout=timeout, as_root=True)


def run(cmd, timeout=300):
    return _exec(cmd, timeout=timeout, as_root=False)


if __name__ == "__main__":
    action = sys.argv[1]
    if action == "put":
        sftp_put(sys.argv[2], sys.argv[3])
        print("put", sys.argv[2], "->", sys.argv[3])
    elif action in ("root", "run"):
        timeout = 300
        args = sys.argv[2:]
        if args and args[0].startswith("--timeout="):
            timeout = int(args[0].split("=", 1)[1])
            args = args[1:]
        fn = root if action == "root" else run
        raise SystemExit(fn(" ".join(args), timeout=timeout))
    elif action == "build":
        cmd = (
            "nohup bash /tmp/ninfer-build.sh "
            ">/f/ninfer-fusion-kvmem/build-120a-nohup.out 2>&1 </dev/null "
            "& echo PID:$!"
        )
        raise SystemExit(root(cmd, timeout=30))
    elif action == "status":
        cmd = (
            "echo '--- pids ---'; "
            "pgrep -c -f 'cmake --build build-120a' || true; "
            "pgrep -c nvcc || true; "
            "echo '--- last progress ---'; "
            "grep -E '\\[[0-9]+/727\\]' /f/ninfer-fusion-kvmem/build-120a.log | tail -n 8; "
            "echo '--- failed ---'; "
            "grep -E 'error:|ninja: build stopped|FAILED:' /f/ninfer-fusion-kvmem/build-120a.log | tail -n 5 || true; "
            "echo '--- end marker ---'; "
            "tail -n 5 /f/ninfer-fusion-kvmem/build-120a-nohup.out 2>/dev/null || true; "
            "grep -E 'build end|error:' /f/ninfer-fusion-kvmem/build-120a.log | tail -n 3 || true; "
            "echo '--- binary ---'; "
            "ls -lh /f/ninfer-fusion-kvmem/src-tree/fusion-engine-src/build-120a/apps/ninfer-serve 2>/dev/null || echo not-built-yet"
        )
        raise SystemExit(root(cmd, timeout=30))
    else:
        raise SystemExit("unknown action")
