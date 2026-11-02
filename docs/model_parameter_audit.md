# 测评模型参数核查与接入清单

核查日期：2026-10-27。**文档证据不等于账号调用成功**；下列“待验证”不是“不支持”。正式批跑前须对每个具体端点、地区、账号权限和模型快照实测截图、格式、token 上限、思考配置、实际传入参数及返回结果，并冻结记录。主测统一 B 档、一次一个动作、采样参数省略；输出上限首版 32768 token，服务不支持时在开跑前确定并披露可用上限。`medium` 是各自服务的中档，不代表各家算力或 token 等价。

## 已核查的厂商文档

- OpenAI：[GPT-6 使用指南](https://developers.openai.com/api/docs/guides/latest-model)指出 GPT-6 Astra 和 GPT-6.1 Sol 不支持 `none`；推理非 `none` 时不发送 temperature 等采样参数。GPT-6.1 Terra 和 GPT-6 Luna 支持 `none`，主测选 `medium`。指定模型及接口仍须实测。该指南说明工具调用存在接口限制；本项目用文本动作而非默认启用平台托管工具。
- Anthropic：[模型列表](https://platform.claude.com/docs/en/models/overview)列出四个 Claude 型号、图像与 adaptive thinking；其[思考文档](https://platform.claude.com/docs/en/build-with-claude/thinking)说明部分型号不能使用非默认采样参数。每个具体 5.5 型号的参数约束以目标 Models API/接口文档与实测为准，不以旧型号约束代替。
- Google：[Gemini 4 Argon 官方指南](https://ai.google.dev/gemini-api/docs/latest-model)说明采样参数被忽略，支持 medium 思考档，且输出上限包括推理与回答；[Gemini 3 指南](https://ai.google.dev/gemini-api/docs/gemini-3)建议使用默认温度。其余 3.x 型号的实际思考字段、输入图片和端点要逐项验证。
- DeepSeek：[Responses 参数说明](https://api-docs.deepseek.com/guides/responses_api/)指出 thinking 模式 temperature 不生效；[图片输入说明](https://api-docs.deepseek.com/guides/vision/)列出 `deepseek-flash` 的图像输入。主测省略温度，思考启用且尝试中档，实际受模型/端点可用档位约束。
- 百炼：[Chat 参数说明](https://www.alibabacloud.com/help/en/model-studio/qwen-api-via-openai-chat-completions)对部分 Qwen、Kimi、GLM 提供 `enable_thinking`；[思考指南](https://www.alibabacloud.com/help/en/model-studio/deep-thinking)区分可切换与仅思考型号。字段并不适用于所有服务或模型。当地知识库 `raw/model-user-guide/model-experience/text-generation-model/deep-thinking.md` 亦说明开关有模型条件。具体型号的图片和推理档要实测。
- 智谱/自托管：`zai-org/...` 是模型仓库标识，不自动等于某 API 服务的模型名。其思考开关、采样和图片能力必须按实际服务商及部署版本查询；不能把百炼或 Z.ai 某个型号的设置直接推广。
- 豆包：[火山引擎多模态思考接口](https://docs.volcengine.com/docs/lake-ai-service/multi-modal-machine-learning-deep-thinking-doubao-seed-2?lang=en)介绍 thinking 与 temperature 接口层参数；不据此假定全部字段适用于名单中的指定版本/路由，须实际确认。

## 各模型接入核查

“设置策略”是本项目计划，不是已完成实测；未明确有中档的型号采用服务默认，禁止假装调到了 medium。四家 OpenAI 模型及 Gemini 4 的中档取值来自上述各自官方文档，其余条目若未标明具体支持则需验收。

| 厂商及名单中模型 | 模型/部署标识 | 主测参数策略 | 仍需确认 |
|---|---|---|---|
| OpenAI GPT-6 Astra | `gpt-6-astra` | medium；省略温度 | 账户与具体 API 路由、图像和输出上限 |
| OpenAI GPT-6.1 Sol | `gpt-6.1-sol` | medium；省略温度 | 同上 |
| OpenAI GPT-6.1 Terra | `gpt-6.1-terra` | medium；省略温度 | 同上 |
| OpenAI GPT-6 Luna | `gpt-6-luna` | medium；省略温度 | 同上 |
| Anthropic Claude Fable 5.1 | `claude-fable-5-1` | adaptive；medium 若该型号接口允许，否则默认并记录 | effort 取值、图像、响应格式 |
| Anthropic Claude Opus 5.5 | `claude-opus-5-5` | adaptive；medium 若接口允许，否则默认并记录 | 同上 |
| Anthropic Claude Sonnet 5.5 | `claude-sonnet-5-5` | adaptive；medium 若接口允许，否则默认并记录 | 同上 |
| Anthropic Claude Haiku 5.5 | `claude-haiku-5-5` | adaptive；medium 若接口允许，否则默认并记录 | 同上 |
| Google Gemini 4 Argon | `gemini-4-argon` | thinking level medium；省略采样 | 账户、端点、图像与长输出 |
| Google Gemini 3.8 Flash | `gemini-3.8-flash` | 可用 medium 则设定，否则默认 | 支持档位、图像及调用格式 |
| Google Gemini 3.6 Flash | `gemini-3.6-flash` | 可用 medium 则设定，否则默认 | 同上 |
| Google Gemini 3.1 Pro Preview | `gemini-3.1-pro-preview` | 可用 medium 则设定，否则默认 | 同上；preview 别名变动 |
| DeepSeek V4.1 Flash | `deepseek-flash` | 启用 thinking；有中档则设定，否则默认 | 实际档位、别名、图像与输出限制 |
| Moonshot Kimi K3（百炼） | `kimi-k3` | 仅思考；中档可用时设定，否则默认 | 视觉输入、端点/地区、参数 |
| Moonshot Kimi K2.7 Code（百炼） | `kimi-k2.7-code` | 思考模式；可用中档则设定 | 图像、端点/地区、参数 |
| Moonshot Kimi K2.6（百炼） | `kimi-k2.6` | 支持时启用 thinking；有中档则设定 | 图像、端点/地区、参数 |
| Moonshot Kimi K2.5（百炼） | `kimi-k2.5` | 支持时启用 thinking；有中档则设定 | 图像、端点/地区、参数 |
| 智谱 GLM-5.3-Flash | `zai-org/GLM-5.3-Flash` | 具体服务支持思考时启用，有中档则设定 | 模型 ID 到端点映射、视觉、参数 |
| 智谱 GLM-5V-Turbo | API ID 未冻结 | 同上 | API ID、服务、视觉、参数 |
| 智谱 GLM-4.6V | `zai-org/GLM-4.6V` | 同上 | 模型 ID 到端点映射、视觉、参数 |
| 智谱 GLM-4.6V-Flash | `zai-org/GLM-4.6V-Flash` | 同上 | 模型 ID 到端点映射、视觉、参数 |
| 阿里 Qwen3.8 Max | `qwen3.8-max` | 百炼支持时 enable_thinking=true；中档可用则设定 | 地区、档位、图像和输出限制 |
| 阿里 Qwen3.8 Flash | `qwen3.8-flash` | 同上 | 同上 |
| 阿里 Qwen3.7 Plus | `qwen3.7-plus` | 同上 | 同上 |
| 阿里 Qwen3.7 Flash | `qwen3.7-flash` | 同上 | 同上 |
| 阿里 Qwen3.6 Plus | `qwen3.6-plus` | 同上 | 同上 |
| 阿里 Qwen3.5 Plus | `qwen3.5-plus` | 同上 | 同上 |
| 字节 Doubao Seed 2.1 Pro | `doubao-seed-2-1-pro-260915` | 官方端点支持时思考启用、中档；否则默认 | 快照 ID、参数名、图像、输出限制 |

## 接入验收记录模板

对每个模型保存：服务商与区域、模型请求 ID、响应模型名和快照、日期、图像输入数量/模式、思考参数及其服务实际支持证据、是否遗漏采样参数、输出上限、截断/错误信息、上下文限制、API 限额，以及项目适配器版本。验收可在测试环境人工配置，但不同模型正式主测不得更换相同题的观察和动作接口。不得保存密钥。对不支持中档或部分能力的情况按真实信息记录；不作无证据的自动替代。
