/**
 * 1个reader和多个tags的核心代码
 */
"use strict";

import { v4 as uuidv4 } from "uuid";
import { logColors } from "./logConfig.js";

export class Reader {
  constructor(Q) {
    this.Q = Q ? Q : Reader.generateRandomQ(); // 初始Q值
  }

  handleResponses(res) {
    console.log("Reader received responses:", res);
    // 处理标签的RN16响应
    const rn16List = res.filter((r) => r.type === "RN16").map((r) => r.rn16);

    // 只有一个标签响应时，才进行后续操作
    if (rn16List.length === 1) {
      const rn16 = rn16List[0];
      return { type: "ACK", rn16: rn16 }; // 发送 ACK，包含 RN16
    } else {
      return null;
    }
  }

  // 静态方法（类自身方法，不是实例方法）
  static generateRandomQ() {
    return Math.floor(Math.random() * 8); // 生成0-15之间的随机整数
  }
}

export class Tag {
  constructor(id) {
    this.id = id;
    this.EPC = uuidv4();
    this.PC = 0x3000;
    this.slotCounter = null;
    this.status = "ready"; // 初始态为ready

    this.RN_16 = null;
    this.CRC_16 = null;
    this.hasResponded = false; // 响应
  }

  // 收到 Reader 的 Query(Q)
  onQuery(Q) {
    // 生成 slot counter
    const maxSlot = Math.pow(2, Q);
    this.slotCounter = Math.floor(Math.random() * maxSlot);
  }

  // 收到 Reader 的 QueryRep
  onQueryRep(Q) {
    const maxSlot = Math.pow(2, Q) - 1; // 获取当前Q值的最大slot值，例如Q=4时，maxSlot=15

    if (this.slotCounter === 0) {
      // 翻转情况：从0回到最大值
      this.slotCounter = maxSlot;
    } else {
      // 正常情况：普通减1
      this.slotCounter--;
    }
  }

  // 判断 slot counter 是否为0
  isSlotZero() {
    return this.slotCounter === 0;
  }

  // 响应RN16
  respondRN16() {
    // 当 slot counter 为0时，hasResponded 为true，其它情况为false
    if (this.hasResponded === true && this.RN_16 === null) {
      this.RN_16 = this.generateRN16();
      return { type: "RN16", tagId: this.id, rn16: this.RN_16 };
    }
    return null;
  }

  // 生成 RN16
  generateRN16() {
    return Math.floor(Math.random() * 0x10000); // 16 bit
  }

  // 静态方法（类自身方法，不是实例方法）
  static generateSlot(Q) {
    const numSlots = Math.pow(2, Q);
    return Math.floor(Math.random() * numSlots); // 生成0到2^Q-1之间的随机整数
  }
}

export class Log {
  constructor({ actor, type, message }) {
    this.id = uuidv4();
    this.timestamp = new Date();
    this.time = this.timestamp.toLocaleTimeString();

    this.actor = actor; // 参与者：Reader、Tag、System
    this.type = type;
    this.message = message;
    this.color = this.getColor(this.type);
  }

  getColor(type) {
    return logColors[type.toUpperCase()] || logColors.INFO;
  }
}
