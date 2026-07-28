from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RepositorySource:
  key: str
  url: str
  commit: str
  license_name: str
  license_path: str


@dataclass(frozen=True)
class SelectedDocument:
  repository: str
  category: str
  path: str


REPOSITORIES = {
  "JavaGuide": RepositorySource(
    key="JavaGuide",
    url="https://github.com/Snailclimb/JavaGuide.git",
    commit="8fb36af2bcd92d87c5223214980a9a97ef946f10",
    license_name="Apache-2.0",
    license_path="LICENSE",
  ),
  "advanced-java": RepositorySource(
    key="advanced-java",
    url="https://github.com/doocs/advanced-java.git",
    commit="1659850d7de4739ac9394dddd6c68466a8c38761",
    license_name="CC-BY-SA-4.0",
    license_path="LICENSE",
  ),
}


def _documents(repository: str, category: str, paths: list[str]) -> list[SelectedDocument]:
  return [SelectedDocument(repository, category, path) for path in paths]


SELECTED_DOCUMENTS = [
  *_documents("JavaGuide", "java-basics", [
    "docs/java/basis/java-basic-questions-01.md",
    "docs/java/basis/java-basic-questions-02.md",
    "docs/java/basis/reflection.md",
    "docs/java/basis/serialization.md",
  ]),
  *_documents("JavaGuide", "java-collections", [
    "docs/java/collection/java-collection-questions-01.md",
    "docs/java/collection/java-collection-questions-02.md",
    "docs/java/collection/hashmap-source-code.md",
    "docs/java/collection/concurrent-hash-map-source-code.md",
  ]),
  *_documents("JavaGuide", "juc", [
    "docs/java/concurrent/java-concurrent-questions-01.md",
    "docs/java/concurrent/java-concurrent-questions-02.md",
    "docs/java/concurrent/aqs.md",
    "docs/java/concurrent/reentrantlock.md",
    "docs/java/concurrent/optimistic-lock-and-pessimistic-lock.md",
  ]),
  *_documents("JavaGuide", "jvm", [
    "docs/java/jvm/memory-area.md",
    "docs/java/jvm/jvm-garbage-collection.md",
    "docs/java/jvm/class-loading-process.md",
    "docs/java/jvm/jdk-monitoring-and-troubleshooting-tools.md",
  ]),
  *_documents("JavaGuide", "spring", [
    "docs/system-design/framework/spring/ioc-and-aop.md",
    "docs/system-design/framework/spring/spring-transaction.md",
    "docs/system-design/framework/spring/spring-boot-auto-assembly-principles.md",
    "docs/system-design/framework/spring/spring-design-patterns-summary.md",
  ]),
  *_documents("JavaGuide", "mysql", [
    "docs/database/mysql/mysql-questions-01.md",
    "docs/database/mysql/mysql-index.md",
    "docs/database/mysql/innodb-implementation-of-mvcc.md",
    "docs/database/mysql/transaction-isolation-level.md",
    "docs/database/mysql/mysql-logs.md",
  ]),
  *_documents("JavaGuide", "redis", [
    "docs/database/redis/cache-basics.md",
    "docs/database/redis/redis-persistence.md",
    "docs/database/redis/redis-questions-01.md",
    "docs/database/redis/redis-data-structures-01.md",
  ]),
  *_documents("JavaGuide", "network", [
    "docs/cs-basics/network/application-layer-protocol.md",
    "docs/cs-basics/network/tcp-connection-and-disconnection.md",
    "docs/cs-basics/network/tcp-reliability-guarantee.md",
    "docs/cs-basics/network/http-vs-https.md",
    "docs/cs-basics/network/http1.0-vs-http1.1.md",
  ]),
  *_documents("JavaGuide", "operating-system", [
    "docs/cs-basics/operating-system/process-and-thread.md",
    "docs/cs-basics/operating-system/memory-management.md",
    "docs/cs-basics/operating-system/io-multiplexing.md",
    "docs/cs-basics/operating-system/dead-lock.md",
  ]),
  *_documents("JavaGuide", "distributed", [
    "docs/distributed-system/distributed-lock-implementations.md",
  ]),
  *_documents("advanced-java", "distributed", [
    "docs/distributed-system/distributed-lock-redis-vs-zookeeper.md",
    "docs/distributed-system/distributed-transaction.md",
  ]),
  *_documents("JavaGuide", "message-queue", [
    "docs/high-performance/message-queue/message-queue.md",
    "docs/high-performance/message-queue/kafka-questions-01.md",
  ]),
  *_documents("advanced-java", "message-queue", [
    "docs/high-concurrency/how-to-ensure-the-reliable-transmission-of-messages.md",
  ]),
  *_documents("advanced-java", "system-design", [
    "docs/high-concurrency/high-concurrency-design.md",
    "docs/high-concurrency/redis-caching-avalanche-and-caching-penetration.md",
    "docs/high-availability/e-commerce-website-detail-page-architecture.md",
  ]),
]
