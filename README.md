# 知信 · ZhixinMail

> 从来信中识别安排与变化，提出日程更新和回复草稿，确认后执行。

GOSIM 2026 智能体应用黑客松 · 邮件赛道参赛作品（OctoSense 脚本应用）。

## 演示视频

[zhixin-demo-v0.2.0.mp4（36 秒，中文解说）](https://github.com/2892480843/zhixin-mail/releases/download/v0.2.0/zhixin-demo-v0.2.0.mp4)：识别 → 提案 → 授权 → 执行 → 日程板 / 物流追踪，card-host 实拍界面逐帧采集。

## 它做什么

一封学校来信把周四接孩子的时间从 16:00 改为 15:30。知信读完这封信，把两个下一步放到你面前：一项日历变更（16:00 → 15:30）和一封可直接修改的确认回复。你改完草稿，选择「仅确认这一次」或「始终允许这类操作」，知信才执行。

完整闭环：

1. **识别** — `mail.sync` / `mail.list` / `mail.message` 读取来信；`model.complete` 做结构化提取（事项类型、新旧时间、事件要素、回复草稿），规则引擎在模型不可用时兜底。
2. **核对** — 每条提取必须附邮件原文引用，且引用逐字出现在正文中（no-facts 护栏）；模型给出但核对不上的内容被丢弃并明确标注「未能在原文中逐字核对」。
3. **提案** — 变更以旧→新对比卡片呈现；同一事项的后续来信更新同一张提案卡（版本号 +「提案已按新来信调整」），不会每封通知都生成一张新卡。
4. **授权** — 「确认并发送」只处理这一封；「始终允许」生成发件人 + 动作维度的规则（如「橡树学校的安排变更 → 自动发送确认回复」），不扩展到其他邮件，授权规则页可随时撤销。
5. **执行** — 确认后 `mail.send` 发送回复，提案进入完成态并保留已发送内容；待办数量同步到桌面 glance 卡片（`glance.publish`，shell 环境生效，card-host 中静默降级）。
6. **物流追踪** — 订单邮件提取订单号 / 运单号 / 预计送达，三步进度可视化；后续发货、送达邮件更新同一份追踪卡，不新增重复卡片。
7. **日程板** — 确认过的日程提案写入应用内日程板；新变更先匹配已有事项（标题匹配去重），显示「将更新已有日程，不会新增重复日程」。

## 与关键词匹配方案的区别

同赛道常见做法是用关键词 + 正则做本地匹配。知信的第一分析引擎是设备上的 `model.complete`（结构化 JSON 输出、schema 校验、逐字引用核对），关键词引擎只在模型服务不可用时兜底；演示数据则保证 card-host 无服务环境下也能完整评审闭环。

## 运行与评审

```sh
# 环境：OctoScript-App-Design-Flow + OctoSense-App-Hub（见官方 QUICKSTART）
tools/octo run apps/zhixin-mail/bundle --port 8141 --detach
tools/octo shot 8141 shot.png
tools/octo check apps/zhixin-mail/bundle
```

card-host 中没有邮件与模型服务，应用自动进入**演示模式**：内置 6 封来信（学校时间变更 + 同一事项的后续补充通知、会议邀请、订单发货与送达、英文改期），完整覆盖识别 → 提案 → 授权 → 执行 → 日程板 / 物流追踪闭环。

3 分钟评审路径：

1. 启动 → 收件箱（识别状态 chips、同一事项「第 2 次更新」标记）
2. 打开橡树学校来信 → 变更卡片（红绿对比 + 原文引用 + 更新提示）
3. 修改草稿 → 「确认并发送回复」→ 完成态（待办 3 → 2）
4. 打开张明远来信 →「始终允许此类操作」→ 授权规则页可见、可撤销
5. 「刷新」重放演示 → 橡树学校来信命中规则自动执行（待办看板只剩 2 项）

## 能力与隐私

| 能力 | 用途 |
| --- | --- |
| `mail` | 读取收件箱、标记已读、发送确认回复（账号由宿主 sheet 登录，应用不接触密码） |
| `model` | 一次性结构化分析来信（设备配置的 AI 提供方，应用看不到 provider 与密钥） |
| `storage` | 保存提案状态与授权规则（设备沙箱内） |
| `glance` | 待确认数量发布到桌面卡片 |

邮件正文只发给设备自己配置的 AI 提供方做一次性分析，不离开设备到任何第三方服务器；无网络 host 声明。

## 已知边界

- 日历写入：App Hub 暂无面向商店应用的 calendar 能力，日程更新以提案卡形式呈现，回复执行后日历侧由用户在系统日历中确认（与当前平台能力一致，见 OctoSense 文档）。
- `card-host` 无 mail/model/glance 服务：演示模式兜底；真实链路在 OctoSense shell（desktop）中验证。
- 规则引擎兜底只做定性识别（类型 + 引用句），新旧值对比依赖 model.complete 或演示数据。

## 提交与发布状态

| 项 | 值 |
| --- | --- |
| App Hub 提交 issue | [OctoSense-App-Hub#106](https://github.com/OctoSense-org/OctoSense-App-Hub/issues/106)（Submit zhixin-mail，待管理员受理） |
| 初赛仓库提交 | [hackathon-agenticapp26#13](https://github.com/gosimfoundation/hackathon-agenticapp26/issues/13)（队伍：云上码术） |
| 发布通道 | `publisher-github-v1`：推送 `v<manifest.version>` tag → `.github/workflows/publish-app.yml` 生成经 GitHub 证明的 release pack |
| 准入门禁 | `hub check` PASSED（见 `review/GATE.txt`），BLAKE3 见 release 里的 receipt |
| 评审问答 | `review/ANSWERS.md`（`hub scan` 的 7 问，逐条附源码引用） |
| 隐私 / 支持 | [PRIVACY.md](PRIVACY.md) · [SUPPORT.md](SUPPORT.md) |

上架由 App Hub 管理员在审核后执行受保护目录工作流完成，开发者不直接改 `catalog.json` / `index/` / `artifacts/`。

## 目录

```
bundle/              提交内容：main.splash / manifest.json / listing.json / assets / screenshots
.github/workflows/   publish-app.yml：tag push 生成带 GitHub 证明的 release pack
review/              GATE.txt（门禁输出）+ ANSWERS.md（scan 七问）
PRIVACY.md SUPPORT.md
```

## 许可证

Apache License 2.0，见 [LICENSE](LICENSE)。
