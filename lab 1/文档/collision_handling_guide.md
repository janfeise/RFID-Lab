# RFID协议冲突处理指导文档

## 1. 概述

本文档指导如何实现EPC GEN2协议中的冲突处理机制。当多个标签在同一时刻响应Reader时，会产生冲突。系统需要通过QueryRep指令逐步减少slot counter，使标签轮流响应。

## 2. 冲突场景分析

### 2.1 冲突定义

在RN16响应阶段，如果多个标签同时响应RN16，则产生冲突：

- **检测方式**：`onRN16Response()` 中 `tagsRespond.length > 1`
- **系统反应**：记录冲突错误日志，设置 `protocolState.stage = "COLLISION"`
- **处理策略**：返回step 1，继续发送QueryRep指令

### 2.2 冲突处理流程

```
[发生冲突]
    ↓
[多个Tag响应RN16]
    ↓
[系统检测到 tagsRespond.length > 1]
    ↓
[设置 protocolState.stage = "COLLISION"]
    ↓
[LogicFlow 重置: activeStep = 0, QueryCommand = "onQueryRep"]
    ↓
[发送QueryRep指令]
    ↓
[所有Tag的slotCounter减1]
    ↓
[进入下一轮Query周期]
```

### 2.3 多Tag同时持有slot=0时的详细处理过程

#### 场景说明

当**多个标签同时持有 `slotCounter = 0`** 时，以下情况会发生：

```
[Reader发送Query(Q)]
    ↓
[多个Tag的slotCounter都初始化为0]
    ↓
[这些Tag都进入 hasResponded=true 状态]
    ↓
[Reader发送 "检查slot是否为0" 命令]
    ↓
[系统检测到多个Tag满足 isSlotZero()]
    ↓
[protocolState.hasSlotZero = true（表示"有"slot为0的tag）]
    ↓
[LogicFlow跳转到 RN16响应阶段]
    ↓
[这些Tag都调用 respondRN16()]
    ↓
[Reader同时收到多个RN16]  ← 🚨 冲突发生！
    ↓
[Reader.handleResponses() 检测 tagsRespond.length > 1]
    ↓
[返回 null（不发送ACK）]
    ↓
[系统记录冲突日志]
    ↓
[protocolState.stage = "COLLISION"]
    ↓
[LogicFlow 重置: activeStep = 0, QueryCommand = "onQueryRep"]
    ↓
[回到step 1，发送QueryRep指令（而非Query）]
    ↓
[所有Tag执行onQueryRep()，slotCounter减1]
    ↓
[不同Tag在不同轮次到达slot=0，逐个响应]
```

#### 关键点

1. **多个RN16同时到达**：不同于单独响应的情况
2. **Reader不发送ACK**：Reader检测到冲突后，不对任何Tag发送ACK确认
3. **进入查询循环**：直接回到step 1（Query/QueryRep）而非step 4（ACK）
4. **等待翻转分散**：通过QueryRep的翻转机制，使不同Tag在后续轮次逐个到达slot=0

## 3. Slot Counter循环机制

### 3.1 EPC GEN2协议规定

根据EPC GEN2标准：

> **If slot value = 0000h, then decrementing the slot value causes it to roll over to 7FFFh**

这意味着slot counter具有"环形"计数特性：在减1操作时，如果当前值为0，应该翻转到最大值。

### 3.2 当前实现中的特殊处理需求

当前系统中，slot counter的范围是 **0 到 2^Q-1**，而非固定的0到7FFFh。因此需要特殊处理：

| 参数            | 范围      | 最大值         |
| --------------- | --------- | -------------- |
| Q值             | 1-15      | -              |
| Slot范围 (固定) | 0 ~ 7FFFh | 32767 (2^15-1) |
| Slot范围 (动态) | 0 ~ 2^Q-1 | 根据Q值变化    |

### 3.3 翻转规则

根据EPC GEN2协议，在QueryRep阶段的slot counter减1操作应遵循以下规则：

#### 情形1：正常减1

```
当前 slotCounter > 0 时：
  slotCounter = slotCounter - 1
```

#### 情形2：翻转处理（关键）

```
当前 slotCounter = 0 时：
  slotCounter = 2^Q - 1
```

**说明**：

