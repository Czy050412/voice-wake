# UE5内嵌Voice 集成指南

## 架构总览

```
[麦克风] → [UE5 Audio Capture] → [WAV字节数组]
                                          ↓
                     VaRest POST → http://127.0.0.1:9876/recognize
                                          ↓
                    voice_server.py (faster-whisper)
                                          ↓
                    返回 JSON {"text": "添加授权"}
                                          ↓
              [蓝图解析] → [匹配命令关键词] → [触发按钮]
```

## 前置条件

1. CIM Manager 项目中已有 `VaRest` 插件 (已确认)
2. `voice_server.py` 在后台运行 (双击 voice_server_start.bat)
3. 确认服务正常: 浏览器打开 http://127.0.0.1:9876/status 应显示 {"status":"ok"}

## UE5蓝图连线（在CIM的UI蓝图中）

### 第一步：添加语音识别组件

在 UI 蓝图中添加:
- `Audio Capture Component` (引擎自带，用于录音)
- 或者用 `VoiceCapture` 系统

### 第二步：录音并发送到服务器

```
Event BeginPlay
  → Start Audio Capture  (启动麦克风)

定时器 或 按键触发:
  → Stop Audio Capture → Get Captured Audio Data → 得到WAV字节数组
  → Send To Voice Server (自定义函数，见下方)
```

### 第三步：Send To Voice Server 函数

```
Send To Voice Server (Input: WAV字节数组)

1. Construct VaRest Request Ext
   - Verb: POST
   - ContentType: x_www_form_urlencoded_url  (二进制数据用这个)
   
2. Set URL
   - Url: "http://127.0.0.1:9876/recognize"

3. Set Binary Request Content
   - Content: [WAV字节数组]

4. Execute Process Request
   → 绑定 OnRequestComplete 事件

5. OnRequestComplete:
   → Get Response Content As String
   → 解析JSON: 用 VaRest 的 Get String Field (FieldName="text")
   → 得到识别文本 string
```

### 第四步：命令匹配与路由

```
识别文本 → Switch On String (或手动 If 判断)

  "添加授权"    → 触发 "添加授权" 按钮的 OnClicked 事件
  "添加新软件"  → 触发 "添加新软件" 按钮
  "刷新状态"    → 触发 "刷新状态" 按钮
  "关闭软件"    → 触发 QuitGame
  "打开设置"    → 打开设置面板
  ...
  default       → PrintString("未识别的命令: " + text)
```

### 第五步：持续监听模式

```
设置一个定时器 (每2-3秒):
  → 录音2秒 → 发送到服务器 → 得到结果 → 匹配命令 → 循环

或者设置语音激活(VAD):
  → 检测到声音开始 → 录音到静音 → 发送 → 匹配
```

## 方案B进阶：一键启动服务

如果想完全一体化（用户不用手动启动voice_server.py），在CIM蓝图的 BeginPlay 中：

```
Event BeginPlay
  → Execute Process (/c "F:\Agent\Claw\voice_wake\voice_server_start.bat")
  → Delay(3秒) 等待服务启动
  → Start Audio Capture
```

## 方案C：去掉HTTP，直接用stdin/stdout管道 (最高效)

如果觉得HTTP开销大，可以改成管道方式：

```python
# voice_pipe.py - 改voice_server.py为stdin/stdout模式
# UE5通过ExecuteProcess启动，stdin写入WAV, stdout读取文本
```

UE5蓝图:
```
Event BeginPlay
  → Create Pipe (命名为 "voice_pipe")
  → Start Process (voice_server.py, stdin/stdout连到pipe)
  → 定时器: 写WAV到stdin → 读stdout文本 → 匹配命令
```

## CIM已有蓝图节点的复用

你已经在CIM Manager中大量使用VaRest，可以直接复制现有模式:

从你的蓝图复制:
- `K2Node_CallFunction_166` - ConstructVaRestRequestExt (PUT → 改为 POST)
- `K2Node_CallFunction_167` - SetURL (alyamkin.com → 改为 127.0.0.1:9876)
- `K2Node_AddDelegate_4` - OnRequestComplete 绑定
- 响应处理回调 - 获取 → 解析 → 执行

## 测试方法

1. 启动 voice_server_start.bat
2. 浏览器打开 http://127.0.0.1:9876/status → 看到 {"status":"ok"}
3. 在CIM中添加蓝图后，对着麦克风说话
4. 查看蓝图 PrintString 输出确认识别到文字
5. 验证命令匹配和按钮触发
