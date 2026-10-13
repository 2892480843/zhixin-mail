# 0.3.6 决赛版本地验证记录

日期：2026-10-13，北京时间。环境：macOS / Darwin arm64、zsh。开发版本 0.3.6；Git 基线 v0.2.1 / `09285755c6791579d03dbec86be52d77f26ee9a9`，本轮改动尚未提交或推送。

## 结果与证明范围

| 验证层级 | 结果 | 证明范围 |
| --- | --- | --- |
| 发送回归 | 14/14 通过 | review_send、明确接受回执、取消、重复审阅、规则不后台发送、旧回执与卡片请求 |
| 决赛优化回归 | 34/34 通过 | 缺失/错误模型字段、伪造字段、原文换行、旧结论清理、账号隔离、草稿版本、发送记录、同卡重开、去重与重试顺序、分步演示、批量卡片合并发布、内容高度、演示摘要、连接取消/忙碌保护、账号切换清空及旧草稿保存 |
| 原生演示 | 15/15 通过 | 收件箱、详情、看板、演示完成、规则、重放、展开原文、空发送记录、分步初始与后续更新、欢迎、日程、空看板、同步失败和物流；另 5 次窄窗、4 次宽窗检查 |
| 主要操作位置 | 通过 | 412×892 窗口普通/再次更新提案均完整显示 46 点高按钮；不是仅按钮可见片段 |
| 本地 hub 门禁 | PASSED | 包结构、资料、权限和摘要；保留 unsigned 开发包警告 |
| 扫描材料 | 已生成 7 问 packet | 未配置外部模型审核器，不宣称模型审核通过 |
| 独立复核 | 通过 | 0.3.0 阶段 40 项回归重跑；另 3 项边界（旧邮件失败重试完整异步链、旧编辑事件跨导航、旧存档来源记录兼容）通过 |
| 官方宿主下载 | 已校验并解压 | RC6 Mac ARM64，摘要、Info.plist 已核对；宿主已启动、知信已安装 |
| 本地安装目录 | catalog 验签通过 | 测试签名副本、7 版本条目、本地 pack 与隔离启动脚本；不是公共上架；0.3.6 尚未在宿主安装 |
| QQ 服务器入口 | 2 项连通 | IMAP 993 / SMTP 465 证书与欢迎消息验证，无认证、读取或发送 |
| RC6 安装与启动日志 | 安装通过、启动日志已取得 | 安装版本为 0.3.3，与当时源码一致，当前 0.3.6 待更新；实际点击与桌面卡正文、计数、撤下已验证 |
| 真实宿主 glance | 演示数据验证通过 | 3→2→1→0、展开正文、宿主打开箭头、全部完成撤下；无邮箱或模型调用 |
| 真实邮箱 / 模型 | 未现场验证 | 宿主登录表单已打开，需用户配置；不能以演示代替真实收发 |

包 BLAKE3（包内容摘要）：`1219fc7f68d7ccc19f29d784f3ddcc9c1c65cac7e47cd282b661a51605e95f82`。截图写入后重新 stamp/check；随后只更新 bundle 外材料。

## 复现命令

从项目根目录运行，工作区已有固定工具链：

```sh
python3 tests/test_send_flow.py --deps ../../octosense-ws/OctoSense-App-Hub/target/release/deps
python3 tests/test_finale_flow.py --deps ../../octosense-ws/OctoSense-App-Hub/target/release/deps
python3 tests/native_preview.py --hub ../../octosense-ws/OctoSense-App-Hub/target/release/hub --card-host ../../octosense-ws/OctoSense-App-Hub/target/release/card-host --output build/native-preview-new-run
../../octosense-ws/OctoSense-App-Hub/target/release/hub check bundle --allow-unsigned
../../octosense-ws/OctoSense-App-Hub/target/release/hub scan bundle --packet build/review-v0.3.6-new.json
git diff --check
```

