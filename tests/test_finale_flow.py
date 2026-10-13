"""Regression cases for model evidence, account isolation and presentation workflow."""
import sys
from test_send_flow import main

CASES = {
    "failed_message_read_is_visible_and_keeps_existing_proposals": '''
messages = [{id: "unread-message"}]
busy = true
fetch_and_analyze(0)
requests[0].cb({is_ok: false data: nil error: "Connection dropped"})
assert(busy == false && proposals.len() == 1 && p.status == "pending")
assert(contains(status_text, "1 封未读取"))
assert(contains(status_text, "刷新重试"))
true
''',
    "next_sync_clears_previous_partial_read_warning": '''
messages = [{id: "unread-message"}]
busy = true
fetch_and_analyze(0)
requests[0].cb({is_ok: false data: nil error: "Connection dropped"})
requests = []
sync_inbox()
requests[0].cb({is_ok: true data: {new: 0 total: 0} error: ""})
requests[1].cb({is_ok: true data: {messages: [] total: 0 folder: "INBOX"} error: ""})
assert(busy == false && !contains(status_text, "未读取"))
assert(p.status == "pending")
true
''',
    "account_switch_saves_old_edited_draft_in_old_account_file": '''
screen = "detail"
edit_draft = "Saved before account switch"
let previous_path = state_path()
add_account()
requests[0].cb({is_ok: true data: {id: "second-account" address: "second@example.com"} error: ""})
assert(files[previous_path].parse_json().proposals[0].draft == "Saved before account switch")
assert(state_path() != previous_path && proposals.len() == 0)
true
''',
    "account_discovery_clears_demo_mail_even_if_live_sync_fails": '''
load_demo()
current_pid = "d1" edit_draft = "Demo text" model_seen_ok = true
requests = []
load_accounts()
requests[0].cb({is_ok: true data: [{id: "real-account" address: "real@example.com"}] error: ""})
requests[1].cb({is_ok: false data: nil error: "Connection failed"})
assert(demo_mode == false && account.id == "real-account")
assert(messages.len() == 0 && proposals.len() == 0)
assert(current_pid == "" && edit_draft == "" && model_seen_ok == false)
assert(busy == false && status_text == "Connection failed")
true
''',
    "new_account_clears_previous_mail_before_sync": '''
messages = [e]
model_seen_ok = true
add_account()
assert(requests[0].method == "mail.add_account")
requests[0].cb({is_ok: true data: {id: "second-account" address: "second@example.com"} error: ""})
assert(messages.len() == 0 && current_pid == "" && edit_draft == "")
assert(model_seen_ok == false && proposals.len() == 0)
assert(requests[1].method == "mail.sync" && requests[1].args.account == "second-account")
true
''',
    "cancelled_account_connection_keeps_demo_and_proposals": '''
load_demo()
requests = []
add_account()
requests[0].cb({is_ok: false data: nil error: "Cancelled"})
assert(demo_mode && account.id == "demo")
assert(messages.len() == 6 && pending_count() == 3)
assert(requests.len() == 1)
true
''',
    "connecting_account_is_blocked_during_sync_or_send_review": '''
busy = true
add_account()
assert(requests.len() == 0)
busy = false reviewing_pid = p.id
add_account()
assert(requests.len() == 0)
true
''',
    "legacy_glance_uses_measured_height_and_explicit_demo_summary": '''
requests = []
demo_mode = true
publish_glance()
assert(contains(requests[0].args.script, "height: Fit"))
assert(contains(requests[0].args.summary, "演示"))
assert(contains(requests[0].args.summary, "未发送"))
demo_mode = false
requests = []
publish_glance()
assert(!contains(requests[0].args.summary, "演示"))
true
''',
    "demo_batch_publishes_one_final_desktop_card": '''
requests = []
load_demo()
let publishes = 0
for r in requests { if r.method == "glance.publish" { publishes = publishes + 1 } }
assert(publishes == 1)
assert(requests[0].args.title == "知信 · 3 项待确认")
true
''',
    "sync_analysis_waits_until_batch_end_before_publishing": '''
requests = []
busy = true
after_analysis(demo_raws()[3], demo_analyze(demo_raws()[3]))
assert(requests.len() == 0)
fetch_and_analyze(messages.len())
assert(busy == false)
assert(requests.len() == 1 && requests[0].method == "glance.publish")
true
''',
    "retrying_older_failed_mail_does_not_replace_known_latest": '''
let latest = {id: "d7" sender: e.sender address: e.address subject: e.subject
    body: "Final notice" preview: "" time: "11:00"}
let a = demo_analyze(demo_raws()[3])
a.new_v = "Latest value"
after_analysis(latest, a)
messages = [{id: "d7"} {id: "d4"} {id: "d1"}]
after_analysis(demo_raws()[3], demo_analyze(demo_raws()[3]))
assert(p.last_id == "d7" && p.new_v == "Latest value" && p.versions == 2)
assert(proposal_for_email("d4") == p)
true
''',
    "old_editor_events_cannot_overwrite_new_notice_draft": '''
screen = "detail"
let old_version = p.versions
let old_message = p.last_id
after_analysis(demo_raws()[3], demo_analyze(demo_raws()[3]))
let latest_draft = edit_draft
update_draft(p.id, old_version, old_message, "Old text still in input")
assert(edit_draft == latest_draft)
busy = true
update_draft(p.id, p.versions, p.last_id, "Typing during sync")
assert(edit_draft == latest_draft)
busy = false
update_draft(p.id, p.versions, p.last_id, "Current edit")
assert(edit_draft == "Current edit")
true
''',
    "open_detail_uses_new_draft_after_notice_update": '''
screen = "detail"
let next = demo_raws()[3]
after_analysis(next, demo_analyze(next))
assert(edit_draft == p.draft)
let latest_draft = p.draft
go_board()
assert(p.draft == latest_draft)
requests = []
execute_proposal(p.id, false)
assert(requests[0].args.body == latest_draft)
true
''',
    "malformed_acceptance_receipt_retains_pending": '''
execute_proposal(p.id, false)
requests[0].cb({is_ok: true data: "invalid" error: ""})
assert(p.status == "pending" && sent_replies.len() == 0)
assert(reviewing_pid == "")
true
''',
    "explicit_signed_delivery_is_recognized_from_body": '''
let mail = {id: "order" sender: "Shop" address: "shop@example.com" subject: "订单更新"
    body: "您的订单 OS-1042 已签收，运单号 JD1234567890。" preview: "" time: "11:00"}
let a = rule_analyze(mail)
assert(a.order_stage == "delivered")
true
''',
    "merged_middle_notice_is_deduplicated_after_restart": '''
let second = demo_raws()[3]
let third = {id: "d7" sender: e.sender address: e.address subject: e.subject
    body: "Final notice" preview: "Final" time: "11:00"}
after_analysis(second, demo_analyze(second))
let a = demo_analyze(second)
a.new_v = "Final value"
after_analysis(third, a)
save_state()
load_state()
let restored = find_proposal("d1")
assert(proposal_for_email("d4") == restored)
after_analysis(second, demo_analyze(second))
assert(restored.versions == 3 && restored.last_id == "d7")
assert(restored.new_v == "Final value")
true
''',
    "newest_first_inbox_is_analyzed_oldest_first": '''
messages = [{id: "latest"} {id: "oldest"}]
fetch_and_analyze(0)
assert(requests[0].method == "mail.message")
assert(requests[0].args.message == "oldest")
true
''',
    "unverified_fields_never_create_calendar_entries": '''
p.verified = false
p.new_v = "" p.ev_date = "" p.ev_time = "" p.ev_loc = ""
upsert_event(p)
assert(events.len() == 0)
true
''',
    "staged_refresh_resets_notice_progress": '''
start_staged_demo()
next_demo_notice()
next_demo_notice()
load_demo()
assert(demo_stage == 0 && messages.len() == 4)
next_demo_notice()
assert(demo_stage == 1 && messages.len() == 5)
true
''',
    "minimal_model_output_does_not_crash": '''
let a = analysis_from_model(e, {kind: "schedule_change" topic: "接孩子" reply_needed: true})
assert(a.reply_needed == true)
assert(a.old_v == "" && a.new_v == "")
true
''',
    "valid_quote_does_not_justify_invented_time": '''
let a = analysis_from_model(e, {kind: "schedule_change" topic: "接孩子" reply_needed: true draft: "回复"
    change: {old: "16:00" new: "18:30" quote: "9 月 17 日周四的接孩子时间由 16:00 调整为 15:30"}
    event: nil order: nil})
assert(a.verified == false)
assert(a.old_v == "" && a.new_v == "")
true
''',
    "quote_must_match_original_including_line_breaks": '''
assert(verify_quote("第一行\\n第二行", "第一行 第二行") == false)
assert(verify_quote("第一行\\n第二行", "第一行\\n第二行") == true)
true
''',
    "new_unverified_notice_clears_old_comparison": '''
let a = demo_analyze(e)
a.old_v = "" a.new_v = "" a.quote = "" a.verified = false
let next = demo_raws()[3]
upsert_proposal(next, a)
assert(p.old_v == "" && p.new_v == "")
assert(p.verified == false)
true
''',
    "order_identifiers_need_literal_evidence": '''
let oe = demo_raws()[2]
let a = analysis_from_model(oe, {kind: "order" topic: "订单" reply_needed: false draft: "" change: nil event: nil
    order: {order_no: "OS-1042" tracking: "MADEUP999" eta: "10 月 9 日" stage: "shipped"
        quote: "您的订单 OS-1042 已于今日发出，运单号 JD1234567890，预计 10 月 9 日送达。无需回复。"}})
assert(a.tracking == "")
true
''',
    "demo_never_overwrites_live_state": '''
save_state()
let real_path = writes[0].path
let before = files[real_path]
load_demo()
execute_proposal("d1", false)
assert(files[real_path] == before)
for w in writes { if w.path == real_path { assert(w.data == before) } }
true
''',
    "account_state_uses_distinct_safe_paths": '''
writes = []
save_state()
let first = writes[0].path
account = {id: "other/account" address: "other@example.com"}
save_state()
let second = writes[1].path
assert(first != second)
assert(second.search("/") < 0)
true
''',
    "saved_draft_survives_navigation": '''
screen = "detail"
edit_draft = "Draft saved before changing screen"
go_board()
assert(p.draft == "Draft saved before changing screen")
true
''',
    "latest_mail_in_merged_proposal_is_marked_read": '''
p.last_id = "latest-message"
open_detail(p.id)
assert(requests[0].method == "mail.mark_read")
assert(requests[0].args.message == "latest-message")
true
''',
    "verified_model_change_keeps_literal_values": '''
let a = analysis_from_model(e, {kind: "schedule_change" topic: "接孩子" reply_needed: true
    change: {old: "16:00" new: "15:30" quote: "9 月 17 日周四的接孩子时间由 16:00 调整为 15:30"}})
assert(a.verified == true && a.old_v == "16:00" && a.new_v == "15:30")
true
''',
    "bad_model_types_fall_back_without_crashing": '''
let a = analysis_from_model(e, {kind: "unknown" topic: [] reply_needed: "yes"})
assert(a.engine == "rules")
let b = analysis_from_model(e, "not an object")
assert(b.engine == "rules")
true
''',
    "live_state_roundtrip_is_bound_to_account": '''
rules.push({address: p.address kind: p.kind sender: p.sender})
save_state()
load_state()
assert(proposals.len() == 1 && rules.len() == 1)
account = {id: "second-account" address: "second@example.com"}
load_state()
assert(proposals.len() == 0 && rules.len() == 0 && events.len() == 0)
true
''',
    "demo_does_not_inherit_live_authorization_rules": '''
rules.push({address: "real@example.com" kind: "new_event" sender: "Real"})
save_state()
load_demo()
assert(rule_matches("real@example.com", "new_event") == false)
true
''',
    "only_real_acceptance_adds_exact_send_history": '''
execute_proposal(p.id, false)
requests[0].cb({is_ok: true data: {accepted: true id: "receipt-1"} error: ""})
assert(sent_replies.len() == 1)
assert(sent_replies[0].body == "Edited reply")
assert(sent_replies[0].receipt_id == "receipt-1")
assert(p.receipt_accepted == true)
load_demo()
execute_proposal("d1", false)
assert(sent_replies.len() == 0)
true
''',
    "later_notice_reopens_same_completed_card_with_history": '''
execute_proposal(p.id, false)
requests[0].cb({is_ok: true data: {accepted: true} error: ""})
let next = demo_raws()[3]
after_analysis(next, demo_analyze(next))
assert(proposals.len() == 1)
assert(p.status == "pending" && p.versions == 2)
assert(sent_replies.len() == 1 && sent_replies[0].body == "Edited reply")
assert(p.receipt_accepted == false)
true
''',
    "staged_demo_shows_initial_notice_then_updates_same_card": '''
start_staged_demo()
assert(messages.len() == 4)
let original = find_proposal("d1")
assert(original.new_v == "9月17日 15:30")
open_detail("d1")
execute_proposal("d1", false)
next_demo_notice()
assert(messages.len() == 5 && proposals.len() == 4)
assert(original.new_v == "9月17日 15:20" && original.status == "pending")
assert(original.versions == 2)
true
''',
    "staged_logistics_notice_merges_and_stops_at_end": '''
start_staged_demo()
next_demo_notice()
next_demo_notice()
assert(messages.len() == 6 && proposals.len() == 4)
assert(find_proposal("d3").order_stage == "delivered")
next_demo_notice()
assert(messages.len() == 6)
assert(sent_replies.len() == 0)
true
''',
}

if __name__ == "__main__":
    sys.exit(main(CASES))