- 当slot counter为0时，继续减1会导致其翻转到最大值 `2^Q - 1`
- 这确保了slot counter在范围内循环，不会出现负数
- 在二进制表示中，这等同于协议中提到的 "0000h 翻转到 7FFFh"

## 4. 实现指导

### 4.1 Tag类中的QueryRep处理

当前代码：

```javascript
onQueryRep() {
  this.slotCounter--; // slot counter 减1
}
```

**需要改进的地方**：
在 `onQueryRep()` 方法中，需要考虑以下场景：

1. **无冲突的QueryRep**：正常减1
   - 条件：当前只有一个或零个Tag待响应
   - 操作：`slotCounter--`

2. **冲突后的QueryRep**：需要考虑翻转
   - 条件：刚发生冲突，多个Tag同时减1
   - 操作：需要将翻转逻辑集成到减1操作中

### 4.2 翻转实现逻辑（伪代码）

```javascript
onQueryRep(Q) {
  // 获取当前Q值的最大slot值
  const maxSlot = Math.pow(2, Q) - 1;  // 例如Q=4时，maxSlot=15

  if (this.slotCounter === 0) {
    // 翻转情况：从0回到最大值
    this.slotCounter = maxSlot;
  } else {
    // 正常情况：普通减1
    this.slotCounter--;
  }
}
```

### 4.3 协议流程中的集成点

在 **App.vue** 中的 `onQueryRep()` 函数：

```javascript
const onQueryRep = () => {
  resetState();

  tags.forEach((tag) => {
    tag.onQueryRep(config.qValue); // 传递Q值用于翻转计算
    logs.push(
      new Log({
        actor: "READER",
        type: "info",
        message: `Sent QueryRep to Tag ${tag.id}, Tag slot counter--`,
      }),
    );
  });
};
```

需要确保：

- QueryRep操作传递Q值参数
- 每个Tag都正确执行翻转逻辑
- 日志能够记录翻转事件

### 4.4 多Tag冲突时的RN16处理逻辑（核心实现）

#### 4.4.1 Reader端的冲突检测与不响应逻辑

在 **App.vue** 的 `onRN16Response()` 函数中：

```javascript
const onRN16Response = () => {
  const tagsRespond = []; // 收集所有响应RN16的标签

  // 第1步：收集所有满足条件的Tag的RN16响应
  tags.forEach((tag) => {
    const rn16Response = tag.respondRN16();
    if (rn16Response) {
      tagsRespond.push(rn16Response);
    }
  });

  // 第2步：尝试处理RN16响应
  const readerRes = reader.value.handleResponses(tagsRespond);

  // 第3步：判断是否发生冲突
  if (readerRes) {
    // ✅ 正常情况：仅一个Tag响应，Reader发送ACK
    console.log("Reader ACK Response:", readerRes);
    protocolState.stage = "ACK";
    protocolState.readerAcked = false;
    logs.push(
      new Log({
        actor: "READER",
        type: "response",
        message: `Reader ACKs Tag ${tagsRespond[0].tagId} with RN16 ${readerRes.rn16}`,
      }),
    );
  } else if (tagsRespond.length > 1) {
    // 🚨 冲突情况：多个Tag同时响应RN16
    logs.push(
      new Log({
        actor: "SYSTEM",
        type: "error",
        message: `Collision detected! ${tagsRespond.length} tags responded with RN16 simultaneously.`,
      }),
    );
    protocolState.stage = "COLLISION";
    protocolState.readerAcked = false;

    // ⚠️ 关键：Reader不发送ACK，不向任何Tag发送确认
    // 反而进入下一轮QueryRep循环
  } else {
    // 其他情况处理
  }
};
```

**处理流程说明**：

1. **收集RN16**：所有`slotCounter=0`的Tag都会响应RN16
2. **单个Tag情况**：`handleResponses()` 返回ACK信息，Reader发送ACK
3. **多个Tag情况**：`handleResponses()` 返回`null`，Reader不发送任何响应
4. **冲突标记**：设置`protocolState.stage = "COLLISION"`，记录错误日志
5. **回到查询**：不执行ACK动作，而是在下一步回到QueryRep循环

#### 4.4.2 LogicFlow的流程控制

在 **LogicFlow.vue** 的 `handleClick()` 函数中：