原生输出目录必须全新，每场景使用独立沙箱并退出。默认 412×892，展开原文用 412×1600。通过定时导航执行生产函数，未模拟鼠标/键盘，这套脚本未验证完整输入事件或真实宿主审阅窗口；本轮另使用 CUA 实际点击 RC6 验证演示确认与 glance。回归执行真实 Splash 解释器，host/文件系统/界面边界为替身，不接入邮箱。

## 证据

- `build/finale-evidence/send-regression-v0.3.6.txt`、`finale-regression-v0.3.6.txt`、`native-regression-v0.3.6.txt`。
- `build/native-ui-v0.3.6-final/<scene>/snapshot.json`、`card-host.log` 与实际原生渲染 PNG；包内三张 screenshots 已更新，保持演示标识。
- [GATE.txt](GATE.txt)、`build/review-v0.3.6.json`。
- `build/host-download/verification.json`、官方 `SHA256SUMS` 与发布 receipt。
- `build/finale-store/verification-v0.3.6.txt`、`build/finale-evidence/qq-server-probes.json`。

中间失败产物保留在 build，不作为最终证据。修复先观察相关用例失败再回归。原生检查发现不支持的 RightWrap 名称、异步导航竞态和按钮矩形裁切造成的误判，已修正语法、测试时序和完整可见检查。

## 复核后补齐的边界

- 保留每封来源标识，重复同步不重放中间旧通知；旧记录 fallback 先保留此前 last_id。
- 较旧邮件上次读取失败、较新邮件已处理：重试只记来源，不回退新版；顺序依据宿主当前新到旧的收件箱快照。
- 详情编辑框跟随新版；旧渲染输入事件、同步或审阅期间输入不覆盖新版草稿。
- 错误类型回执保留待确认；「已签收」按正文识别送达，不盲信模型枚举。

## 已知限制

本地 makepad/octoscript/runtime 修订为 `c155f61d0e1600d2ec474209374444a38a09a470`、`5991dfae9344589e732b2605b530f788e8bbcd11`、`2cc5ef37d7d6a3d2992673389ce74488f7bb2d87`。card-host 不提供真实 mail/model/glance；完整 RC6 的 glance 已验收，真实邮箱与模型需另行验收。

每次扫描最近 10 封；合并依赖发件地址与事项标题一致。模型标题漂移、更早历史、不在同一快照中的乱序未承诺全面处理。旧版未绑定账号文件保留不自动导入；状态含邮件内容。系统日历不在本次范围内。

[HOST-SETUP.md](HOST-SETUP.md) 为准备入口，[REAL-HOST-DEMO.md](REAL-HOST-DEMO.md) 为现场验收。未创建公共发布、未更新比赛提交、未发信或向评审发表评论。

## 真实宿主排练补充

官方 RC6 通过独立签名本地商店安装当时的 0.3.3，安装后 main.splash 与当时工作区逐字节一致；不能作为 0.3.4 安装证明。CUA 实际点击证实演示确认、应用内日程、glance 正文与 3→2→1→0、最后撤下。安装记录见 `build/finale-evidence/rc6-validation-v0.3.3.json`，截图见 REAL-HOST-DEMO。

初次真实运行暴露每封分析加批末都发布导致每分钟 6 次限流；批处理中抑制中间发布，最终只发布一次。展开脚本卡的根视图 Fill 导致正文空白；官方 RC6 要求 legacy 脚本使用 Fit 计算内容高度，改后实际正文恢复。新增摘要区分演示，移除不可点击却像链接的正文提示，打开应用使用宿主右箭头。这两类问题均先复现，再修复验证。

记录保留早期失败日志；当前 v0.3.3 启动区段未出现限流拒绝。RC6 商店详情多次连续更新后按钮曾无响应，重启本轮独立宿主后安装完成；未修改官方宿主代码。真实账号、模型、宿主发送审阅、收件方送达与录像仍未验收。

## 0.3.4 真实连接修复

