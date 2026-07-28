#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DOMAINS = {
  "redis": [
    ("Redis Stream PEL", "PEL", "XACK"),
    ("缓存穿透", "BloomFilter", "negative-cache"),
    ("缓存击穿", "singleflight", "mutex"),
    ("缓存雪崩", "jitter", "circuit-breaker"),
    ("分布式锁", "Redisson", "watchdog"),
  ],
  "spring": [
    ("Spring 事务传播", "REQUIRES_NEW", "TransactionSynchronization"),
    ("Bean 生命周期", "BeanPostProcessor", "InitializingBean"),
    ("循环依赖", "singletonFactories", "early-reference"),
    ("Spring AI 结构化输出", "StructuredOutputConverter", "retry"),
    ("Web MVC 异常处理", "ControllerAdvice", "ExceptionHandler"),
  ],
  "jvm": [
    ("G1 回收器", "region", "remembered-set"),
    ("ZGC 染色指针", "colored-pointer", "load-barrier"),
    ("类加载双亲委派", "ClassLoader", "parent-delegation"),
    ("JMM 可见性", "happens-before", "volatile"),
    ("虚拟线程", "continuation", "carrier-thread"),
  ],
  "database": [
    ("MVCC", "snapshot", "xmin"),
    ("B+Tree 索引", "page-split", "fanout"),
    ("事务隔离", "repeatable-read", "serialization"),
    ("慢查询分析", "EXPLAIN", "execution-plan"),
    ("连接池", "HikariCP", "maxLifetime"),
  ],
  "concurrency": [
    ("AQS", "state", "CLH-queue"),
    ("ConcurrentHashMap", "CAS", "tree-bin"),
    ("线程池背压", "RejectedExecutionHandler", "bounded-queue"),
    ("CompletableFuture", "CompletionStage", "executor"),
    ("内存屏障", "StoreLoad", "reordering"),
  ],
  "rag": [
    ("Evidence Span", "source-offset", "ground-truth"),
    ("Exact Cosine Search", "dot-product", "L2-normalization"),
    ("Embedding Cache", "SHA-256", "cache-key"),
    ("Structure Chunking", "heading-path", "Markdown-AST"),
    ("Parent Child Retrieval", "child-index", "parent-expansion"),
  ],
  "network": [
    ("TCP 拥塞控制", "cwnd", "slow-start"),
    ("HTTP 缓存", "ETag", "If-None-Match"),
    ("TLS 握手", "ClientHello", "session-resumption"),
    ("DNS 解析", "recursive-resolver", "TTL"),
    ("负载均衡", "consistent-hashing", "health-check"),
  ],
  "messaging": [
    ("消息幂等", "idempotency-key", "deduplication"),
    ("消费者重试", "dead-letter-queue", "backoff"),
    ("顺序消息", "partition-key", "single-consumer"),
    ("事务消息", "outbox-pattern", "relay"),
    ("流量削峰", "buffer", "rate-limit"),
  ],
  "security": [
    ("JWT 校验", "signature", "audience"),
    ("OAuth2 PKCE", "code-verifier", "code-challenge"),
    ("密码存储", "Argon2", "salt"),
    ("CSRF 防护", "SameSite", "csrf-token"),
    ("SQL 注入", "prepared-statement", "parameter-binding"),
  ],
  "observability": [
    ("分布式追踪", "trace-id", "span"),
    ("指标基数", "cardinality", "label"),
    ("结构化日志", "correlation-id", "JSON"),
    ("SLO", "error-budget", "burn-rate"),
    ("采样策略", "head-sampling", "tail-sampling"),
  ],
}


def main() -> None:
  output = ROOT / "data/raw/synthetic-smoke-v1"
  output.mkdir(parents=True, exist_ok=True)
  for domain, topics in DOMAINS.items():
    lines = [f"# {domain.title()} 工程笔记", ""]
    for index, (heading, term_a, term_b) in enumerate(topics, start=1):
      lines.extend([
        f"## {heading}",
        "",
        (
          f"{heading}的第一项机制围绕 `{term_a}` 展开。系统先识别请求的边界与状态，"
          f"再用 {term_a} 保存能够复核的中间信息；这一过程强调确定性、可观测性和失败后恢复，"
          f"避免把隐含状态散落到调用链中。编号 D{index}-A 用于区分本段事实。"
        ),
        "",
        (
          f"{heading}的第二项机制使用 `{term_b}` 处理异常路径。实现会记录输入、决策和最终结果，"
          f"并在重复请求到达时依据 {term_b} 保持一致行为；容量达到阈值后应显式降级，"
          f"而不是静默丢弃数据。编号 D{index}-B 用于区分这一证据。"
        ),
        "",
      ])
    (output / f"{domain}.md").write_text("\n".join(lines), encoding="utf-8")
  print(f"seeded {len(DOMAINS)} documents in {output}")


if __name__ == "__main__":
  main()
