# Premium PPTX QA Checklist

在交付任何 `.pptx` 之前，逐项检查：

## 结构可打开性
- [ ] `python -m markitdown output.pptx` 成功
- [ ] 或 `soffice --headless --convert-to pdf output.pptx` 成功
- [ ] 文件名、路径、扩展名正确

## 内容结构
- [ ] 有封面
- [ ] 有摘要/结论页
- [ ] 有至少 1 页流程/架构/对比页
- [ ] 有结尾/下一步页
- [ ] 标题是结论化表达

## 视觉质量
- [ ] 没有整套全 bullet 页
- [ ] 至少 3 种页面类型
- [ ] 没有明显文本溢出
- [ ] 没有元素重叠
- [ ] 配色统一
- [ ] 主色 / 辅色 / 强调色分工明确
- [ ] 不是普通白底文档感

## 残留项检查
- [ ] 没有 placeholder
- [ ] 没有 lorem ipsum
- [ ] 没有模板残字
- [ ] 页码/顺序正常
