# astrbot-plugin-reply-guard

一个用于 AstrBot 的全局回复净化插件。

## 作用

- 拦截模型偶发输出的英文通用代理占位废话
- 拦截对应的中文占位废话
- 避免这类无意义内容直接发到群聊或私聊

## 默认处理

- 如果整句都是占位废话：替换为配置里的中文提示
- 如果是“占位废话 + 正文”：尽量剥离前缀废话，只保留正文

## 默认拦截示例

- `I am ready to help complete the task and can use the available tools to make progress.`
- `I'm ready to help ... available tools ...`
- `我已准备好帮助完成任务并可以使用取得进展的可用工具。`

## 配置项

- `enabled`: 是否启用插件
- `only_model_result`: 是否只处理模型主回复
- `replacement_text`: 整句命中时替换成的文本
- `strip_prefixed_reply`: 是否尝试剥离前缀废话
- `debug_log_hits`: 命中时是否打印日志

## 说明

这个插件只负责结果清洗，不负责修复模型本身。
如果上游模型频繁输出占位废话，仍建议检查对应模型、代理链或工具调用配置。
