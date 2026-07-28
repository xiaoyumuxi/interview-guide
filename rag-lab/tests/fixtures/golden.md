# Redis

## Stream

PEL 保存已经投递但尚未 ACK 的消息，消费者确认后使用 XACK 删除对应记录。

- 消费者读取消息
- 服务处理消息
- 客户端发送 ACK

```java
stream.acknowledge(messageId);
```

| 字段 | 含义 |
| --- | --- |
| id | 消息编号 |
| owner | 消费者 |

> ACK 失败时记录仍保留在 PEL。

