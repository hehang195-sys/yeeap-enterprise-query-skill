# yeeap-enterprise-query 企业查询 Skill

> 官方成功案例：企业信息查询付费 Skill。
> 用户输入企业关键词后，Skill 创建订单，调用官方 `yeeap-wallet` 完成支付，支付成功后返回企业工商信息。

## 普通用户如何使用

普通用户不需要本地启动 `yeeap` 后端，也不需要配置 `app_id`、`app_secret`、`skill_id` 或 `mockPayee.*`。
这些配置由 Skill 维护者或平台部署方处理。

你只需要在 Agent 中提出企业查询请求，例如：

```text
查询阿里巴巴的企业工商信息
```

Agent 会按以下流程执行：

1. 检查企业是否在当前支持范围内。
2. 创建企业查询订单。
3. 调用官方 `yeeap-wallet` 完成支付授权。
4. 支付成功后返回企业工商信息。

如果 Agent 找不到官方支付 Skill，会先自动执行安装命令安装 `yeeap-wallet`；安装完成后，需要完全退出并重启 Agent 客户端再重试。

## 当前支持的企业范围

当前仅支持以下企业关键词：

阿里巴巴 / 腾讯 / 字节跳动 / 美团 / 京东 / 百度 / 易宝 / 网易 / 华为 / 小米

如果输入的企业不在支持范围内，Skill 会在创建订单前直接拦截并提示，不会要求用户付款。

## 面向 Agent 的执行协议

运行本 Skill 时，以 `SKILL.md` 为准。业务 Skill 只负责：

1. Phase 1：执行 `scripts/create_order.py` 创建订单。
2. Phase 2：调用官方 `yeeap-wallet`，只传入 `order_no` 与 `app_id`。
3. Phase 3：执行 `scripts/service.py` 拉取企业查询结果。

业务 Skill 不直接执行 `yeeap-cli`，也不自行处理支付授权、查询或补凭证流程。

## 维护者/本地开发部署说明（普通用户无需执行）

以下内容仅供 Skill 维护者、本地联调人员或平台部署方使用。不要把本章节作为普通用户使用前置条件展示。


## 常见问题

| 现象 | 原因 | 处理 |
|------|------|------|
| 订单创建失败: 400 question 不能为空 | Phase 1 漏传参数 | 加引号传企业关键词 |
| 订单创建失败: 400 当前仅支持以下企业关键词 | 企业查询成功案例暂未收录该企业 | 改用支持企业关键词，未创建订单也不会扣款 |
| 订单创建失败: 500 企业查询服务配置缺失 | 维护者未配置企业查询业务后端 | 普通用户不要自行配置，联系 Skill 维护者；维护者按“维护者/本地开发部署说明”写入 `app_id` / `app_secret` / `skill_id` |
| 支付提交 403 skill_id 不属于该 app_id | `skill_id` 与 `app_id` 不匹配 | 维护者重新检查邮箱或 H5 我的 Skill 列表里的 `skill_id` |
| 支付提交 403 沙箱支付未启用 | QA 未开沙箱或生产环境 | 维护者确认 `yeeap.sandbox.enabled=true`（生产必须为 false） |
| 支付提交 403 该 skill 未启用沙箱 | skill 未标记 `sandbox_enabled` | 维护者重新登记 Skill 或执行 V9 DDL |
| Phase 3 PAY_STATUS=ERROR 支付凭证解密失败 | wallet credential 密钥与默认值不一致 | 维护者保持默认配置或显式设置 `yeeap.wallet.credential-sm4-key-base64` |
| Phase 3 未找到匹配企业 | question 中没包含已收录关键词 | 用「阿里巴巴」「腾讯」等明确关键词重试 |