```javascript
const handleClick = (step) => {
  if (step.action === "onSlotZero") {
    emit("onSlotZero");

    if (!props.hasSlotZero) {
      // 没有tag的slot counter为0 → 走QueryRep（继续查询）
      activeStep.value = 0; // 回到step 1
      QueryCommand.value = "onQueryRep"; // 切换到QueryRep指令
      return;
    }
  } else if (step.action) {
    emit(step.action);
  }

  // 正常情况下，步骤递增
  if (activeStep.value < steps.value.length - 1) {
    activeStep.value += 1;
  } else {
    activeStep.value = 0;
  }
};
```

**流程解析**：

- `activeStep = 0` → step 1：Query/QueryRep
- `activeStep = 1` → step 2：检查slot是否为0
- `activeStep = 2` → step 3：RN16响应
- `activeStep = 3` → step 4：ACK确认

**冲突处理中的流程跳转**：

```
[step 2] 检查slot是否为0
    ↓
[多个slot=0存在]
    ↓
[emit("onSlotZero")]
    ↓ 在App.vue中检测到冲突
[protocolState.hasSlotZero = true]
    ↓
[watch监听hasSlotZero变化]
    ↓
[activeStep = 2 → RN16阶段]
    ↓
[emit("onRN16Response")]
    ↓ 在App.vue中检测冲突
[多个RN16同时到达]
    ↓
[Reader.handleResponses() → null]
    ↓
[protocolState.stage = "COLLISION"]
    ↓ 下一步点击时
[LogicFlow中处理冲突回跳]
    ↓
[activeStep = 0, QueryCommand = "onQueryRep"]
    ↓
[进入step 1的QueryRep分支]
```

#### 4.4.3 Tag端的RN16响应逻辑

在 **core.js** 的 `Tag` 类中：

```javascript
// 响应RN16
respondRN16() {
  // 只有当Tag处于"待响应"状态，且之前未发送过RN16时，才发送RN16
  if (this.hasResponded === true && this.RN_16 === null) {
    this.RN_16 = this.generateRN16();
    return { type: "RN16", tagId: this.id, rn16: this.RN_16 };
  }
  return null;
}

// 判断是否应进入响应状态
isSlotZero() {
  return this.slotCounter === 0;  // 只判断当前slot是否为0，不关心其他Tag
}
```

**关键理解**：

- 每个Tag独立地检查自己的`slotCounter`
- 当多个Tag同时满足`isSlotZero()`时，它们都会进入`hasResponded=true`状态
- 所有这些Tag都会调用`respondRN16()`，生成各自的RN16并返回
- Reader收集所有RN16，发现有多个时就是冲突

#### 4.4.4 完整的冲突处理时序图

```
时刻          Reader              Tag1              Tag2              Tag3
────────────────────────────────────────────────────────────────────────
T0     [Query(Q=2)]  ──→
         初始slot范围0-3     slot=2           slot=1           slot=0 ✓

T1          |                |               |               [hasResponded=true]
     [slot为0检查]          |               |
     protocolState.
     hasSlotZero=true       |               |

T2          |                |               |               [RN16: 0x5A3B]
     [RN16响应请求]  ──→    |               |
                        slot=2         slot=1        (发送RN16)
                                                     (hasResponded已=true)

T3    [收到RN16] ──┐
      [ 0x5A3B ]  ├─ 多个RN16！
      [ 0x7C9E ]  ┤
      (冲突!)     └─ Reader.handleResponses() → null

T4  [不发ACK]
    [重置为       [slot=2]  [slot=1]  [slot=0→翻转到3]
    QueryRep模式]
    activeStep=0
    QueryCommand=
    "onQueryRep"

T5     [QueryRep]  ──→
       (slot--减)
                     slot=1   slot=0✓  slot=3
                                [hasResponded=true新一轮]

T6      |
   [slot为0检查]         [slot=1]  [slot=0✓]  [slot=3]
   (仍有slot=0)

T7    [RN16响应]
      (这次只有         [slot=1]  [RN16: 0x8D4F]  [slot=3]
      Tag2响应)                  (单独响应)

T8    [发送ACK]
      [给Tag2]
```

#### 4.4.5 冲突流程中的变量状态变化

