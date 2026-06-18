# yeeap-enterprise-query Skill 演示指南

> 演示场景：业务方接入 yeeap 支付，提供「企业信息查询」付费 Skill。
> 联调链路：Skill 创建订单 → 模拟收款方后端签发 encrypted_data → yeeap-wallet 完成支付 → Skill 凭 payCredential 拉取查询结果。
> `pay-query` 只代表订单状态；只有新版 yeeap-wallet 写入本地 payCredential 后才能进入 Phase 3。

## 1. 前置准备（一次性配置）

### 1.1 启动 yeeap 后端（含模拟收款方端点）

```bash
mvn -DskipTests package
java -jar target/yeeap-*.jar
# 默认监听 http://127.0.0.1:8080/yeeap
```

### 1.2 在 H5 完成「我要收款」+ Skill 登记

1. 打开 H5（`/yeeap/`），登录后进入「我要收款」，输入邮箱开通收款，记下邮件中的 `app_id` 与 `app_secret`。
2. 在「我的 Skill」区域点击「+ 登记」，填写 Skill 名称 / 摘要 / 仓库地址（选填）与接收邮箱（默认使用开通收款时的邮箱），提交后系统立即下发 `skill_id` 并发送至邮箱。

### 1.3 把真实凭证写入配置中心

不要写入 `application.yml`。在配置中心 `YEEAP_BASE_CONFIG` 中新增：

| Key | 示例 | 说明 |
| --- | --- | --- |
| `mockPayee.enabled` | `true` | 是否启用企业查询 demo 后端。 |
| `mockPayee.appId` | `app_xxx` | H5 邮件中收到的 app_id。 |
| `mockPayee.appSecret` | `xxxxxxxx` | H5 邮件中收到的 app_secret，Base64。 |
| `mockPayee.skillId` | `SKL_xxx` | 邮件下发的企业查询 Skill ID。 |
| `mockPayee.defaultAmountFen` | `1` | 默认订单金额，单位分。 |

> 注意：`app_secret` 必须是 Base64 编码的 16 字节明文（默认值 `eWVlYXBAMDA3LnllZXBheQ==` 即 `yeeap@007.yeepay`）。
> 这一阶段同时会验证 `yeeap.wallet.credential-sm4-key-base64` 与上述 secret 一致；演示阶段保持默认即可。

重启服务后生效。

## 2. 演示链路（每次跑）

### 2.1 沙箱验收（推荐，零元）

不扣真实余额，走 QA Open API 全链路。demo 默认创建 `pay_env=SANDBOX` 订单：

```bash
cd agent-skills/yeeap-enterprise-query

python3 scripts/create_order.py "阿里巴巴"
# 记下 ORDER_NO、APP_ID；输出应包含 PAY_ENV=SANDBOX

npx --yes yeeap-cli@0.3.6 pay-context -o <ORDER_NO> -a <APP_ID> --env sandbox
python3 scripts/service.py <ORDER_NO>
```

或从仓库根目录：

```bash
./tools/skill-acceptance/run.sh agent-skills/yeeap-enterprise-query "阿里巴巴"
```

### 2.2 真支付演示（可选）

```bash
cd agent-skills/yeeap-enterprise-query

export YEEAP_PAY_ENV=PRODUCTION

# Phase 1：创建订单（模拟收款方后端会签发 encrypted_data 与 skill_id）
python3 scripts/create_order.py "阿里巴巴"
# 输出：
# ORDER_NO=DEMO20260615...
# AMOUNT=1
# QUESTION=阿里巴巴
# APP_ID=app_xxx
# SKILL_ID=SKL_xxx
# PAY_ENV=PRODUCTION

# Phase 2：调用 yeeap-wallet 完成支付（在 Claude / Cursor 中由 yeeap-wallet skill 触发）
# 等价命令：
npx --yes yeeap-cli@0.3.6 pay-context -o <ORDER_NO> -a <APP_ID>
# 期间会出现支付授权链接，扫码完成授权后回到命令行即可

# Phase 3：拿支付凭证查询企业信息
python3 scripts/service.py <ORDER_NO>
# 输出：
# PAY_STATUS: SUCCESS
# 公司全称：阿里巴巴（中国）网络技术有限公司
# 统一社会信用代码：91330100799655058B
# 法定代表人：戴珊
# ...
```

## 3. 演示企业库

当前内置 10 家企业的真实工商信息（数据来源：国家企业信用信息公示系统）：

阿里巴巴 / 腾讯 / 字节跳动 / 美团 / 京东 / 百度 / 易宝 / 网易 / 华为 / 小米

若需扩展，编辑 `src/main/java/com/yeepay/yeeap/controller/mock/EnterpriseInfoRegistry.java` 即可。

## 4. 常见问题

| 现象 | 原因 | 处理 |
|------|------|------|
| 订单创建失败: 400 question 不能为空 | Phase 1 漏传参数 | 加引号传企业关键词 |
| 订单创建失败: 500 模拟收款方配置缺失 | application.yml 未配置 | 按 §1.3 写入 app_id / app_secret / skill_id |
| 支付提交 403 skill_id 不属于该 app_id | skill_id 与 app_id 不匹配 | 重新检查邮箱或 H5 我的 Skill 列表里的 skill_id |
| 支付提交 403 沙箱支付未启用 | QA 未开沙箱或生产环境 | 确认 `yeeap.sandbox.enabled=true`（生产必须为 false） |
| 支付提交 403 该 skill 未启用沙箱验收 | skill 未标记 sandbox_enabled | 重新登记 Skill 或执行 V9 DDL |
| Phase 3 PAY_STATUS=ERROR 支付凭证解密失败 | wallet credential 密钥与默认值不一致 | 保持默认配置或显式设 `yeeap.wallet.credential-sm4-key-base64` |
| Phase 3 未在演示企业库中找到匹配企业 | question 中没包含已收录关键词 | 用「阿里巴巴」「腾讯」等明确关键词重试 |
