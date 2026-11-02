# 多模态测试模型名单

版本：v1.0｜更新：2026-10-27｜状态：名单已确定；具体服务端点、权限与接口适配待验证。

| 厂商 | 测试模型 | 模型标识或 API 名称 |
|---|---|---|
| OpenAI | GPT-6 Astra | `gpt-6-astra` |
| OpenAI | GPT-6.1 Sol | `gpt-6.1-sol` |
| OpenAI | GPT-6.1 Terra | `gpt-6.1-terra` |
| OpenAI | GPT-6 Luna | `gpt-6-luna` |
| Anthropic | Claude Fable 5.1 | `claude-fable-5-1` |
| Anthropic | Claude Opus 5.5 | `claude-opus-5-5` |
| Anthropic | Claude Sonnet 5.5 | `claude-sonnet-5-5` |
| Anthropic | Claude Haiku 5.5 | `claude-haiku-5-5` |
| Google | Gemini 4 Argon | `gemini-4-argon` |
| Google | Gemini 3.8 Flash | `gemini-3.8-flash` |
| Google | Gemini 3.6 Flash | `gemini-3.6-flash` |
| Google | Gemini 3.1 Pro Preview | `gemini-3.1-pro-preview` |
| DeepSeek | DeepSeek V4.1 Flash | `deepseek-flash` |
| Moonshot AI | Kimi K3 | `kimi-k3`（百炼） |
| Moonshot AI | Kimi K2.7 Code | `kimi-k2.7-code`（百炼，待核实图片接口） |
| Moonshot AI | Kimi K2.6 | `kimi-k2.6`（百炼，待核实图片接口） |
| Moonshot AI | Kimi K2.5 | `kimi-k2.5`（百炼，待核实图片接口） |
| 智谱 / Z.ai | GLM-5.3-Flash | `zai-org/GLM-5.3-Flash`（模型标识） |
| 智谱 / Z.ai | GLM-5V-Turbo | GLM-5V-Turbo（API ID 待核实） |
| 智谱 / Z.ai | GLM-4.6V | `zai-org/GLM-4.6V`（模型标识） |
| 智谱 / Z.ai | GLM-4.6V-Flash | `zai-org/GLM-4.6V-Flash`（模型标识） |
| 阿里云 / Qwen | Qwen3.8 Max | `qwen3.8-max` |
| 阿里云 / Qwen | Qwen3.8 Flash | `qwen3.8-flash` |
| 阿里云 / Qwen | Qwen3.7 Plus | `qwen3.7-plus` |
| 阿里云 / Qwen | Qwen3.7 Flash | `qwen3.7-flash` |
| 阿里云 / Qwen | Qwen3.6 Plus | `qwen3.6-plus` |
| 阿里云 / Qwen | Qwen3.5 Plus | `qwen3.5-plus` |
| 字节跳动 | Doubao Seed 2.1 Pro | `doubao-seed-2-1-pro-260915` |

仅列支持图像输入的模型系列；具体服务端点及实际权限须在正式接入前验证。模型标识不是通用 API ID，不同部署平台的调用名可能不同。DeepSeek 官方 API 当前仅 `deepseek-flash` 支持图像输入，`deepseek-v4-pro` 不支持；旧 Vision 别名已指向同一 Flash 模型，因此不重复计作不同模型。正式运行版本及参数按 [测评协议](evaluation_protocol.md) 登记。

参考：[OpenAI](https://developers.openai.com/api/docs/models)｜[Anthropic](https://platform.claude.com/docs/en/models/overview)｜[Google](https://ai.google.dev/gemini-api/docs/models)｜[DeepSeek](https://api-docs.deepseek.com/quick_start/pricing/)｜[Kimi](https://huggingface.co/moonshotai/models)｜[GLM](https://huggingface.co/zai-org/models)｜[GLM-5V-Turbo](https://arxiv.org/abs/2604.26752)｜[Qwen](https://www.alibabacloud.com/help/en/model-studio/vision-model)｜[豆包](https://docs.volcengine.com/docs/ark/model-list?lang=en)。