| 阶段         | protocolState.hasSlotZero | protocolState.stage | tagsRespond.length | Reader响应 |
| ------------ | ------------------------- | ------------------- | ------------------ | ---------- |
| Query后      | `false` (默认)            | `null`              | 0                  | -          |
| 检查slot     | `true` (检测到有slot=0)   | `null`              | 0                  | -          |
| RN16阶段     | `true`                    | `null`              | **2+** (冲突!)     | ❌ null    |
| 冲突检测     | `true`                    | **COLLISION**       | 2+                 | ❌ 不发ACK |
| QueryRep开始 | `false` (重置)            | `null` (重置)       | 0                  | -          |
| 下轮检查     | `true` (新的tag=0)        | `null`              | 0                  | -          |
| 单个RN16     | `true`                    | `null`              | **1** (单独)       | ✅ ACK     |
| ACK发送      | `false` (重置)            | **ACK**             | 1                  | ✅ 已发送  |

## 5. 冲突处理的完整循环示例

假设Q=2，最大slot=3，有3个Tag：

### 初始状态（Query阶段）

```
Tag1: slotCounter = 2
Tag2: slotCounter = 1
Tag3: slotCounter = 0  ← 立即进入响应状态
```

### 第1次QueryRep

```
所有Tag减1：
Tag1: 2 → 1
Tag2: 1 → 0  ← 进入响应状态
Tag3: 0 → 3  ← 翻转到最大值！
```

### 第2次QueryRep

```
Tag1: 1 → 0  ← 进入响应状态
Tag2: 0 → 3  ← 翻转
Tag3: 3 → 2
```

### 第3次QueryRep

```
Tag1: 0 → 3  ← 翻转
Tag2: 3 → 2
Tag3: 2 → 1
```

### 最终状态

每个Tag都会逐个进入slotCounter=0的状态，单独响应RN16，避免冲突。

## 6. 关键注意事项

### 6.1 Q值的动态性

- Q值在Query阶段由Reader动态设置
- 每次新的Query周期，Q值可能改变
- 因此slot的最大值 `2^Q-1` 需要动态计算

### 6.2 翻转与冲突的关系

```
┌─────────────────────────────────────┐
│  冲突原因分析                        │
├─────────────────────────────────────┤
│ 多个Tag同时持有slotCounter=0       │
│              ↓                       │
│ 这些Tag都会在同一时刻响应RN16      │
│              ↓                       │
│ Reader接收到多个RN16 → 冲突        │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  翻转的作用                          │
├─────────────────────────────────────┤
│ 使用翻转机制后，slotCounter循环    │
│              ↓                       │
│ 不同Tag在不同时刻到达slotCounter=0 │
│              ↓                       │
│ 避免多个Tag同时响应                │
└─────────────────────────────────────┘
```

### 6.3 协议规范遵循

- EPC GEN2规范明确要求这种翻转行为
- 不实现翻转会导致某些Tag永远无法响应
- 在高密度场景（多Tag）下，翻转是冲突解决的关键

## 7. 测试场景建议

为验证冲突处理的正确性，建议测试以下场景：

### 场景A：无冲突

- 4个Tag，Q=2，初始slot分别为0,1,2,3
- 预期：第1轮Tag1响应，第2轮Tag2响应...

### 场景B：初始冲突

- 3个Tag，Q=2，初始slot都是0
- 预期：需要3轮QueryRep使所有Tag逐个响应

### 场景C：翻转验证

- 2个Tag，Q=1（slot范围0-1），初始都是0
- 预期：
  - 第1次QueryRep后：都翻转到1
  - 第2次QueryRep后：都回到0
  - 需要进一步碰撞处理

## 8. 日志记录建议

在实现过程中，建议添加以下日志：

```javascript
// 在onQueryRep中
`Tag ${tag.id}: slotCounter ${oldValue} → ${newValue}` +
  (newValue > oldValue ? " [翻转]" : " [正常递减]")
  // 在冲突检测中
  `Collision detected at round ${roundCount}: ${count} tags with slotCounter=0`
  // 在Query阶段
  `Query initiated with Q=${Q}, slot range: 0~${Math.pow(2, Q) - 1}`;
```

## 9. 总结

冲突处理的核心在于：

1. **检测冲突**：多个Tag的RN16同时到达
2. **重置流程**：返回QueryRep循环
3. **执行翻转**：slot counter在0处翻转到2^Q-1
4. **分散响应**：使各Tag在不同周期响应，消除冲突

翻转机制是EPC GEN2协议的关键特性，确保即使出现冲突，系统也能最终识别所有Tag。
