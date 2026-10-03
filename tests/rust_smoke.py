#!/usr/bin/env python3
"""
PLAN-039 T-05：Rust 编译轨冒烟 + 难度切换动态 cols 实证（AC-03/D4）。

Drives the COMPILED exe (rust-workspace/target/debug/minesweeper.exe,
`auto build -r rust` product) via its AutoUI MCP channel:

  T1 structure: info bar + three difficulty buttons + 81-cell grid (9×9).
  T2 dynamic cols (D4): press 中级 16×16 → board 256 cells / cols:16;
     press 高级 30×16 → board 480 cells / cols:30; back to 初级 → 81/9.
     `cols: .store.cols` runs through the PLAN-039 D4 runtime-eval arm
     (rust.rs grid arm) — this is the compiled-track proof the VM suite
     cannot provide.
  T3 reset: face button returns board to 81 covered cells.

Usage:
    cd apps/038-minesweeper/tests
    python rust_smoke.py    # builds nothing; expects the exe present

Prerequisites: `auto build -r rust` run (see pac desktop_exe), python requests.
"""

import os
import re
import subprocess
import sys
import time

import requests

APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXE = os.path.join(APP_ROOT, "rust-workspace", "target", "debug", "minesweeper.exe")
MCP_PORT = int(os.environ.get("RUST_SMOKE_MCP_PORT", "9371"))


class Mcp:
    def __init__(self, url):
        self.url = url
        self.req_id = 0

    def call(self, tool, **args):
        self.req_id += 1
        r = requests.post(self.url, json={
            "jsonrpc": "2.0", "method": "tools/call",
            "params": {"name": tool, "arguments": args},
            "id": self.req_id,
        }, timeout=15)
        r.raise_for_status()
        data = r.json()
        if "error" in data:
            raise RuntimeError(f"MCP error: {data['error']}")
        content = data.get("result", {}).get("content", [])
        return content[0]["text"] if content else ""

    def snapshot(self):
        return self.call("autoui_snapshot")

    def state(self, *fields):
        return self.call("autoui_state", fields=list(fields))

    def click(self, element_id):
        return self.call("autoui_action", element_id=element_id, action="press")


def find_buttons_by_label(snap, label):
    """All `button #id "<label>"` ids in document order (rendered-vtree
    snapshot format — same locator as desktop_mcp.py)."""
    pat = re.compile(r'button\s+#(aura_\d+|vnode_\d+)\s+"' + re.escape(label) + '"')
    return pat.findall(snap)


def covered_cells(snap):
    return find_buttons_by_label(snap, "　")


class Checks:
    def __init__(self):
        self.fails = 0

    def check(self, name, ok, detail=""):
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
        if not ok:
            self.fails += 1
            print(f"       {detail[:200]}")


def main():
    if not os.path.isfile(EXE):
        print(f"exe not found: {EXE} — run `auto build -r rust` first")
        return 2
    env = dict(os.environ, AUTOUI_MCP_PORT=str(MCP_PORT))
    proc = subprocess.Popen([EXE], cwd=APP_ROOT, env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    url = f"http://127.0.0.1:{MCP_PORT}/mcp"
    try:
        for _ in range(60):
            try:
                requests.post(url, json={
                    "jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 1
                }, timeout=2)
                break
            except requests.RequestException:
                if proc.poll() is not None:
                    print("exe died during startup")
                    return 2
                time.sleep(0.5)
        mcp = Mcp(url)
        # Wait for first render (iced window up + view materialized).
        snap = ""
        for _ in range(30):
            time.sleep(1)
            try:
                snap = mcp.snapshot()
                if "初级" in snap or "aura_" in snap:
                    break
            except (requests.RequestException, RuntimeError):
                pass
        c = Checks()

        print("\nT1: compiled structure")
        snap = mcp.snapshot()
        c.check("difficulty buttons", all(l in snap for l in ("初级 9×9", "中级 16×16", "高级 30×16")), snap[:120])
        c.check("81 covered cells (9×9)", len(covered_cells(snap)) == 81, f"got {len(covered_cells(snap))}")

        print("\nT2: difficulty switch — D4 dynamic cols (compiled track)")
        for label, cols, rows in (("中级 16×16", 16, 16), ("高级 30×16", 30, 16), ("初级 9×9", 9, 9)):
            ids = find_buttons_by_label(mcp.snapshot(), label)
            c.check(f"{label} button bound", bool(ids), "missing")
            if ids:
                mcp.click(ids[0])
                time.sleep(0.4)
                snap = mcp.snapshot()
                st = mcp.state("cols", "rows")
                expect_cells = cols * rows
                got = len(covered_cells(snap))
                c.check(f"cols {cols} in state", f"cols: {cols}" in st, st)
                c.check(f"board {expect_cells} cells", got == expect_cells, f"got {got}")

        print("\nT3: reset returns to covered board")
        face = find_buttons_by_label(mcp.snapshot(), "🙂") or find_buttons_by_label(mcp.snapshot(), "😵")
        c.check("face reset button bound", bool(face), "missing")
        if face:
            mcp.click(face[0])
            time.sleep(0.3)
            snap = mcp.snapshot()
            c.check("81 covered after reset", len(covered_cells(snap)) == 81, f"got {len(covered_cells(snap))}")

        print(f"\n==== {('FAIL' if c.fails else 'PASS')}: {c.fails} failure(s) ====")
        return 1 if c.fails else 0
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    sys.exit(main())
