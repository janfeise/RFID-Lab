/**
 * 标签有限状态机 (Tag FSM)
 * 用于管理 RFID 标签在不同命令下的状态转移逻辑
 *
 * 使用示例：
 * ```javascript
 * // 1. 创建状态机实例
 * const tagFSM = new TagFSM();
 *
 * // 2. 创建 tag 对象（包含状态机所需属性）
 * const tag = {
 *   slotCounter: 0,      // 时隙计数器（用于仲裁状态）
 *   RN16: "0x1234",      // 随机数 RN16（用于回复确认）
 *   handle: "0x5678"     // 句柄（用于确认后的操作）
 * };
 *
 * // 3. 创建事件对象（包含命令和必要参数）
 * const event = {
 *   command: TagFSM.COMMANDS.Query,  // 命令类型
 *   RN16: "0x1234",                  // 某些命令需要 RN16
 *   handle: "0x5678"                 // 某些命令需要 handle
 * };
 *
 * // 4. 处理事件
 * const newState = tagFSM.handleEvent(tag, event);
 *
 * // 5. 查询当前状态（可选）
 * const currentState = tagFSM.getCurrentState();
 * ```
 */

// tag FSM

export class TagFSM {
  // 第一段：状态
  static STATES = {
    Ready: "Ready", // 准备状态
    Arbitrate: "Arbitrate", // 仲裁状态
    Reply: "Reply", // 回复状态
    Acknowledged: "Acknowledged", // 确认状态
    Open: "Open", // 开放状态
    Secured: "Secured", // 安全状态
    Killed: "Killed", // 杀死状态
  };

  static COMMANDS = {
    Select: "Select", // 选择命令
    Query: "Query", // 查询命令
    QueryRep: "QueryRep", // 查询回复命令
    QueryAdjust: "QueryAdjust", // 查询调整命令
    ACK: "ACK", // 确认命令
    NAK: "NAK", // 拒绝命令
    Req_RN: "Req_RN", // 请求RN命令
    Read: "Read", // 读命令
    Write: "Write", // 写命令
    Kill: "Kill", // 杀死命令
    Lock: "Lock", // 锁定命令
    Access: "Access", // 访问命令[optional]
  };

  #currentState; // 当前状态，为私有属性

  constructor() {
    this.#currentState = TagFSM.STATES.Ready;
  }

  getCurrentState() {
    return this.#currentState;
  }

  // 第二段：状态逻辑转移，只关心下一个状态
  #nextState(tag, event) {
    switch (this.#currentState) {
      case TagFSM.STATES.Ready:
        if (event.command === TagFSM.COMMANDS.Query) {
          return TagFSM.STATES.Arbitrate; // 进入仲裁状态
        }
        break;

      case TagFSM.STATES.Arbitrate:
        if (
          event.command === TagFSM.COMMANDS.QueryRep &&
          tag.slotCounter === 0
        ) {
          return TagFSM.STATES.Reply; // 进入开放状态
        }
        if (event.command === TagFSM.COMMANDS.Query) {
          return TagFSM.STATES.Arbitrate;
        }
        break;

      case TagFSM.STATES.Reply:
        if (event.command === TagFSM.COMMANDS.ACK && tag.RN16 === event.RN16) {
          return TagFSM.STATES.Acknowledged; // 进入确认状态
        }
        if (
          event.command === TagFSM.COMMANDS.Query ||
          event.command === TagFSM.COMMANDS.Select
        ) {
          return TagFSM.STATES.Ready;
        }
        return TagFSM.STATES.Arbitrate; // RN16不匹配或收到其他指令（如NAK）时回退

      case TagFSM.STATES.Acknowledged:
        if (
          event.command === TagFSM.COMMANDS.Req_RN &&
          event.handle === tag.handle
        ) {
          return TagFSM.STATES.Open; // 进入开放状态
        }
        if (
          event.command === TagFSM.COMMANDS.Select ||
          event.command === TagFSM.COMMANDS.Query ||
          event.command === TagFSM.COMMANDS.QueryRep ||
          event.command === TagFSM.COMMANDS.QueryAdjust
        ) {
          return TagFSM.STATES.Ready; // 进入准备状态
        }
        break;

      case TagFSM.STATES.Open:
        if (event.command === TagFSM.COMMANDS.Access) {
          return TagFSM.STATES.Secured; // 进入安全状态
        }
        if (event.command === TagFSM.COMMANDS.Kill) {
          return TagFSM.STATES.Killed; // 进入杀死状态
        }
        if (
          event.command === TagFSM.COMMANDS.Select ||
          event.command === TagFSM.COMMANDS.Query ||
          event.command === TagFSM.COMMANDS.QueryRep ||
          event.command === TagFSM.COMMANDS.QueryAdjust
        ) {
          return TagFSM.STATES.Ready;
        }
        break;

      case TagFSM.STATES.Secured:
        if (
          event.command === TagFSM.COMMANDS.Select ||
          event.command === TagFSM.COMMANDS.Query ||
          event.command === TagFSM.COMMANDS.QueryRep ||
          event.command === TagFSM.COMMANDS.QueryAdjust
        ) {
          return TagFSM.STATES.Ready;
        }
    }
    return this.#currentState; // 默认保持当前状态
  }

  // 第三段：输出逻辑，由于项目中输出逻辑单独实现，这里不再实现

  // 统一入口：处理事件
  handleEvent(tag, event) {
    const prevState = this.#currentState; // 当前状态

    // 计算下一个状态
    this.#currentState = this.#nextState(tag, event);

    // 打印结果
    console.log(
      `[${prevState}] 事件: ${event.command} -> [${this.#currentState}]`,
    );

    return this.#currentState;
  }
}
