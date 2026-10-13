"""Run production Splash logic in the pinned interpreter with host/FS/UI boundaries mocked.

No mailbox is accessed and no mail is sent. The real native host needs separate acceptance.
Usage: python3 tests/test_send_flow.py --deps ../../octosense-ws/OctoSense-App-Hub/target/release/deps
"""
import argparse
import pathlib
import subprocess
import sys

APP = pathlib.Path(__file__).resolve().parents[1]
MOCKS = '''
use mod.std.assert
let requests = []
let writes = []
let files = {}
let fs = {
    write: fn(path, data) { writes.push({path: path data: data}) files[path] = data }
    exists: fn(path) { for key value in files { if ("" + key) == path { return true } } return false }
    read: fn(path) { for key value in files { if ("" + key) == path { return value } } return "" }
}
let host = {request: fn(method, args, cb) { requests.push({method: method args: args cb: cb}) }}
let start_timeout = fn(delay, cb) { cb() }
'''
SETUP = '''
account = {id: "test-account" address: "me@example.com"}
let e = demo_raws()[0]
let p = upsert_proposal(e, demo_analyze(e))
current_pid = p.id
edit_draft = "Edited reply"
requests = []
'''
CASES = {
    'self_test_uses_current_account_and_native_review': '''
check_mail_send()
assert(requests.len() == 1 && requests[0].method == "mail.review_send")
assert(requests[0].args.to == account.address && requests[0].args.subject == "知信邮箱连通性测试")
assert(p.status == "pending")
true
''',
    'self_test_cancel_does_not_add_history': '''
check_mail_send()
requests[0].cb({is_ok: false data: nil error: "cancelled"})
assert(sent_replies.len() == 0 && reviewing_pid == "")
assert(contains(connection_send_status, "取消"))
true
''',
    'self_test_acceptance_does_not_claim_delivery_or_finish_proposals': '''
check_mail_send()
requests[0].cb({is_ok: true data: {accepted: true id: "test-receipt"} error: ""})
assert(sent_replies.len() == 1 && sent_replies[0].reply_to == account.address)
assert(p.status == "pending" && events.len() == 0)
assert(contains(connection_send_status, "接受") && contains(connection_send_status, "核对是否收到"))
true
''',
    'self_test_is_blocked_during_sync_review_or_demo': '''
busy = true check_mail_send() busy = false
reviewing_pid = p.id check_mail_send() reviewing_pid = ""
demo_mode = true check_mail_send()
assert(requests.len() == 0)
true
''',
    'model_connection_check_uses_fixed_non_mail_input': '''
check_model_connection()
assert(requests.len() == 1 && requests[0].method == "model.complete")
assert(requests[0].args.input == "connection-check")
requests[0].cb({is_ok: true data: {output: {ready: true}} error: ""})
assert(contains(connection_model_status, "已响应"))
true
''',
    'model_check_failure_is_visible_and_allows_deliberate_retry': '''
check_model_connection()
check_model_connection()
assert(requests.len() == 1)
requests[0].cb({is_ok: false data: nil error: "Missing API key"})
assert(contains(connection_model_status, "未就绪"))
check_model_connection()
assert(requests.len() == 2)
true
''',
    "manual_send_requests_native_review_with_edited_body": '''
execute_proposal(p.id, false)
assert(requests.len() == 1)
assert(requests[0].method == "mail.review_send")
assert(requests[0].args.body == "Edited reply")
assert(p.status == "pending")
true
''',
    "success_without_acceptance_does_not_complete": '''
execute_proposal(p.id, false)
requests[0].cb({is_ok: true data: {accepted: false} error: ""})
assert(p.status == "pending")
assert(events.len() == 0)
true
''',
    "cancellation_keeps_proposal_pending": '''
execute_proposal(p.id, false)
requests[0].cb({is_ok: false data: nil error: "Review cancelled; nothing was sent"})
assert(p.status == "pending")
assert(events.len() == 0)
true
''',
    "one_review_at_a_time": '''
execute_proposal(p.id, false)
execute_proposal(p.id, false)
assert(requests.len() == 1)
true
''',
    "rule_match_never_requests_background_send": '''
rules.push({address: p.address kind: p.kind sender: p.sender})
after_analysis(e, demo_analyze(e))
for r in requests { assert(r.method != "mail.send" && r.method != "mail.review_send") }
assert(p.status == "pending")
true
''',
    "accepted_reply_updates_schedule_and_desktop_card": '''
execute_proposal(p.id, false)
requests[0].cb({is_ok: true data: {accepted: true} error: ""})
assert(p.status == "done")
assert(p.draft == "Edited reply")
assert(events.len() == 1)
assert(requests.len() == 2)
assert(requests[1].method == "glance.withdraw")
true
''',
    "late_receipt_does_not_complete_newer_proposal": '''
execute_proposal(p.id, false)
p.versions = p.versions + 1
p.draft = "Newer reply"
requests[0].cb({is_ok: true data: {accepted: true} error: ""})
assert(p.status == "pending")
assert(p.draft == "Newer reply")
assert(events.len() == 0)
true
''',
    "missing_acceptance_is_not_success": '''
execute_proposal(p.id, false)
requests[0].cb({is_ok: true data: {} error: ""})
assert(p.status == "pending")
assert(events.len() == 0)
true
''',
    "json_receipt_marks_accepted_only_once": '''
execute_proposal(p.id, false)
requests[0].cb({is_ok: true data: "{\\"accepted\\":true,\\"status\\":\\"accepted\\"}".parse_json() error: ""})
assert(p.status == "done")
execute_proposal(p.id, false)
assert(requests.len() == 2)
true
''',
    "empty_edited_body_is_not_replaced_by_old_draft": '''
edit_draft = ""
execute_proposal(p.id, false)
assert(requests.len() == 0)
assert(p.status == "pending")
true
''',
    "cancel_allows_a_deliberate_retry_and_keeps_edit": '''
execute_proposal(p.id, false)
requests[0].cb({is_ok: false data: nil error: "Review cancelled; nothing was sent"})
assert(p.draft == "Edited reply")
execute_proposal(p.id, false)
assert(requests.len() == 3)
assert(requests[2].method == "mail.review_send")
true
''',
    "desktop_card_keeps_required_fields_and_reports_failure": '''
publish_glance()
assert(requests[0].method == "glance.publish")
assert(requests[0].args.card_id == "zhixin-pending")
assert(requests[0].args.title != "")
assert(requests[0].args.script != "")
requests[0].cb({is_ok: false data: nil error: "no glance service"})
assert(glance_status != "")
true
''',
    "demo_completion_never_claims_real_sending": '''
demo_mode = true
execute_proposal(p.id, false)
assert(p.status == "done")
assert(status_label(p) == "演示完成 · 未发送")
for r in requests { assert(r.method != "mail.send" && r.method != "mail.review_send") }
true
''',
    "demo_refresh_does_not_duplicate_messages": '''
load_demo()
assert(messages.len() == 6)
load_demo()
assert(messages.len() == 6)
assert(pending_count() == 3)
true
''',
}