新增演示页面连接入口。`activate_account` 保存旧账号草稿后清空邮件和编辑状态，再加载目标账号数据；取消连接保留当前数据，同步或审阅期间禁止连接。新增回归先观察 3 项失败，修复后新增 5 项均通过，合计 48 项。原生 10 页通过，并检查连接入口完整显示。

本机测试 catalog sequence 5 已验签。操作宿主时检测到用户接管，保留登录窗口，没有更新当前安装。账号表单未认证，真实收发、模型和送达仍未验证。

## 0.3.6 温暖生活助手 UI

用户明确选择温暖生活助手方向。奶油底、柔和蓝、鼠尾草绿；统一字级与间距，原安排/新安排有明确文字标签。分隔由默认 45 点改为 1 点；演示与连接合并一行，正常计数由摘要呈现，错误仍可见。长邮件主题与时间分行，避免相互挤压；欢迎、日程、规则、空状态保持一致。

48 项业务回归通过，15 个标准窗口场景、5 个 360×800 场景、4 个 840×892 场景通过。主要操作保持完整 46 点高度。静态配色 6 组计算对比度为 4.67–10.89，不能代替完整辅助功能验收。详见 [UI-DESIGN.md](UI-DESIGN.md)。本轮未操作正在登录的宿主，0.3.6 待更新；当前截图使用 card-host 演示数据。

## 0.3.7 真实收件可靠性补充

本轮在 macOS 检查宿主邮箱地址和授权码仍为空；QQ 官方网页登录页亦未登录。已打开官方扫码页面并交给用户，未获取或生成授权码，未读取真实邮件、发送邮件或验证模型。宿主表单仍为默认 Gmail 服务器；尝试修改收件服务器没有改变可见字段，不能宣称 QQ 参数已填好。

代码修复单封读取失败静默跳过的问题。先观察失败用例，再补充失败数量提示与下次同步清理；当前 14 项发送 + 36 项业务优化回归共 50 项通过。新增 `16-read-failure` 原生场景执行生产失败路径，显示 1 封未读取和刷新重试；使用无邮件服务的 card-host 与虚构账号，不能作为真实收件证明。温暖 UI 未更改；前文 24 次渲染为 0.3.6 历史证据。本轮 0.3.7 准入通过，扫描材料已生成，未运行外部模型评审器。


## 2026-10-14 提交前复验（0.3.7）

- 当前代码重新运行发送回归 14/14、决赛回归 36/36，共 50/50 通过。测试替换外部边界，不发送邮件。
- 本地 App Hub 工作区 `ba36df0505e198f998201af312ff5184df98cae9` 开发包检查通过，unsigned 警告保留。本次 GitHub 发布工具固定官方最新修订 `386359153ed6377b5f047bd9ed2767a6a2ac2bc7`，其准入检查和来源证明以 tag 工作流结果为准。
- 官方 RC6 安装知信 0.3.7，安装源码与当前 bundle 一致；实际 QQ 邮箱认证后显示 10 封来信、4 项待确认和桌面 glance 卡。
- 当前没有真实发送记录，SMTP 发送、收件方送达、模型结果和连续录像尚未实测。
- 已确认 RC6 仍为最新官方桌面发行版；网页和 GitHub Releases API 均核对。
- 公开证据摘要：`review/evidence/real-mail-validation-v0.3.7.json`；真实来信与凭据不公开。
- 0.3.6 原生多尺寸 UI 与 0.3.3 演示循环是历史证据，不能记为本轮重新执行。


## 0.3.8 最新优化验收（2026-10-14）

环境：macOS / Darwin 25.6.0 arm64，zsh；应用基线 v0.3.7 / 78a2476。

