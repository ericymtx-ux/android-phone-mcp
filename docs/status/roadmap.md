# Android Phone MCP 开发进度 (Roadmap)

## ✅ 已完成 (Phase 1 & 2 & 3)

### 基础架构
- [x] **MCP Server**: 基于 `fastmcp` 构建核心服务。
- [x] **Controller**: 封装 `uiautomator2`，实现单例连接管理。
- [x] **Tools**: `connect`, `disconnect`, `tap`, `swipe`, `input_text`, `press_key`。

### 智能感知 (Perception)
- [x] **截图压缩**: 支持 JPEG 压缩和 Resize，适配 VLM Token 限制。
- [x] **Compact XML**: 实现 XML 树裁剪算法，仅保留关键节点和属性。
- [x] **Scale 参数**: 允许 Agent 指定截图缩放比例。

### 智能控制 (Action)
- [x] **UI 选择器**: 实现 `tap_element`，支持通过 Text/ResourceID 点击。
- [x] **坐标归一化**: 实现 `normalize`/`denormalize`，支持 0-1000 坐标系。
- [x] **系统操作**: 实现 `list_apps` (第三方应用列表) 和 `unlock_device`。

### AI 集成 (Integration)
- [x] **Volcengine Client**: 集成火山引擎 API。
- [x] **Prompt Engineering**: 内置 `COMPUTER_USE_DOUBAO` 提示词。
- [x] **Action Parser**: 实现正则解析器，提取 `click`, `type` 等指令。
- [x] **多轮对话**: 实现 `history` 管理和自动修剪 (Max 5 images)。

---

## 🚧 进行中 (In Progress)

- [ ] **端到端测试脚本**: 编写自动化脚本，在真机上验证完整流程。
- [ ] **错误处理增强**: 针对 API 超时、模型幻觉的重试机制。

## 📅 计划中 (Backlog)

### Phase 4: 高级功能
- [ ] **自我反思 (Reflection)**: 当操作失败（截图无变化）时，自动重试或尝试替代方案。
- [ ] **任务宏 (Macros)**: 录制并回放常见操作序列（如“解锁并打开微信”）。
- [ ] **本地 VLM**: 探索集成 `SeeClick` 或 `Qwen-VL` 本地模型，降低延迟和成本。

### Phase 5: 跨平台
- [ ] **Android 模拟器**: 更好的模拟器支持。
- [ ] **iOS 支持**: 探索 `WebDriverAgent` 集成。
