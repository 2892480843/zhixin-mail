"""Render native pages using production logic plus scheduled fixture navigation.

Uses no real mailbox and no synthesized mouse/keyboard input. Each fixture runs
in its own storage jail, then quits. Screenshot evidence is explicitly demo data.
"""
import argparse
import json
import os
import pathlib
import shutil
import subprocess
import time
import urllib.request

APP = pathlib.Path(__file__).resolve().parents[1]
SCENES = {
    "01-inbox": ("", ["演示数据", "3 件事待确认", "第 2 次更新"]),
    "02-detail": ('open_detail("d1")', ["15:20", "回复草稿"]),
    "03-board": ("go_board()", ["橡树学校", "Sarah", "第 2 次更新 · 提案已按新来信调整"]),
    "04-complete": ('open_detail("d1") execute_proposal("d1", false)', ["演示完成 · 未发送", "演示回复（未发送）"]),
    "05-rules": ('open_detail("d2") add_rule_for("d2") go_rules()', ["准备草稿", "待宿主审阅"]),
    "06-rule-replay": ('open_detail("d2") add_rule_for("d2") load_demo()', ["规则已匹配 · 待审阅", "3 件事待确认"]),
    "07-original": ('open_detail("d1") show_original = true refresh_all()', ["邮件原文 ·", "补充通知", "15:20"]),
    "08-history": ('go_history()', ["发送记录", "暂无真实发送记录"]),
    "09-staged-initial": ('start_staged_demo() go_board()', ["演示阶段 1/3", "15:30"]),
    "10-staged-update": ('start_staged_demo() start_timeout(0.5, || { open_detail("d1") execute_proposal("d1", false) next_demo_notice() })', ["15:20", "第 2 次更新", "回复草稿"]),
    "11-welcome": ('demo_mode = false account = nil proposals = [] messages = [] status_text = "" glance_status = "" screen = "welcome" refresh_all()', ["把重要的安排", "放在心上", "知信不接触授权码"]),
    "12-calendar": ('open_detail("d1") execute_proposal("d1", false) go_calendar()', ["已经确认的安排", "15:20", "不代表写入系统日历"]),
    "13-empty-board": ('proposals = [] status_text = "" go_board()', ["安排都理清了", "有新的变化"]),
    "14-sync-error": ('demo_mode = false account = {id: "fixture" address: "test@example.com"} proposals = [] messages = [] status_text = "邮箱同步失败：网络连接中断" screen = "inbox" refresh_all()', ["邮箱同步失败", "暂时没有可显示的来信"]),
    "15-order": ('open_detail("d3")', ["物流追踪", "已送达", "JD1234567890"]),
    "16-read-failure": ('demo_mode = false account = {id: "fixture" address: "test@example.com"} proposals = [] messages = [{id: "missing" sender: "测试通知" subject: "待重试的来信" time: "12:00"}] busy = true screen = "inbox" fetch_and_analyze(0) refresh_all()', ["1 封未读取", "刷新重试", "待重试的来信"]),
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--hub", type=pathlib.Path, required=True)
    parser.add_argument("--card-host", type=pathlib.Path, required=True)
    parser.add_argument("--port", type=int, default=8144)
    parser.add_argument("--output", type=pathlib.Path, default=APP / "build/native-preview")
    parser.add_argument("--size", default="412x892")
    parser.add_argument("--scenes", nargs="+", choices=SCENES)
    args = parser.parse_args()
    hub, card_host = args.hub.resolve(), args.card_host.resolve()
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=True)
    base = f"http://127.0.0.1:{args.port}"
    source = (APP / "bundle/main.splash").read_text(encoding="utf-8")
    selected = {name: SCENES[name] for name in (args.scenes or SCENES)}
    for name, (navigation, expected) in selected.items():
        scene_size = "412x1600" if name == "07-original" else args.size
        fixture = root / name
        if fixture.exists():
            raise RuntimeError(f"Use a fresh output directory: {fixture}")
        bundle = fixture / "bundle"
        shutil.copytree(APP / "bundle", bundle)
        script = source.replace(
            "// ---------- 界面 ----------",
            f"start_timeout(0.8, || {{ {navigation} }})\n// ---------- 界面 ----------",
        )
        (bundle / "main.splash").write_text(script, encoding="utf-8")
        subprocess.run([str(hub), "stamp", str(bundle)], check=True, capture_output=True)
        env = dict(os.environ, MAKEPAD_REMOTE=str(args.port), MAKEPAD_HIDE_WINDOWS="1")
        log = fixture / "card-host.log"
        with log.open("w", encoding="utf-8") as stream:
            process = subprocess.Popen([
                str(card_host), "--bundle", str(bundle), "--allow-unsigned",
                "--app-data", str(fixture / "state"), "--size", scene_size,
            ], stdout=stream, stderr=subprocess.STDOUT, env=env)
            try:
                deadline = time.monotonic() + 25
                snapshot, text = {}, ""
                while True:
                    try:
                        with urllib.request.urlopen(base + "/snap", timeout=2) as response:
                            snapshot = json.load(response)
                        # Ignore Splash source text, which would produce false matches.
                        text = "\n".join(w.get("t", "") for w in snapshot["s"] if w["ty"] == "Label")
                        if all(value in text for value in expected):
                            break
                    except (OSError, ValueError):
                        pass
                    if process.poll() is not None or time.monotonic() > deadline:
                        (fixture / "failed-snapshot.json").write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
                        raise RuntimeError(f"{name} did not reach expected state: {expected}\nVisible labels: {text}\n{log.read_text()}")
                    time.sleep(0.1)
                (fixture / "snapshot.json").write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
                if name == "01-inbox":
                    connect = [w for w in snapshot["s"] if w["ty"] == "Button" and w.get("t") == "连接真实邮箱"]
                    if len(connect) != 1 or connect[0]["r"][3] < 36:
                        raise RuntimeError("Real mailbox connection entry is not fully visible in the demo inbox")
                if name in ("02-detail", "10-staged-update", "11-welcome"):
                    primary_label = "连接邮箱" if name == "11-welcome" else "演示确认（不发送）"
                    actions = [w for w in snapshot["s"] if w["ty"] == "Button" and w.get("t") == primary_label]
                    if len(actions) != 1:
                        raise RuntimeError(f"Missing primary action in {name}")
                    x, y, width, height = actions[0]["r"]
                    window_width, window_height = map(int, args.size.split("x"))
                    # Remote widget bounds are clipped to the viewport; a 26px
                    # visible fragment does not prove the 46px action fits.
                    if height < 46 or x < 0 or y < 0 or x + width > window_width or y + 46 > window_height:
                        raise RuntimeError(f"Primary action is outside {args.size}: {actions[0]}")
                with urllib.request.urlopen(base + "/g?raw=1", timeout=15) as response:
                    (root / f"{name}.png").write_bytes(response.read())
                errors = log.read_text(encoding="utf-8")
                if "[E]" in errors or '"level":"error"' in errors or "callback error" in errors:
                    raise RuntimeError(errors)
                print(f"PASS native {name}")
            finally:
                try:
                    urllib.request.urlopen(base + "/quit", timeout=3).close()
                except OSError:
                    pass
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.terminate()
                    process.wait(timeout=5)
    print(f"{len(selected)}/{len(selected)} native demo pages passed")


if __name__ == "__main__":
    main()