| 检查 | 结果 | 边界 |
| --- | --- | --- |
| 发送业务 | 20/20 | 宿主审阅、独立自发测试记录、取消、模糊回执、忙碌保护；外部边界为替身 |
| 邮件质量业务 | 57/57 | 通知页脚、引用旧要求、回复主题、同卡分类、时刻方向、物流否定/未来表达、单号引用、旧规则迁移、重复卡与草稿保留 |
| 原生界面 | 21/21 | 当前原生场景，包含连接页、规则回退、未知物流、此前单号引用及合并前草稿 |
| 多尺寸 | 窄窗 3/3、宽窗 3/3 | 360×800 / 840×892 检查分析来源、未知物流、连接页；窄窗连接页另复验 1/1 |
| 包检查 | PASSED | 本地 Hub ba36df05；unsigned 开发包警告保留；最新工具准入以 GitHub tag 工作流为准 |
| 独立静态复核 | P2 已修复 | 英文未来/否定、旧主题冲突和账号诊断重置；最后 P3 当前详情选择重映射也已修复并回归 |
| 官方 RC6 实际更新 | 0.3.8 已安装 | 源文件逐字节匹配；本机签名 catalog sequence 9；不是公共准入 |
| 实际来信 | 显示最近 10 封，旧待办 4→0 | 不代表规则召回率或全邮箱准确率；缺失历史的重复主题分卡保留并提示 |
| 模型连接 | 固定文本检查未就绪 | 需要检查宿主提供方配置；未验证真实邮件模型质量 |
| 实际发送审阅 | 用户批准后被宿主拒绝 | “The Mail account is signed out; review is no longer valid”；未取得 accepted 回执，未声称送达 |

生产代码保留逐字引用护栏。规则使用宿主支持的字符组处理英文词边界；本地正则不支持 `\b`，先复现编译失败后改为显式字母边界。时间顺序不明不填 old/new。旧规则同主题卡仅在最新收件列表能证明先后时合并，完整来源标识联合保留，旧草稿存档可在完整原文区域查看；缺失历史不猜时间。

证据：`build/finale-evidence/{send,quality}-v0.3.8-complete.txt`、`native-v0.3.8-published.txt`、`native-v0.3.8-{narrow,wide,connection-final,merged-draft}.txt`、`gate-v0.3.8.json`。开发包摘要 `704aec2eca14d19e405d577a852d94fdeafeeac458409de04092dec709dc0b17`；公开发布证明另由工作流产生。

真实发送失败已定位到宿主 Mail 未登录：实际 Mail 显示 Add account；官方 RC6 的 mail_card.rs:54–57 校验 `os.mail` 活跃账号。QQ 地址与收发服务器已准备，授权码仍需用户直接输入宿主。未修改宿主账号授权文件、未获取密钥、未绕过物理批准。真实邮件截图只保留本机，公开摘要匿名。


### 0.3.8 正式发布与提交结果

固定标签 `v0.3.8` / `3b21fc730aa7d2ffd42b4a694a26635cf1d25837` 已推送，GitHub [工作流](https://github.com/2892480843/zhixin-mail/actions/runs/38445812869) prepare/publish 均成功。正式发布使用 App Hub `386359153ed6377b5f047bd9ed2767a6a2ac2bc7`。

下载包 SHA256：`7b431770eb8f25f8c0e3a91d1e7b81f20567d2dee8e925bf5628280f0ed3dd60`，与公开 release-receipt.json 一致；main.splash / listing.json 与标签逐字节一致。GitHub CLI 按仓库和 `.github/workflows/publish-app.yml` 验证签名证明成功；本地兼容工具解包/复验 passed，无 findings。

[App Hub 后续提交](https://github.com/OctoSense-org/OctoSense-App-Hub/issues/106#issuecomment-6152353565)、[云上码术队伍更新](https://github.com/gosimfoundation/hackathon-agenticapp26/issues/13#issuecomment-6152354145) 已发表，正文与本机提交材料回读一致。公开 [Release](https://github.com/2892480843/zhixin-mail/releases/tag/v0.3.8) 说明回读一致，3 个资产保留。不宣称管理员已准入或新评分已出。

发布后仅补充 bundle 外的当前讲稿、界面说明与发布回执；没有移动标签或替换已公开的安装包。匿名公开结果见 [public-release-v0.3.8.json](evidence/public-release-v0.3.8.json)。真实 SMTP、送达和模型质量边界如前。
