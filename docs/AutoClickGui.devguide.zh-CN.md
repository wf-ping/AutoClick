# AutoClickGui.py 开发指南（中文）

## 概览

- **用途**：提供一个可视化“圆圈目标点”，并按指定间隔在圆心位置执行鼠标左键点击。
- **窗口**：
  - **CircleWindow**：小圆圈窗口；圆心即点击目标坐标；可拖动定位。
  - **ControlPanel**：操作面板；配置间隔/次数并控制开始/停止/复位/关闭。

## 详细说明

### 1) 圆圈拖动交互（CircleWindow）

- **拖动时效果**：
  - 圆圈颜色变浅
  - 圆心出现十字准星
  - 弹出坐标气泡 `CoordHintWindow` 显示 `X=, Y=`
- **坐标气泡防出屏**：
  - 以圆心为参考点，尝试把气泡放在 NE/NW/SE/SW 四个象限方向之一
  - 选择“出屏惩罚最小”的方向，并做 clamp，确保最终可见
- **贴纸模式（运行中）**：
  - 圆圈变浅、鼠标穿透（不拦截点击）

### 2) 点击逻辑（ControlPanel）

- **点击动作**：
  - 每次点击前先隐藏圆圈，再执行 `pyautogui.moveTo` + `pyautogui.click`，之后再显示圆圈
  - 这样可以保证点击落到下层窗口，不会点到圆圈窗本身
  - 启动/点击前会有一个很短的 `QTimer.singleShot(10, ...)` 延迟，帮助窗口从合成层移除，提升“隐藏后再点”的稳定性
- **停止条件**：
  - 鼠标移出圆心半径 `R` 的范围会触发自动停止
- **点击参数**：
  - 间隔最小 `MIN_INTERVAL_SEC`（当前代码为 0.1 秒）
  - 点击次数：`0` 表示不限

### 3) 圆圈初始/复位位置

- 统一由 `ControlPanel._place_circle_relative_to_panel()` 计算并做屏幕 clamp
- **坐标系**：以操作面板**左上角**为原点（像素）
  - `CIRCLE_OFFSET_X_ZH` / `CIRCLE_OFFSET_Y_ZH`：中文界面下的偏移（x 向右为正，y 向下为正）
  - `CIRCLE_OFFSET_X_EN` / `CIRCLE_OFFSET_Y_EN`：英文界面下的偏移（独立控制，避免因面板宽度变化导致位置不合适）
- 函数内部会做屏幕可见区域 clamp，避免圆圈出屏

### 4) 置顶（📌 铆钉）

- 操作面板右上角为📌铆钉开关（`PinToggle`）
  - **置顶**：📌 竖直
  - **不置顶**：📌 倾斜
  - 悬浮 tooltip 随状态变化
- 切换时通过 `setWindowFlag(WindowStaysOnTopHint, on)` 动态生效

### 5) 语言切换（中/英）

- 默认语言为中文（`LANG_ZH`），可切换为英文（`LANG_EN`）
- 文案统一走 `TRANSLATIONS` 与 `_t(key)`，切换时刷新标题、标签、按钮、状态文案、以及 📌 tooltip
- 语言切换也会影响圆圈偏移：使用对应语言的 `CIRCLE_OFFSET_*_(ZH|EN)` 参数

## 开发指南

### 运行

```bash
python3 AutoClickGui.py
```

## 主要类/函数索引

- `CoordHintWindow`：坐标气泡渲染与尺寸自适应
- `CircleWindow.get_center_screen()`：获取圆心屏幕坐标
- `CircleWindow.set_sticker_mode()`：贴纸模式
- `ControlPanel._start_click()` / `_stop_click()`：开始/停止
- `ControlPanel._place_circle_relative_to_panel()`：圆圈初始/复位位置
- `main()`：面板居中、展示窗口、初始化圆圈位置

