# 知信支持与反馈

## 报告问题

在仓库开 issue：https://github.com/2892480843/zhixin-mail/issues

请附上：

1. OctoSense 宿主版本与平台（目前仅在 macOS 上验证过）；
2. 应用版本（bundle 清单里的 `version`，例如 0.2.1）；
3. 复现步骤：点到哪一步、看到了什么；
4. 若与识别结果相关：来信的脱敏片段（时间、地点可改写，但保留句式），以及应用给出的提案。

## 已知边界

- 演示数据（6 封内置来信）在无宿主邮件服务的环境中也能跑通全流程；真实收件箱需要宿主提供 `mail` 服务。
- 若宿主不提供 `model` 服务，应用退化为规则引擎：仍能识别显式的时间/日期变更，但不做语义抽取，且会把「未使用模型」标注在界面上。
- 时间解析以宿主 `local_time()` 为基准；在 `card-host` 中运行为 UTC。
- 只在 macOS 上测试过。其他平台未验证。

## 版本与更新

每个版本对应一个不可变的 Git tag（`v<manifest.version>`）与一份由发布工作流生成的 `app.bundle.pack.json`。校验方式：

```sh
shasum -a 256 app.bundle.pack.json   # 与 release-receipt.json 里的 pack_sha256 一致
```