def main(cases=CASES):
    parser = argparse.ArgumentParser()
    parser.add_argument("--deps", type=pathlib.Path, required=True)
    args = parser.parse_args()
    deps = args.deps.resolve()
    libraries = list(deps.glob("libmakepad_script-*.rlib"))
    if len(libraries) != 1:
        parser.error("Expected one pinned libmakepad_script rlib; build the documented card-host first")
    out = APP / "build" / "send-regression"
    out.mkdir(parents=True, exist_ok=True)
    runner = out / "splash-runner"
    subprocess.run([
        "rustc", "--edition=2021", str(APP / "tests/splash_runner.rs"),
        "--extern", f"makepad_script={libraries[0]}", "-L", f"dependency={deps}",
        "-o", str(runner),
    ], check=True)
    source = (APP / "bundle/main.splash").read_text(encoding="utf-8")
    core = source.split("// ---------- 启动 ----------")[0]
    start = core.index("fn refresh_all()")
    end = core.index("fn open_detail(", start)
    core = core[:start] + "fn refresh_all() {}\n" + core[end:]
    failures = 0
    for name, case in cases.items():
        script = out / f"{name}.splash"
        script.write_text(MOCKS + core + SETUP + case, encoding="utf-8")
        result = subprocess.run([str(runner), str(script)], capture_output=True, text=True)
        output = result.stdout + result.stderr
        # Splash may recover after an assertion error; the VM log is part of the verdict.
        failed = result.returncode != 0 or "[E]" in output or '"level":"error"' in output
        failures += failed
        print(f"{'FAIL' if failed else 'PASS'} {name}")
        if failed:
            print(output.strip())
    print(f"{len(cases) - failures}/{len(cases)} passed")
    return bool(failures)


if __name__ == "__main__":
    sys.exit(main())
