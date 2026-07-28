# java-interview-real-v1 — Dev Human Review

Each item must be approved by a human before the reviewed JSONL is created.

## 1. java_real_candidate_001 — TERMINOLOGY

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** Java 字节码是什么？

**Reference Answer:** 在 Java 中，JVM 可以理解的代码就叫做字节码（即扩展名为 .class 的文件），它不面向任何特定的处理器，只面向虚拟机。Java 语言通过字节码的方式，在一定程度上解决了传统解释型语言执行效率低的问题，同时又保留了解释型语言可移植的特点。

**Evidence 1:** `JavaGuide/docs/java/basis/java-basic-questions-01.md` offset `[3894, 4267)`

在 Java 中，JVM 可以理解的代码就叫做字节码（即扩展名为 `.class` 的文件），它不面向任何特定的处理器，只面向虚拟机。Java 语言通过字节码的方式，在一定程度上解决了传统解释型语言执行效率低的问题，同时又保留了解释型语言可移植的特点。所以， Java 程序运行时相对来说还是高效的（不过，和 C、 C++，Rust，Go 等语言还是有一定差距的），而且，由于字节码并不针对一种特定的机器，因此，Java 程序无须重新编译便可在多种不同操作系统的计算机上运行。

**Java 程序从源代码到运行的过程如下图所示**：

![Java程序转变为机器代码的过程](https://oss.javaguide.cn/github/javaguide/java/basis/java-code-to-machine-code.png)


## 2. java_real_candidate_002 — TERMINOLOGY

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** XA 两阶段提交方案如何协调多个数据库事务？

**Reference Answer:** XA 采用两阶段提交，由事务管理器协调多个数据库资源：先询问各数据库是否就绪，全部同意才统一提交；任一数据库不同意就回滚。

**Evidence 1:** `advanced-java/docs/distributed-system/distributed-transaction.md` offset `[391, 782)`

所谓的 XA 方案，即：两阶段提交，有一个**事务管理器**的概念，负责协调多个数据库（资源管理器）的事务，事务管理器先问问各个数据库你准备好了吗？如果每个数据库都回复 ok，那么就正式提交事务，在各个数据库上执行操作；如果任何其中一个数据库回答不 ok，那么就回滚事务。

这种分布式事务方案，比较适合单块应用里，跨多个库的分布式事务，而且因为严重依赖于数据库层面来搞定复杂的事务，效率很低，绝对不适合高并发的场景。如果要玩儿，那么基于 `Spring + JTA` 就可以搞定，自己随便搜个 demo 看看就知道了。

这个方案，我们很少用，一般来说**某个系统内部如果出现跨多个库**的这么一个操作，是**不合规**的。我可以给大家介绍一下， 现在微服务，一个大的系统分成几十个甚至几百个服务。一般来说，我们的规定和规范，是要求**每个服务只能操作自己对应的一个数据库**。


## 3. java_real_candidate_003 — TERMINOLOGY

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** AQS 是什么，它为同步器提供了哪些通用能力？

**Reference Answer:** AQS 是构建同步器的抽象执行框架，统一定义资源获取与释放流程，具体资源逻辑由同步器重写模板方法实现。

**Evidence 1:** `JavaGuide/docs/java/concurrent/aqs.md` offset `[1263, 1585)`

AQS 解决了开发者在实现同步器时的复杂性问题。它提供了一个通用框架，用于实现各种同步器，例如 **可重入锁**（`ReentrantLock`）、**信号量**（`Semaphore`）和 **倒计时器**（`CountDownLatch`）。通过封装底层的线程同步机制，AQS 将复杂的线程管理逻辑隐藏起来，使开发者只需专注于具体的同步逻辑。

简单来说，AQS 是一个抽象类，为同步器提供了通用的 **执行框架**。它定义了 **资源获取和释放的通用流程**，而具体的资源获取逻辑则由具体同步器通过重写模板方法来实现。 因此，可以将 AQS 看作是同步器的 **基础“底座”**，而同步器则是基于 AQS 实现的 **具体“应用”**。


## 4. java_real_candidate_004 — TERMINOLOGY

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** 什么是 Condition？

**Reference Answer:** Condition 是 java.util.concurrent.locks 包中定义的接口，它提供了类似于 Object.wait() / Object.notify() 的线程等待/通知机制，但功能更加强大和灵活。支持多个等待队列：一个 Lock 可以创建多个 Condition 实例，不同的线程可以在不同的条件上等待，实现更精细的线程协作。

**Evidence 1:** `JavaGuide/docs/java/concurrent/aqs.md` offset `[39653, 40150)`

`Condition` 是 `java.util.concurrent.locks` 包中定义的接口，它提供了类似于 `Object.wait()` / `Object.notify()` 的线程等待/通知机制，但功能更加强大和灵活。`Condition` 必须与 `Lock` 配合使用，就像 `wait/notify` 必须与 `synchronized` 配合使用一样。

与 `Object` 的 `wait/notify` 相比，`Condition` 的主要优势在于：

- **支持多个等待队列**：一个 `Lock` 可以创建多个 `Condition` 实例，不同的线程可以在不同的条件上等待，实现更精细的线程协作。而 `synchronized` 只有一个等待队列。
- **支持不响应中断的等待**：`Condition` 提供了 `awaitUninterruptibly()` 方法。
- **支持超时等待**：`Condition` 提供了 `awaitNanos(long)` 和 `await(long, TimeUnit)` 方法，可以设定等待的截止时间。



## 5. java_real_candidate_005 — TERMINOLOGY

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** TCC 分布式事务中的 Try、Confirm、Cancel 分别做什么？

**Reference Answer:** Try 用于检测并锁定或预留各服务的资源，Confirm 执行实际操作，Cancel 在服务出错时补偿并回滚已成功的业务逻辑。

**Evidence 1:** `advanced-java/docs/distributed-system/distributed-transaction.md` offset `[1030, 1463)`

TCC 的全称是： `Try` 、 `Confirm` 、 `Cancel` 。

-   Try 阶段：这个阶段说的是对各个服务的资源做检测以及对资源进行**锁定或者预留**。
-   Confirm 阶段：这个阶段说的是在各个服务中**执行实际的操作**。
-   Cancel 阶段：如果任何一个服务的业务方法执行出错，那么这里就需要**进行补偿**，就是执行已经执行成功的业务逻辑的回滚操作。（把那些执行成功的回滚）

这种方案说实话几乎很少人使用，我们用的也比较少，但是也有使用的场景。因为这个**事务回滚**实际上是**严重依赖于你自己写代码来回滚和补偿**了，会造成补偿代码巨大，非常之恶心。

比如说我们，一般来说跟**钱**相关的，跟钱打交道的，**支付**、**交易**相关的场景，我们会用 TCC，严格保证分布式事务要么全部成功，要么全部自动回滚，严格保证资金的正确性，保证在资金上不会出现问题。

而且最好是你的各个业务执行的时间都比较短。


## 6. java_real_candidate_006 — TERMINOLOGY

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** AQS 的 Exclusive 和 Share 两种资源共享模式分别是什么？

**Reference Answer:** Exclusive 是独占模式，同一时刻只有一个线程执行，ReentrantLock 是典型例子；Share 是共享模式，允许多个线程同时执行，例如 Semaphore 和 CountDownLatch。

**Evidence 1:** `JavaGuide/docs/java/concurrent/aqs.md` offset `[8692, 8967)`

AQS 定义两种资源共享方式：`Exclusive`（独占，只有一个线程能执行，如 `ReentrantLock`）和 `Share`（共享，多个线程可同时执行，如 `Semaphore`/`CountDownLatch`）。

一般来说，自定义同步器的共享方式要么是独占，要么是共享，他们也只需实现 `tryAcquire-tryRelease`、`tryAcquireShared-tryReleaseShared` 中的一种即可。但 AQS 也支持自定义同步器同时实现独占和共享两种方式，如 `ReentrantReadWriteLock`。


## 7. java_real_candidate_009 — TERMINOLOGY

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** IoC 和依赖注入 DI 是什么关系？

**Reference Answer:** IoC 是把对象创建控制权交给第三方容器的设计思想，依赖注入 DI 是 IoC 最常见、最合理的实现方式。

**Evidence 1:** `JavaGuide/docs/system-design/framework/spring/ioc-and-aop.md` offset `[1954, 2458)`

IoC（Inverse of Control:控制反转）是一种设计思想或者说是某种模式。这个设计思想就是 **将原本在程序中手动创建对象的控制权交给第三方比如 IoC 容器。** 对于我们常用的 Spring 框架来说， IoC 容器实际上就是个 Map（key，value）,Map 中存放的是各种对象。不过，IoC 在其他语言中也有应用，并非 Spring 特有。

IoC 最常见以及最合理的实现方式叫做依赖注入（Dependency Injection，简称 DI）。

老马（Martin Fowler）在一篇文章中提到将 IoC 改名为 DI，原文如下，原文地址：<https://martinfowler.com/articles/injection.html> 。

![](https://oss.javaguide.cn/github/javaguide/system-design/framework/spring/martin-fowler-injection.png)

老马的大概意思是 IoC 太普遍并且不表意，很多人会因此而迷惑，所以，使用 DI 来精确指名这个模式比较好。


## 8. java_real_candidate_013 — TERMINOLOGY

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** TCP SACK 是什么，它怎样减少不必要的重传？

**Reference Answer:** SACK 是选择性确认，用来补充累积 ACK 无法表达乱序已收区间的问题。它在 ACK 选项中报告已收到的非连续字节区间，使发送方只重传真正缺失的数据。

**Evidence 1:** `JavaGuide/docs/cs-basics/network/tcp-reliability-guarantee.md` offset `[6413, 6962)`

SACK（Selective Acknowledgment，选择性确认）用来补足累积 ACK 的信息盲区。普通 ACK 只能表达“某个序号之前的数据都收到了”，但无法表达“后面的某些区间虽然乱序，也已经收到了”。SACK 会在 ACK 的 TCP 选项里携带已经收到的非连续字节区间，帮助发送方只重传真正缺失的部分。

SACK 需要在三次握手时通过 SACK-Permitted 选项协商。启用后，ACK 号本身仍然遵循累积确认规则，SACK 选项额外携带一个或多个 SACK block。每个 SACK block 由 Left Edge 和 Right Edge 组成，表示接收方已经收到的字节区间 `[Left Edge, Right Edge)`。

举个例子：发送方连续发送 `[0, 1000)`、`[1000, 2000)`、`[2000, 3000)`、`[3000, 4000)`，其中 `[1000, 2000)` 丢失，但后面两段已经到达。接收方的累计 ACK 仍然只能停在 ACK = 1000，但它可以在 SACK 里报告已经收到 `[2000, 4000)`。发送方据此就知道 `[1000, 2000)` 需要重传，而 `[2000, 4000)` 不必重复发送。


## 9. java_real_candidate_016 — TERMINOLOGY

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** 什么是覆盖索引？

**Reference Answer:** 如果一个索引包含（或者说覆盖）所有需要查询的字段的值，我们就称之为 覆盖索引（Covering Index）。覆盖索引即需要查询的字段正好是索引的字段，那么直接根据该索引，就可以查到数据了，而无需回表查询。

**Evidence 1:** `JavaGuide/docs/database/mysql/mysql-questions-01.md` offset `[17605, 17822)`

如果一个索引包含（或者说覆盖）所有需要查询的字段的值，我们就称之为 **覆盖索引（Covering Index）**。

在 InnoDB 存储引擎中，非主键索引的叶子节点包含的是主键的值。这意味着，当使用非主键索引进行查询时，数据库会先找到对应的主键值，然后再通过主键索引来定位和检索完整的行数据。这个过程被称为“回表”。

**覆盖索引即需要查询的字段正好是索引的字段，那么直接根据该索引，就可以查到数据了，而无需回表查询。**


## 10. java_real_candidate_020 — TERMINOLOGY

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** Kafka 里的 Producer、Consumer、Broker、Topic 和 Partition 分别是什么？

**Reference Answer:** Producer 产生消息，Consumer 消费消息，Broker 是独立的 Kafka 实例；Topic 是消息主题，Partition 是 Topic 的分区，一个 Topic 可以跨多个 Broker 分布多个 Partition。

**Evidence 1:** `JavaGuide/docs/high-performance/message-queue/kafka-questions-01.md` offset `[2499, 3196)`

Kafka 将生产者发布的消息发送到 **Topic（主题）** 中，需要这些消息的消费者可以订阅这些 **Topic（主题）**，如下图所示：

![](https://oss.javaguide.cn/github/javaguide/high-performance/message-queue20210507200944439.png)

上面这张图也为我们引出了，Kafka 比较重要的几个概念：

1. **Producer（生产者）** : 产生消息的一方。
2. **Consumer（消费者）** : 消费消息的一方。
3. **Broker（代理）** : 可以看作是一个独立的 Kafka 实例。多个 Kafka Broker 组成一个 Kafka Cluster。

同时，你一定也注意到每个 Broker 中又包含了 Topic 以及 Partition 这两个重要的概念：

- **Topic（主题）** : Producer 将消息发送到特定的主题，Consumer 通过订阅特定的 Topic(主题) 来消费消息。
- **Partition（分区）** : Partition 属于 Topic 的一部分。一个 Topic 可以有多个 Partition ，并且同一 Topic 下的 Partition 可以分布在不同的 Broker 上，这也就表明一个 Topic 可以横跨多个 Broker 。这正如我上面所画的图一样。

> 划重点：**Kafka 中的 Partition（分区） 实际上可以对应成为消息队列中的队列。这样是不是更好理解一点？**


## 11. java_real_candidate_022 — TERMINOLOGY

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** AMQP 是什么？

**Reference Answer:** AMQP，即 Advanced Message Queuing Protocol，一个提供统一消息服务的应用层标准 高级消息队列协议（二进制应用层协议），是应用层协议的一个开放标准，为面向消息的中间件设计，兼容 JMS。RabbitMQ 就是基于 AMQP 协议实现的。

**Evidence 1:** `JavaGuide/docs/high-performance/message-queue/message-queue.md` offset `[6767, 6962)`

AMQP，即 Advanced Message Queuing Protocol，一个提供统一消息服务的应用层标准 **高级消息队列协议**（二进制应用层协议），是应用层协议的一个开放标准，为面向消息的中间件设计，兼容 JMS。基于此协议的客户端与消息中间件可传递消息，并不受客户端/中间件同产品，不同的开发语言等条件的限制。

**RabbitMQ 就是基于 AMQP 协议实现的。**


## 12. java_real_candidate_024 — TERMINOLOGY

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** PCB 是什么？

**Reference Answer:** PCB（Process Control Block，进程控制块）是操作系统管理进程的数据结构。进程运行时的许多信息不会散落在空气里，而是由内核放在类似 PCB 的结构里维护。

**Evidence 1:** `JavaGuide/docs/cs-basics/operating-system/process-and-thread.md` offset `[2490, 2977)`

PCB（Process Control Block，进程控制块）是操作系统管理进程的数据结构。进程运行时的许多信息不会散落在空气里，而是由内核放在类似 PCB 的结构里维护。

PCB 通常记录：

- 进程标识信息：PID、父进程 ID、用户 ID 等。
- 进程状态和调度信息：就绪、运行、阻塞、优先级、时间统计。
- CPU 上下文：程序计数器、栈指针、通用寄存器等，方便切换回来继续执行。
- 内存管理信息：页表、虚拟地址空间、内存映射。
- 资源信息：打开文件、信号处理、工作目录、I/O 状态等。

发生上下文切换时，操作系统会把当前执行实体的寄存器等现场保存起来，再恢复下一个执行实体的现场。PCB/TCB 这类结构就是“下次从哪儿继续跑”的依据。

Linux 的实现有一点特别：它把进程和线程都看成 task，`task_struct` 里并不直接塞进所有资源，而是通过指针指向内存描述符、文件表、信号处理等资源结构。多个线程属于同一进程时，它们会指向同一批资源结构；不同进程则指向不同资源。这也是 Linux 上理解 `clone()` 很有用的原因。


## 13. java_real_candidate_026 — PARAPHRASE

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** AOT 的主要收益和使用代价是什么？

**Reference Answer:** AOT 对冷启动和内存敏感的应用更有吸引力，但会增加构建时间、元数据维护和兼容性适配成本。

**Evidence 1:** `JavaGuide/docs/java/basis/java-basic-questions-01.md` offset `[9089, 9507)`

Spring 使用 AOT 处理来适配这种执行方式。它会在构建阶段分析应用上下文，生成 Java 源码、代理字节码以及反射、资源和代理所需的 `RuntimeHints`。CGLIB 通常借助 ASM 在运行时生成代理类；到了 Native Image 场景，这类工作可以提前到构建阶段完成。框架或应用提供相应的构建期适配后，Spring、CGLIB 和 ASM 仍可参与 AOT 应用的构建与运行。具体机制可以参考 [Spring AOT 官方文档](https://docs.spring.io/spring-framework/reference/core/aot.html)。

AOT 把一部分运行时工作和信息搬到了构建阶段，同时增加了构建时间、元数据维护和兼容性适配成本。对于依赖运行时动态加载、Java Agent 或大量动态字节码生成的应用，JIT 模式通常更省事；对于冷启动和内存占用敏感的应用，AOT 更有吸引力。


## 14. java_real_candidate_027 — PARAPHRASE

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** Saga 事务里某个参与者失败后，已经提交的本地事务怎么处理？

**Reference Answer:** Saga 会对失败前已经成功的参与者执行补偿，并按相反顺序调用相应的补偿服务，把这些本地事务造成的数据修改补偿掉。

**Evidence 1:** `advanced-java/docs/distributed-system/distributed-transaction.md` offset `[1759, 1970)`

业务流程中每个参与者都提交本地事务，若某一个参与者失败，则补偿前面已经成功的参与者。下图左侧是正常的事务流程，当执行到 T3 时发生了错误，则开始执行右边的事务补偿流程，反向执行 T3、T2、T1 的补偿服务 C3、C2、C1，将 T3、T2、T1 已经修改的数据补偿掉。

![distributed-transacion-TCC](./images/distributed-transaction-saga.png)


## 15. java_real_candidate_028 — PARAPHRASE

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** 小型电商商品详情页为什么适合做全量静态化，典型请求链路是什么？

**Reference Answer:** 可以把数据库中的商品数据填入模板生成静态 HTML，再推送到 Nginx。用户访问时直接返回静态页，不执行数据库交互和业务代码，因此速度和性能较高，适合页面数量较少的小型网站。

**Evidence 1:** `advanced-java/docs/high-availability/e-commerce-website-detail-page-architecture.md` offset `[39, 643)`

小型电商网站的页面展示采用页面全量静态化的思想。数据库中存放了所有的商品信息，页面静态化系统，将数据填充进静态模板中，形成静态化页面，推入 Nginx 服务器。用户浏览网站页面时，取用一个已经静态化好的 html 页面，直接返回回去，不涉及任何的业务逻辑处理。

![e-commerce-website-detail-page-architecture-1](./images/e-commerce-website-detail-page-architecture-1.png)

下面是页面模板的简单 Demo 。

```html
<html>
    <body>
        商品名称：#{productName}<br />
        商品价格：#{productPrice}<br />
        商品描述：#{productDesc}
    </body>
</html>
```

这样做，**好处**在于，用户每次浏览一个页面，不需要进行任何的跟数据库的交互逻辑，也不需要执行任何的代码，直接返回一个 html 页面就可以了，速度和性能非常高。

对于小网站，页面很少，很实用，非常简单，Java 中可以使用 velocity、freemarker、thymeleaf 等等，然后做个 cms 页面内容管理系统，模板变更的时候，点击按钮或者系统自动化重新进行全量渲染。


## 16. java_real_candidate_029 — PARAPHRASE

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** 为什么浮点数运算的时候会有精度丢失的风险？

**Reference Answer:** 计算机使用有限位宽的二进制格式表示 float 和 double，许多十进制小数转换为二进制后会无限循环，只能舍入为有限位数，因此存在精度损失的风险。不过，像 0.5、0.25 这样能够表示为有限二进制小数的值可以被精确表示。

**Evidence 1:** `JavaGuide/docs/java/basis/java-basic-questions-01.md` offset `[30752, 31421)`

浮点数运算精度丢失代码演示：

```java
float a = 2.0f - 1.9f;
float b = 1.8f - 1.7f;
System.out.printf("%.9f",a);// 0.100000024
System.out.println(b);// 0.099999905
System.out.println(a == b);// false
```

**为什么会出现这个问题呢？**

这个和计算机保存浮点数的机制有很大关系。计算机使用有限位宽的二进制格式表示 `float` 和 `double`，许多十进制小数转换为二进制后会无限循环，只能舍入为有限位数，因此存在精度损失的风险。不过，像 0.5、0.25 这样能够表示为有限二进制小数的值可以被精确表示。

就比如说十进制下的 0.2 就没办法精确转换成二进制小数：

```java
// 0.2 转换为二进制数的过程为，不断乘以 2，直到不存在小数为止，
// 在这个计算过程中，得到的整数部分从上到下排列就是二进制的结果。
0.2 * 2 = 0.4 -> 0
0.4 * 2 = 0.8 -> 0
0.8 * 2 = 1.6 -> 1
0.6 * 2 = 1.2 -> 1
0.2 * 2 = 0.4 -> 0（发生循环）
...
```

关于浮点数的更多内容，建议看一下[计算机系统基础（四）浮点数](http://kaito-kidd.com/2018/08/08/computer-system-float-point/)这篇文章。


## 17. java_real_candidate_031 — PARAPHRASE

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** 静态方法为什么不能调用非静态成员？

**Reference Answer:** 静态方法在静态上下文中执行，没有隐式的当前实例 this，因此不能直接访问实例成员。静态方法仍然可以通过一个显式的对象引用访问该对象的实例成员，这与类加载或成员是否已经“分配内存”无关。

**Evidence 1:** `JavaGuide/docs/java/basis/java-basic-questions-01.md` offset `[35971, 36459)`

静态方法在静态上下文中执行，没有隐式的当前实例 `this`，因此不能直接访问实例成员。静态方法仍然可以通过一个显式的对象引用访问该对象的实例成员，这与类加载或成员是否已经“分配内存”无关。

```java
public class Example {
    // 定义一个字符型常量
    public static final char LETTER_A = 'A';

    // 定义一个字符串常量
    public static final String GREETING_MESSAGE = "Hello, world!";

    public static void main(String[] args) {
        // 输出字符型常量的值
        System.out.println("字符型常量的值为：" + LETTER_A);

        // 输出字符串常量的值
        System.out.println("字符串常量的值为：" + GREETING_MESSAGE);
    }
}
```


## 18. java_real_candidate_032 — PARAPHRASE

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** Java 方法重载和重写的核心区别是什么？

**Reference Answer:** 重载是在同一方法名下根据不同输入选择处理；重写是子类覆盖从父类继承的同签名方法。

**Evidence 1:** `JavaGuide/docs/java/basis/java-basic-questions-01.md` offset `[37128, 37214)`

> 重载就是同样的一个方法能够根据输入数据的不同，做出不同的处理
>
> 重写就是当子类继承自父类的相同方法，输入数据一样，但要做出有别于父类的响应时，你就要覆盖父类方法


## 19. java_real_candidate_035 — PARAPHRASE

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** Java 集合相比数组主要灵活在哪里？

**Reference Answer:** Java 集合大小可变、支持泛型并带有内建算法，能够更灵活地存储和处理数量不确定的数据。

**Evidence 1:** `JavaGuide/docs/java/collection/java-collection-questions-01.md` offset `[2863, 3147)`

当我们需要存储一组类型相同的数据时，数组是最常用且最基本的容器之一。但是，使用数组存储对象存在一些不足之处，因为在实际开发中，存储的数据类型多种多样且数量不确定。这时，Java 集合就派上用场了。与数组相比，Java 集合提供了更灵活、更有效的方法来存储多个数据对象。Java 集合框架中的各种集合类和接口可以存储不同类型和数量的对象，同时还具有多样化的操作方式。相较于数组，Java 集合的优势在于它们的大小可变、支持泛型、具有内建算法等。总的来说，Java 集合提高了数据的存储和处理灵活性，可以更好地适应现代软件开发中多样化的数据需求，并支持高质量的代码编写。


## 20. java_real_candidate_036 — PARAPHRASE

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** 高并发写入场景下，MQ 怎么帮助 MySQL 控制压力？

**Reference Answer:** 先把大量写请求放入 MQ 排队，再由下游系统异步、逐步消费并写入 MySQL，把写入速度控制在 MySQL 的承载范围内，从而提升整体并发能力。

**Evidence 1:** `advanced-java/docs/high-concurrency/high-concurrency-design.md` offset `[1510, 1803)`

MQ，必须得用 MQ。可能你还是会出现高并发写的场景，比如说一个业务操作里要频繁搞数据库几十次，增删改增删改，疯了。那高并发绝对搞挂你的系统，你要是用 redis 来承载写那肯定不行，人家是缓存，数据随时就被 LRU 了，数据格式还无比简单，没有事务支持。所以该用 mysql 还得用 mysql 啊。那你咋办？用 MQ 吧，大量的写请求灌入 MQ 里，排队慢慢玩儿，**后边系统消费后慢慢写**，控制在 mysql 承载范围之内。所以你得考虑考虑你的项目里，那些承载复杂写业务逻辑的场景里，如何用 MQ 来异步写，提升并发性。MQ 单机抗几万并发也是 ok 的，这个之前还特意说过。


## 21. java_real_candidate_037 — PARAPHRASE

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** RabbitMQ 消费者拿到消息后进程崩溃，怎么避免消息被当成已消费而丢失？

**Reference Answer:** 关闭自动 ack，只在业务处理完成后显式确认。若消费者在处理完成前崩溃，因为没有 ack，RabbitMQ 会认为消息尚未处理并把它交给其他消费者。

**Evidence 1:** `advanced-java/docs/high-concurrency/how-to-ensure-the-reliable-transmission-of-messages.md` offset `[4223, 4767)`

RabbitMQ 如果丢失了数据，主要是因为你消费的时候，**刚消费到，还没处理，结果进程挂了**，比如重启了，那么就尴尬了，RabbitMQ 认为你都消费了，这数据就丢了。

这个时候得用 RabbitMQ 提供的 `ack` 机制，简单来说，就是你必须关闭 RabbitMQ 的自动 `ack` ，可以通过一个 api 来调用就行，然后每次你自己代码里确保处理完的时候，再在程序里 `ack` 一把。这样的话，如果你还没处理完，不就没有 `ack` 了？那 RabbitMQ 就认为你还没处理完，这个时候 RabbitMQ 会把这个消费分配给别的 consumer 去处理，消息是不会丢的。

> 为了保证消息从队列中可靠地到达消费者，RabbitMQ 提供了消息确认机制。消费者在声明队列时，可以指定 noAck 参数，当 noAck=false，RabbitMQ 会等待消费者显式发回 ack 信号后，才从内存（和磁盘，如果是持久化消息）中移去消息。否则，一旦消息被消费者消费，RabbitMQ 会在队列中立即删除它。

![rabbitmq-message-lose-solution](./images/rabbitmq-message-lose-solution.png)


## 22. java_real_candidate_038 — PARAPHRASE

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** HashMap 和 HashSet 的核心区别是什么？

**Reference Answer:** HashMap 实现 Map 接口并存储键值对；HashSet 实现 Set 接口、只存对象，底层基于 HashMap 实现。

**Evidence 1:** `JavaGuide/docs/java/collection/java-collection-questions-02.md` offset `[2450, 3537)`

如果你看过 `HashSet` 源码的话就应该知道：`HashSet` 底层就是基于 `HashMap` 实现的。（`HashSet` 的源码非常非常少，因为除了 `clone()`、`writeObject()`、`readObject()` 是 `HashSet` 自己不得不实现之外，其他方法都是直接调用 `HashMap` 中的方法。

|               `HashMap`                |                                                        `HashSet`                                                         |
| :------------------------------------: | :----------------------------------------------------------------------------------------------------------------------: |
|           实现了 `Map` 接口            |                                                     实现 `Set` 接口                                                      |
|               存储键值对               |                                                        仅存储对象                                                        |
|     调用 `put()`向 map 中添加元素      |                                           调用 `add()`方法向 `Set` 中添加元素                                            |
| `HashMap` 使用键（Key）计算 `hashcode` | `HashSet` 使用成员对象来计算 `hashcode` 值，对于两个对象来说 `hashcode` 可能相同，所以`equals()`方法用来判断对象的相等性 |


## 23. java_real_candidate_039 — PARAPHRASE

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** JDK 8 的 HashMap 什么时候把冲突链表转成红黑树，数组较小时为什么不直接树化？

**Reference Answer:** 链表长度达到默认阈值 8 后会进入 treeifyBin 判断；只有数组长度至少为 64 才转成红黑树，否则先扩容数组，以减少哈希冲突。

**Evidence 1:** `JavaGuide/docs/java/collection/hashmap-source-code.md` offset `[2059, 2390)`

相比于之前的版本，JDK1.8 以后在解决哈希冲突时有了较大的变化。

当链表长度大于阈值（默认为 8）时，会首先调用 `treeifyBin()` 方法。这个方法会根据 HashMap 数组来决定是否转换为红黑树。只有当数组长度大于或者等于 64 的情况下，才会执行转换红黑树操作，以减少搜索时间。否则，就是只是执行 `resize()` 方法对数组扩容。相关源码这里就不贴了，重点关注 `treeifyBin()` 方法即可！

![jdk1.8之后的内部结构-HashMap](https://oss.javaguide.cn/github/javaguide/java/collection/jdk1.8_hashmap.png)

**类的属性：**


## 24. java_real_candidate_040 — PARAPHRASE

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** ArrayBlockingQueue 和 LinkedBlockingQueue 在存储结构、容量与锁设计上有什么区别？

**Reference Answer:** ArrayBlockingQueue 基于数组、创建时必须指定容量且生产消费共用一把锁；LinkedBlockingQueue 基于链表、容量可选，并将生产锁与消费锁分离。

**Evidence 1:** `JavaGuide/docs/java/collection/java-collection-questions-01.md` offset `[20942, 21562)`

`ArrayBlockingQueue` 和 `LinkedBlockingQueue` 是 Java 并发包中常用的两种阻塞队列实现，它们都是线程安全的。不过，不过它们之间也存在下面这些区别：

- 底层实现：`ArrayBlockingQueue` 基于数组实现，而 `LinkedBlockingQueue` 基于链表实现。
- 是否有界：`ArrayBlockingQueue` 是有界队列，必须在创建时指定容量大小。`LinkedBlockingQueue` 创建时可以不指定容量大小，默认是 `Integer.MAX_VALUE`，也就是无界的。但也可以指定队列大小，从而成为有界的。
- 锁是否分离： `ArrayBlockingQueue` 中的锁是没有分离的，即生产和消费用的是同一个锁；`LinkedBlockingQueue` 中的锁是分离的，即生产用的是 `putLock`，消费是 `takeLock`，这样可以防止生产者和消费者线程之间的锁争夺。
- 内存占用：`ArrayBlockingQueue` 需要提前分配数组内存，而 `LinkedBlockingQueue` 则是动态分配链表节点内存。这意味着，`ArrayBlockingQueue` 在创建时就会占用一定的内存空间，且往往申请的内存比实际所用的内存更大，而 `LinkedBlockingQueue` 则是根据元素的增加而逐渐占用内存空间。



## 25. java_real_candidate_042 — PARAPHRASE

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** CLH 锁为什么用队列组织竞争线程？

**Reference Answer:** CLH 把竞争线程排入队列，让线程监控前驱节点而非直接争抢共享变量，从而按序获取锁并降低 CAS 长期失败造成的饥饿风险。

**Evidence 1:** `JavaGuide/docs/java/concurrent/aqs.md` offset `[1614, 1990)`

CLH 锁是一种基于 **自旋锁** 的优化实现。

先说一下自旋锁存在的问题：自旋锁通过线程不断对一个原子变量执行 `compareAndSet`（简称 `CAS`）操作来尝试获取锁。在高并发场景下，多个线程会同时竞争同一个原子变量，容易造成某个线程的 `CAS` 操作长时间失败，从而导致 **“饥饿”问题**（某些线程可能永远无法获取锁）。

CLH 锁通过引入一个队列来组织并发竞争的线程，对自旋锁进行了改进：

- 每个线程会作为一个节点加入到队列中，并通过自旋监控前一个线程节点的状态，而不是直接竞争共享变量。
- 线程按顺序排队，确保公平性，从而避免了 “饥饿” 问题。

AQS（AbstractQueuedSynchronizer）在 CLH 锁的基础上进一步优化，形成了其内部的 **CLH 队列变体**。主要改进点有以下两方面：


## 26. java_real_candidate_043 — PARAPHRASE

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** Java 平台线程和虚拟线程分别由谁调度？

**Reference Answer:** 平台线程通常以 1:1 方式映射到操作系统线程并由操作系统调度；虚拟线程由 JVM 调度，多个虚拟线程可以复用较少的平台线程。

**Evidence 1:** `JavaGuide/docs/java/concurrent/java-concurrent-questions-01.md` offset `[1669, 2166)`

早期 JDK 曾使用绿色线程（Green Threads）实现用户级线程。后来，HotSpot 中通过 `new Thread()` 创建的传统线程采用平台线程（Platform Thread）实现，平台线程通常以 1:1 方式映射到操作系统线程，由操作系统负责调度。Java 21 正式引入的虚拟线程（Virtual Thread）则由 JVM 调度，大量虚拟线程可以复用较少的平台线程作为载体，因此不能再把所有 Java 线程都等同于操作系统线程。

我们上面提到了用户线程和内核线程，考虑到很多读者不太了解二者的区别，这里简单介绍一下：

- 用户线程：由用户空间程序管理和调度的线程，运行在用户空间（专门给应用程序使用）。
- 内核线程：由操作系统内核管理和调度的线程，运行在内核空间（只有内核程序可以访问）。

顺便简单总结一下用户线程和内核线程的区别和特点：用户级线程通常由运行时在用户空间调度，创建和切换成本较低；能否利用多核取决于用户线程与内核线程之间的映射模型，多对一模型不能并行利用多核，多对多模型则可以。内核线程由操作系统调度，创建和切换成本通常更高，可以直接利用多核。


## 27. java_real_candidate_044 — PARAPHRASE

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** 为什么 wait() 方法不定义在 Thread 中？

**Reference Answer:** wait() 是让获得对象锁的线程实现等待，会自动释放当前线程占有的对象锁。每个对象（Object）都拥有对象锁，既然要释放当前线程占有的对象锁并让其进入 WAITING 状态，自然是要操作对应的对象（Object）而非当前的线程（Thread）。

**Evidence 1:** `JavaGuide/docs/java/concurrent/java-concurrent-questions-01.md` offset `[6505, 6725)`

`wait()` 是让获得对象锁的线程实现等待，会自动释放当前线程占有的对象锁。每个对象（`Object`）都拥有对象锁，既然要释放当前线程占有的对象锁并让其进入 WAITING 状态，自然是要操作对应的对象（`Object`）而非当前的线程（`Thread`）。

类似的问题：**为什么 `sleep()` 方法定义在 `Thread` 中？**

因为 `sleep()` 是让当前线程暂停执行，不涉及到对象类，也不需要获得对象锁。


## 28. java_real_candidate_045 — PARAPHRASE

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** 单核 CPU 上多线程一定更高效吗？

**Reference Answer:** 不一定。CPU 密集型任务会因频繁切换增加开销；IO 密集型任务可在等待 IO 时让其他线程使用 CPU，因此可能提高效率。

**Evidence 1:** `JavaGuide/docs/java/concurrent/java-concurrent-questions-01.md` offset `[8530, 8965)`

单核 CPU 同时运行多个线程的效率是否会高，取决于线程的类型和任务的性质。一般来说，有两种类型的线程：

1. **CPU 密集型**：CPU 密集型的线程主要进行计算和逻辑处理，需要占用大量的 CPU 资源。
2. **IO 密集型**：IO 密集型的线程主要进行输入输出操作，如读写文件、网络通信等，需要等待 IO 设备的响应，而不占用太多的 CPU 资源。

在单核 CPU 上，同一时刻只能有一个线程在运行，其他线程需要等待 CPU 的时间片分配。如果线程是 CPU 密集型的，那么多个线程同时运行会导致频繁的线程切换，增加了系统的开销，降低了效率。如果线程是 IO 密集型的，那么多个线程同时运行可以利用 CPU 在等待 IO 时的空闲时间，提高了效率。

因此，对于单核 CPU 来说，如果任务是 CPU 密集型的，那么开很多线程会影响效率；如果任务是 IO 密集型的，那么开很多线程会提高效率。当然，这里的“很多”也要适度，不能超过系统能够承受的上限。


## 29. java_real_candidate_049 — PARAPHRASE

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** JVM 如何判断一个类是否属于无用类？

**Reference Answer:** 一个类需同时满足三个条件：实例已全部回收、加载它的 ClassLoader 已回收、对应的 Class 对象不再被引用。

**Evidence 1:** `JavaGuide/docs/java/jvm/jvm-garbage-collection.md` offset `[10953, 11253)`

方法区主要回收的是无用的类，那么如何判断一个类是无用的类的呢？

判定一个常量是否是“废弃常量”比较简单，而要判定一个类是否是“无用的类”的条件则相对苛刻许多。类需要同时满足下面 3 个条件才能算是 **“无用的类”**：

- 该类所有的实例都已经被回收，也就是 Java 堆中不存在该类的任何实例。
- 加载该类的 `ClassLoader` 已经被回收。
- 该类对应的 `java.lang.Class` 对象没有在任何地方被引用，无法在任何地方通过反射访问该类的方法。

虚拟机可以对满足上述 3 个条件的无用类进行回收，这里说的仅仅是“可以”，而并不是和对象一样不使用了就会必然被回收。


## 30. java_real_candidate_051 — PARAPHRASE

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** AOP 为什么叫面向切面编程？

**Reference Answer:** AOP 之所以叫面向切面编程，是因为它的核心思想就是将横切关注点从核心业务逻辑中分离出来，形成一个个的切面（Aspect）。

**Evidence 1:** `JavaGuide/docs/system-design/framework/spring/ioc-and-aop.md` offset `[2821, 3038)`

AOP 之所以叫面向切面编程，是因为它的核心思想就是将横切关注点从核心业务逻辑中分离出来，形成一个个的**切面（Aspect）**。

![面向切面编程图解](https://oss.javaguide.cn/github/javaguide/system-design/framework/spring/aop-program-execution.jpg)

这里顺带总结一下 AOP 关键术语（不理解也没关系，可以继续往下看）：


## 31. java_real_candidate_060 — PARAPHRASE

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** Redis 6.0 之前的主要操作为什么保持单线程？

**Reference Answer:** 主要原因是单线程更易维护，Redis 的瓶颈主要在内存和网络，而且多线程可能引入死锁、上下文切换等额外成本。

**Evidence 1:** `JavaGuide/docs/database/redis/redis-questions-01.md` offset `[19076, 19737)`

虽然说 Redis 是单线程模型，但实际上，**Redis 在 4.0 之后的版本中就已经加入了对多线程的支持。**

不过，Redis 4.0 增加的多线程主要是针对一些大键值对的删除操作的命令，使用这些命令就会使用主线程之外的其他线程来“异步处理”，从而减少对主线程的影响。

为此，Redis 4.0 之后新增了几个异步命令：

- `UNLINK`：可以看作是 `DEL` 命令的异步版本。
- `FLUSHALL ASYNC`：用于清空所有数据库的所有键，不限于当前 `SELECT` 的数据库。
- `FLUSHDB ASYNC`：用于清空当前 `SELECT` 数据库中的所有键。

![redis4.0 more thread](https://oss.javaguide.cn/github/javaguide/database/redis/redis4.0-more-thread.png)

总的来说，直到 Redis 6.0 之前，Redis 的主要操作仍然是单线程处理的。

**那 Redis6.0 之前为什么不使用多线程？** 我觉得主要原因有 3 点：

- 单线程编程容易并且更容易维护；
- Redis 的性能瓶颈不在 CPU，主要在内存和网络；
- 多线程就会存在死锁、线程上下文切换等问题，甚至会影响性能。

相关阅读：[为什么 Redis 选择单线程模型？](https://draveness.me/whys-the-design-redis-single-thread/)。


## 32. java_real_candidate_066 — DIRECT_FACT

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** 列举几项 Java 语言的典型特点。

**Reference Answer:** Java 语法相对简单，支持面向对象和平台无关运行，并具备异常处理、自动内存管理、安全防护及 JIT 优化等能力。

**Evidence 1:** `JavaGuide/docs/java/basis/java-basic-questions-01.md` offset `[312, 876)`

1. 简单易学（语法简单，上手容易）；
2. 面向对象（封装，继承，多态）；
3. 平台无关性（Java 虚拟机实现平台无关性）；
4. 支持多线程（C++ 语言没有内置的多线程机制，因此必须调用操作系统的多线程功能来进行多线程程序设计，而 Java 语言却提供了多线程支持）；
5. 可靠性（具备异常处理和自动内存管理机制）；
6. 安全性（Java 语言本身的设计就提供了多重安全防护机制如访问权限修饰符、限制程序直接访问操作系统资源）；
7. 高效性（通过 Just In Time 编译器等技术的优化，Java 语言的运行效率还是非常不错的）；
8. 支持网络编程并且很方便；
9. 编译与解释并存；
10. ……

> **🐛 修正（参见：[issue#544](https://github.com/Snailclimb/JavaGuide/issues/544)）**：C++11 开始（2011 年的时候），C++ 就引入了多线程库，在 Windows、Linux、macOS 都可以使用 `std::thread` 和 `std::async` 来创建线程。参考链接：<http://www.cplusplus.com/reference/thread/thread/?kw=thread>

🌈 拓展一下：


## 33. java_real_candidate_069 — DIRECT_FACT

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** 超过 long 范围的整数在 Java 中如何表示？

**Reference Answer:** 可以使用 BigInteger 表示超过 long 范围的整数；它用 int 数组保存任意大小的整型数据，但运算效率低于常规整数类型。

**Evidence 1:** `JavaGuide/docs/java/basis/java-basic-questions-01.md` offset `[32117, 32410)`

基本数值类型都有一个表达范围，如果超过这个范围就会有数值溢出的风险。

在 Java 中，64 位 long 整型是最大的整数类型。

```java
long l = Long.MAX_VALUE;
System.out.println(l + 1); // -9223372036854775808
System.out.println(l + 1 == Long.MIN_VALUE); // true
```

`BigInteger` 内部使用 `int[]` 数组来存储任意大小的整形数据。

相对于常规整数类型的运算来说，`BigInteger` 运算的效率会相对较低。


## 34. java_real_candidate_070 — DIRECT_FACT

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** 数据库读写分离的基本做法是什么，读压力继续升高时怎么办？

**Reference Answer:** 采用主从架构，让主库处理写入、从库承担读取；当读流量继续增大时，可以增加更多从库来分摊。

**Evidence 1:** `advanced-java/docs/high-concurrency/high-concurrency-design.md` offset `[1927, 2034)`

读写分离，这个就是说大部分时候数据库可能也是读多写少，没必要所有请求都集中在一个库上吧，可以搞个主从架构，**主库写**入，**从库读**取，搞一个读写分离。**读流量太多**的时候，还可以**加更多的从库**。


## 35. java_real_candidate_071 — DIRECT_FACT

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** 静态方法和实例方法在调用方式与直接访问成员方面有何不同？

**Reference Answer:** 静态方法可通过类名直接调用，无需创建对象；实例方法要通过对象调用。静态方法不能直接访问实例成员，但获得对象引用后可以通过该对象访问；实例方法没有这一直接访问限制。

**Evidence 1:** `JavaGuide/docs/java/basis/java-basic-questions-01.md` offset `[36483, 37107)`

**1、调用方式**

在外部调用静态方法时，可以使用 `类名.方法名` 的方式，也可以使用 `对象.方法名` 的方式，而实例方法只有后面这种方式。也就是说，**调用静态方法可以无需创建对象**。

不过，需要注意的是一般不建议使用 `对象.方法名` 的方式来调用静态方法。这种方式非常容易造成混淆，静态方法不属于类的某个对象而是属于这个类。

因此，一般建议使用 `类名.方法名` 的方式来调用静态方法。

```java
public class Person {
    public void method() {
      //......
    }

    public static void staicMethod(){
      //......
    }
    public static void main(String[] args) {
        Person person = new Person();
        // 调用实例方法
        person.method();
        // 调用静态方法
        Person.staicMethod()
    }
}
```

**2、访问类成员是否存在限制**

静态方法在访问本类的成员时，只允许访问静态成员（即静态成员变量和静态方法），不允许访问实例成员（即实例成员变量和实例方法），而实例方法不存在这个限制。


## 36. java_real_candidate_079 — DIRECT_FACT

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** ArrayDeque 和 LinkedList 用作队列时有哪些区别？

**Reference Answer:** ArrayDeque 基于可变长数组和双指针且不支持 null；LinkedList 基于链表并支持 null。通常用 ArrayDeque 实现队列性能更好。

**Evidence 1:** `JavaGuide/docs/java/collection/java-collection-questions-01.md` offset `[18786, 19201)`

`ArrayDeque` 和 `LinkedList` 都实现了 `Deque` 接口，两者都具有队列的功能，但两者有什么区别呢？

- `ArrayDeque` 是基于可变长的数组和双指针来实现，而 `LinkedList` 则通过链表来实现。

- `ArrayDeque` 不支持存储 `NULL` 数据，但 `LinkedList` 支持。

- `ArrayDeque` 是在 JDK1.6 才被引入的，而 `LinkedList` 早在 JDK1.2 时就已经存在。

- `ArrayDeque` 插入时可能存在扩容过程, 不过均摊后的插入操作依然为 O(1)。虽然 `LinkedList` 不需要扩容，但是每次插入数据时均需要申请新的堆空间，均摊性能相比更慢。

从性能的角度上，选用 `ArrayDeque` 来实现队列要比 `LinkedList` 更好。此外，`ArrayDeque` 也可以用于实现栈。


## 37. java_real_candidate_080 — DIRECT_FACT

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** 选用 Map、Set 和 List 时分别要考虑哪些需求？

**Reference Answer:** 需要按键取值时选 Map：要排序可用 TreeMap，不排序可用 HashMap，需要线程安全可用 ConcurrentHashMap。只存元素值时选 Collection：要求元素唯一就选 Set，如 TreeSet 或 HashSet；不要求唯一就选 List，如 ArrayList 或 LinkedList，再结合各实现特点选择。

**Evidence 1:** `JavaGuide/docs/java/collection/java-collection-questions-01.md` offset `[2557, 2848)`

我们主要根据集合的特点来选择合适的集合。比如：

- 我们需要根据键值获取到元素值时就选用 `Map` 接口下的集合，需要排序时选择 `TreeMap`,不需要排序时就选择 `HashMap`,需要保证线程安全就选用 `ConcurrentHashMap`。
- 我们只需要存放元素值时，就选择实现 `Collection` 接口的集合，需要保证元素唯一时选择实现 `Set` 接口的集合比如 `TreeSet` 或 `HashSet`，不需要就选择实现 `List` 接口的比如 `ArrayList` 或 `LinkedList`，然后再根据实现这些接口的集合的特点来选用。



## 38. java_real_candidate_081 — DIRECT_FACT

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** Kafka 作为流处理平台提供哪三项关键能力，主要用于哪两类场景？

**Reference Answer:** Kafka 提供消息流发布订阅、容错持久化存储和流式处理三项能力，主要用于构建实时消息管道，以及构建转换或处理数据流的实时处理程序。

**Evidence 1:** `JavaGuide/docs/high-performance/message-queue/kafka-questions-01.md` offset `[388, 691)`

Kafka 是一个分布式流式处理平台。这到底是什么意思呢？

流平台具有三个关键功能：

1. **消息队列**：发布和订阅消息流，这个功能类似于消息队列，这也是 Kafka 也被归类为消息队列的原因。
2. **容错的持久方式存储记录消息流**：Kafka 会把消息持久化到磁盘，有效避免了消息丢失的风险。
3. **流式处理平台：** 在消息发布的时候进行处理，Kafka 提供了一个完整的流式处理类库。

Kafka 主要有两大应用场景：

1. **消息队列**：建立实时流数据管道，以可靠地在系统或应用程序之间获取数据。
2. **数据处理：** 构建实时的流数据处理程序来转换或处理数据流。



## 39. java_real_candidate_083 — DIRECT_FACT

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** BlockingQueue 常见实现类有哪些？

**Reference Answer:** 常见实现包括 ArrayBlockingQueue、LinkedBlockingQueue、PriorityBlockingQueue、SynchronousQueue 和 DelayQueue。

**Evidence 1:** `JavaGuide/docs/java/collection/java-collection-questions-01.md` offset `[20244, 20885)`

![BlockingQueue 的实现类](https://oss.javaguide.cn/github/javaguide/java/collection/blocking-queue-hierarchy.png)

Java 中常用的阻塞队列实现类有以下几种：

1. `ArrayBlockingQueue`：使用数组实现的有界阻塞队列。在创建时需要指定容量大小，并支持公平和非公平两种方式的锁访问机制。
2. `LinkedBlockingQueue`：使用单向链表实现的可选有界阻塞队列。在创建时可以指定容量大小，如果不指定则默认为 `Integer.MAX_VALUE`。和 `ArrayBlockingQueue` 不同的是， 它仅支持非公平的锁访问机制。
3. `PriorityBlockingQueue`：支持优先级排序的无界阻塞队列。元素必须实现 `Comparable` 接口或者在构造函数中传入 `Comparator` 对象，并且不能插入 null 元素。
4. `SynchronousQueue`：同步队列，是一种不存储元素的阻塞队列。每个插入操作都必须等待对应的删除操作，反之删除操作也必须等待插入操作。因此，`SynchronousQueue` 通常用于线程之间的直接传递数据。
5. `DelayQueue`：延迟队列，其中的元素只有到了其指定的延迟时间，才能够从队列中出队。
6. ……

日常开发中，这些队列使用的其实都不多，了解即可。


## 40. java_real_candidate_088 — DIRECT_FACT

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** Java 线程生命周期包含哪些状态？

**Reference Answer:** Java 线程有 NEW、RUNNABLE、BLOCKED、WAITING、TIMED_WAITING 和 TERMINATED 六种状态。

**Evidence 1:** `JavaGuide/docs/java/concurrent/java-concurrent-questions-01.md` offset `[4036, 4684)`

Java 线程在运行的生命周期中的指定时刻只可能处于下面 6 种不同状态的其中一个状态：

- NEW: 初始状态，线程被创建出来但没有被调用 `start()`。
- RUNNABLE: 运行状态，线程被调用了 `start()` 等待运行的状态。
- BLOCKED：阻塞状态，需要等待锁释放。
- WAITING：等待状态，表示该线程需要等待其他线程做出一些特定动作（通知或中断）。
- TIMED_WAITING：超时等待状态，可以在指定的时间后自行返回而不是像 WAITING 那样一直等待。
- TERMINATED：终止状态，表示该线程已经运行完毕。

线程在生命周期中并不是固定处于某一个状态而是随着代码的执行在不同状态之间切换。

Java 线程状态变迁图(图源：[挑错 |《Java 并发编程的艺术》中关于线程状态的三处错误](https://mp.weixin.qq.com/s/0UTyrJpRKaKhkhHcQtXAiA))：

![Java 线程状态变迁图](https://oss.javaguide.cn/github/javaguide/java/concurrent/640.png)

由上图可以看出：线程创建之后它将处于 **NEW（新建）** 状态，调用 `start()` 方法后开始运行，线程这时候处于 **READY（可运行）** 状态。可运行状态的线程获得了 CPU 时间片（timeslice）后就处于 **RUNNING（运行）** 状态。


## 41. java_real_candidate_089 — DIRECT_FACT

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** 可以直接调用 Thread 类的 run 方法吗？

**Reference Answer:** start() 会执行线程的相应准备工作，然后自动执行 run() 方法的内容，这是真正的多线程工作。但是，直接执行 run() 方法，会把 run() 方法当成一个普通方法在调用该方法的线程去执行，所以这并不是多线程工作。

**Evidence 1:** `JavaGuide/docs/java/concurrent/java-concurrent-questions-01.md` offset `[6757, 7083)`

这是另一个非常经典的 Java 多线程面试问题，而且在面试中会经常被问到。很简单，但是很多人都会答不上来！

new 一个 `Thread`，线程进入了新建状态。调用 `start()` 方法，会启动一个线程并使线程进入了就绪状态，当分配到时间片后就可以开始运行了。 `start()` 会执行线程的相应准备工作，然后自动执行 `run()` 方法的内容，这是真正的多线程工作。 但是，直接执行 `run()` 方法，会把 `run()` 方法当成一个普通方法在调用该方法的线程去执行，所以这并不是多线程工作。

**总结：调用 `start()` 方法方可启动线程并使线程进入就绪状态，直接执行 `run()` 方法的话不会以多线程的方式执行。**


## 42. java_real_candidate_090 — DIRECT_FACT

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** 单核 CPU 支持 Java 多线程吗？

**Reference Answer:** 单核 CPU 是支持 Java 多线程的。尽管单核 CPU 一次只能执行一个任务，但通过快速在多个线程之间切换，可以让用户感觉多个任务是同时进行的。

**Evidence 1:** `JavaGuide/docs/java/concurrent/java-concurrent-questions-01.md` offset `[7984, 8391)`

单核 CPU 是支持 Java 多线程的。操作系统通过时间片轮转的方式，将 CPU 的时间分配给不同的线程。尽管单核 CPU 一次只能执行一个任务，但通过快速在多个线程之间切换，可以让用户感觉多个任务是同时进行的。

这里顺带提一下 Java 使用的线程调度方式。

操作系统主要通过两种线程调度方式来管理多线程的执行：

- **抢占式调度（Preemptive Scheduling）**：操作系统决定何时暂停当前正在运行的线程，并切换到另一个线程执行。这种切换通常是由系统时钟中断（时间片轮转）或其他高优先级事件（如 I/O 操作完成）触发的。这种方式存在上下文切换开销，但公平性和 CPU 资源利用率较好，不易阻塞。
- **协同式调度（Cooperative Scheduling）**：线程执行完毕后，主动通知系统切换到另一个线程。这种方式可以减少上下文切换带来的性能开销，但公平性较差，容易阻塞。



## 43. java_real_candidate_096 — DIRECT_FACT

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** JVM 如何判断字符串常量已经废弃？

**Reference Answer:** 如果字符串常量池中的字符串已没有任何 String 对象引用，它就属于废弃常量，内存回收时可能被清理。

**Evidence 1:** `JavaGuide/docs/java/jvm/jvm-garbage-collection.md` offset `[10276, 10933)`

字符串常量池主要回收的是废弃的常量。那么，我们如何判断一个常量是废弃常量呢？

~~**JDK1.7 及之后版本的 JVM 已经将运行时常量池从方法区中移了出来，在 Java 堆（Heap）中开辟了一块区域存放运行时常量池。**~~

> **🐛 修正（参见：[issue747](https://github.com/Snailclimb/JavaGuide/issues/747)，[reference](https://blog.csdn.net/q5706503/article/details/84640762)）**：
>
> 1. **JDK1.7 之前运行时常量池逻辑包含字符串常量池存放在方法区, 此时 hotspot 虚拟机对方法区的实现为永久代**
> 2. **JDK1.7 字符串常量池被从方法区拿到了堆中, 这里没有提到运行时常量池，也就是说字符串常量池被单独拿到堆，运行时常量池剩下的东西还在方法区, 也就是 hotspot 中的永久代**。
> 3. **JDK1.8 hotspot 移除了永久代用元空间(Metaspace)取而代之, 这时候字符串常量池还在堆, 运行时常量池还在方法区, 只不过方法区的实现从永久代变成了元空间(Metaspace)**

假如在字符串常量池中存在字符串 "abc"，如果当前没有任何 String 对象引用该字符串常量的话，就说明常量 "abc" 就是废弃常量，如果这时发生内存回收的话而且有必要的话，"abc" 就会被系统清理出常量池了。


## 44. java_real_candidate_097 — DIRECT_FACT

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** JVM 类加载包含哪些主要阶段？

**Reference Answer:** 类加载主要经历加载、连接、初始化三步，其中连接又分为验证、准备和解析。

**Evidence 1:** `JavaGuide/docs/java/jvm/class-loading-process.md` offset `[505, 923)`

**Class 文件需要加载到虚拟机中之后才能运行和使用，那么虚拟机是如何加载这些 Class 文件呢？**

系统加载 Class 类型的文件主要三步：**加载->连接->初始化**。连接过程又可分为三步：**验证->准备->解析**。

![类加载过程](https://oss.javaguide.cn/github/javaguide/java/jvm/class-loading-procedure.png)

详见 [Java Virtual Machine Specification - 5.3. Creation and Loading](https://docs.oracle.com/javase/specs/jvms/se8/html/jvms-5.html#jvms-5.3 "Java Virtual Machine Specification - 5.3. Creation and Loading")。


## 45. java_real_candidate_100 — DIRECT_FACT

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** 数据库事务的 ACID 特性分别是什么？

**Reference Answer:** ACID 分别是原子性、一致性、隔离性和持久性：事务不可分割，执行前后数据保持一致，并发事务相互隔离，提交后的改变能够持久保存。

**Evidence 1:** `JavaGuide/docs/system-design/framework/spring/spring-transaction.md` offset `[1614, 2163)`

1. **原子性**（`Atomicity`）：事务是最小的执行单位，不允许分割。事务的原子性确保动作要么全部完成，要么完全不起作用；
2. **一致性**（`Consistency`）：执行事务前后，数据保持一致，例如转账业务中，无论事务是否成功，转账者和收款人的总额应该是不变的；
3. **隔离性**（`Isolation`）：并发访问数据库时，一个用户的事务不被其他事务所干扰，各并发事务之间数据库是独立的；
4. **持久性**（`Durability`）：一个事务被提交之后。它对数据库中数据的改变是持久的，即使数据库发生故障也不应该对其有任何影响。

🌈 这里要额外补充一点：**只有保证了事务的持久性、原子性、隔离性之后，一致性才能得到保障。也就是说 A、I、D 是手段，C 是目的！** 想必大家也和我一样，被 ACID 这个概念被误导了很久! 我也是看周志明老师的公开课[《周志明的软件架构课》](https://time.geekbang.org/opencourse/intro/100064201)才搞清楚的（多看好书！！！）。

![AID->C](https://oss.javaguide.cn/github/javaguide/mysql/AID->C.png)


## 46. java_real_candidate_101 — DIRECT_FACT

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** @Transactional 可以标注在方法、类和接口的哪些位置？

**Reference Answer:** @Transactional 推荐标在方法上；标在类上会让符合代理可见性规则的方法应用相同事务语义；接口上虽可标注但不推荐。

**Evidence 1:** `JavaGuide/docs/system-design/framework/spring/spring-transaction.md` offset `[17726, 17916)`

1. **方法**：推荐将注解使用于方法上。Spring 6 的类代理默认还支持 `protected` 和包可见方法；接口代理要求方法是接口中定义的 `public` 方法。较早版本的代理模式通常只支持 `public` 方法。
2. **类**：如果这个注解使用在类上，表明该类中符合上述代理可见性规则的方法都应用相同的事务语义。
3. **接口**：不推荐在接口上使用。



## 47. java_real_candidate_103 — DIRECT_FACT

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** RabbitMQ 要同时做哪两项持久化配置，才能在重启后恢复队列和消息？

**Reference Answer:** 创建队列时要把 queue 设置为持久化，发送消息时还要把 deliveryMode 设为 2；两项同时开启后，RabbitMQ 重启可从磁盘恢复队列及其数据。

**Evidence 1:** `advanced-java/docs/high-concurrency/how-to-ensure-the-reliable-transmission-of-messages.md` offset `[3562, 4085)`

就是 RabbitMQ 自己弄丢了数据，这个你必须**开启 RabbitMQ 的持久化**，就是消息写入之后会持久化到磁盘，哪怕是 RabbitMQ 自己挂了，**恢复之后会自动读取之前存储的数据**，一般数据不会丢。除非极其罕见的是，RabbitMQ 还没持久化，自己就挂了，**可能导致少量数据丢失**，但是这个概率较小。

设置持久化有**两个步骤**：

-   创建 queue 的时候将其设置为持久化。这样就可以保证 RabbitMQ 持久化 queue 的元数据，但是它是不会持久化 queue 里的数据的。

-   第二个是发送消息的时候将消息的 `deliveryMode` 设置为 2。就是将消息设置为持久化的，此时 RabbitMQ 就会将消息持久化到磁盘上去。

必须要同时设置这两个持久化才行，RabbitMQ 哪怕是挂了，再次重启，也会从磁盘上重启恢复 queue，恢复这个 queue 里的数据。

注意，哪怕是你给 RabbitMQ 开启了持久化机制，也有一种可能，就是这个消息写到了 RabbitMQ 中，但是还没来得及持久化到磁盘上，结果不巧，此时 RabbitMQ 挂了，就会导致内存里的一点点数据丢失。


## 48. java_real_candidate_106 — DIRECT_FACT

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** InnoDB 的当前读和快照读有什么区别？

**Reference Answer:** 快照读读取行的历史版本，不因记录上的排他锁而等待；当前读会对行记录加共享锁或排他锁。

**Evidence 1:** `JavaGuide/docs/database/mysql/mysql-questions-01.md` offset `[31835, 32381)`

**快照读**（一致性非锁定读）就是单纯的 `SELECT` 语句，但不包括下面这两类 `SELECT` 语句：

```sql
SELECT ... FOR UPDATE
# 共享锁 可以在 MySQL 5.7 和 MySQL 8.0 中使用
SELECT ... LOCK IN SHARE MODE;
# 共享锁 可以在 MySQL 8.0 中使用
SELECT ... FOR SHARE;
```

快照即记录的历史版本，每行记录可能存在多个历史版本（多版本技术）。

快照读的情况下，如果读取的记录正在执行 UPDATE/DELETE 操作，读取操作不会因此去等待记录上 X 锁的释放，而是会去读取行的一个快照。

只有在事务隔离级别 RC(读取已提交) 和 RR（可重读）下，InnoDB 才会使用一致性非锁定读：

- 在 RC 级别下，对于快照数据，一致性非锁定读总是读取被锁定行的最新一份快照数据。
- 在 RR 级别下，对于快照数据，一致性非锁定读总是读取本事务开始时的行数据版本。

快照读比较适合对于数据一致性要求不是特别高且追求极致性能的业务场景。

**当前读** （一致性锁定读）就是给行记录加 X 锁或 S 锁。

当前读的一些常见 SQL 语句类型如下：


## 49. java_real_candidate_107 — DIRECT_FACT

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** InnoDB 支持哪几类行锁？

**Reference Answer:** InnoDB 支持记录锁、间隙锁和临键锁；临键锁由记录锁与间隙锁组合而成。

**Evidence 1:** `JavaGuide/docs/database/mysql/mysql-questions-01.md` offset `[30129, 30521)`

InnoDB 行锁是通过对索引数据页上的记录加锁实现的，MySQL InnoDB 支持三种行锁定方式：

- **记录锁（Record Lock）**：属于单个行记录上的锁。
- **间隙锁（Gap Lock）**：锁定一个范围，不包括记录本身。
- **临键锁（Next-Key Lock）**：Record Lock+Gap Lock，锁定一个范围，包含记录本身，主要目的是为了解决幻读问题（MySQL 事务部分提到过）。记录锁只能锁住已经存在的记录，为了避免插入新记录，需要依赖间隙锁。

**在 InnoDB 默认的隔离级别 REPEATABLE-READ 下，行锁默认使用的是 Next-Key Lock。但是，如果操作的索引是唯一索引或主键，InnoDB 会对 Next-Key Lock 进行优化，将其降级为 Record Lock，即仅锁住索引本身，而不是范围。**


## 50. java_real_candidate_111 — DIRECT_FACT

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** Redis 如何判断 key 是否过期？

**Reference Answer:** 过期字典的键指向 Redis 数据库中的某个 key（键），过期字典的值是一个 long long 类型的整数，这个整数保存了 key 所指向的数据库键的过期时间（毫秒精度的 UNIX 时间戳）。在查询一个 key 的时候，Redis 首先检查该 key 是否存在于过期字典中（时间复杂度为 O(1)），如果不在就直接返回，在的话需要判断一下这个 key 是否过期，过期直接删除 key 然后返回 null。

**Evidence 1:** `JavaGuide/docs/database/redis/redis-questions-01.md` offset `[22183, 22702)`

Redis 通过一个叫做过期字典（可以看作是 hash 表）来保存数据过期的时间。过期字典的键指向 Redis 数据库中的某个 key（键），过期字典的值是一个 long long 类型的整数，这个整数保存了 key 所指向的数据库键的过期时间（毫秒精度的 UNIX 时间戳）。

![Redis 过期字典](https://oss.javaguide.cn/github/javaguide/database/redis/redis-expired-dictionary.png)

过期字典是存储在 redisDb 这个结构里的：

```c
typedef struct redisDb {
    ...

    dict *dict;     //数据库键空间,保存着数据库中所有键值对
    dict *expires   // 过期字典,保存着键的过期时间
    ...
} redisDb;
```

在查询一个 key 的时候，Redis 首先检查该 key 是否存在于过期字典中（时间复杂度为 O(1)），如果不在就直接返回，在的话需要判断一下这个 key 是否过期，过期直接删除 key 然后返回 null。


## 51. java_real_candidate_112 — DIRECT_FACT

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** Redis 实际采用哪种过期 key 删除策略？

**Reference Answer:** Redis 结合使用定期删除和惰性删除，在内存占用与 CPU 开销之间取平衡。

**Evidence 1:** `JavaGuide/docs/database/redis/redis-questions-01.md` offset `[23199, 23671)`

Redis 采用的是 **定期删除+惰性/懒汉式删除** 结合的策略，这也是大部分缓存框架的选择。定期删除对内存更加友好，惰性删除对 CPU 更加友好。两者各有千秋，结合起来使用既能兼顾 CPU 友好，又能兼顾内存友好。

下面是我们详细介绍一下 Redis 中的定期删除具体是如何做的。

Redis 的定期删除过程是随机的（周期性地随机从设置了过期时间的 key 中抽查一批），所以并不保证所有过期键都会被立即删除。这也就解释了为什么有的 key 过期了，并没有被删除。并且，Redis 底层会通过限制删除操作执行的时长和频率来减少删除操作对 CPU 时间的影响。

另外，定期删除还会受到执行时间和过期 key 的比例的影响：

- 执行时间已经超过了阈值，那么就中断这一次定期删除循环，以避免使用过多的 CPU 时间。
- 如果这一批过期的 key 比例超过一个比例，就会重复执行此删除流程，以更积极地清理过期 key。相应地，如果过期的 key 比例低于这个比例，就会中断这一次定期删除循环，避免做过多的工作而获得很少的内存回收。



## 52. java_real_candidate_115 — DIRECT_FACT

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** TCP 连接在什么条件下会从四次挥手表现为三次挥手？

**Reference Answer:** 典型条件是被动关闭方收到 FIN 后已经没有待发送数据，并且应用立即关闭连接。如果确认 FIN 的 ACK 还在等待合并，内核可以把 ACK 与本端 FIN 合成一个 FIN+ACK 报文，因此抓包表现为三次挥手。

**Evidence 1:** `JavaGuide/docs/cs-basics/network/tcp-connection-and-disconnection.md` offset `[10023, 10478)`

四次挥手变成三次挥手，本质上不是少了关闭步骤，而是**第二次挥手的 ACK 和第三次挥手的 FIN 被合并到同一个报文段里**。

比较典型的条件是：被动关闭方收到 FIN 后，本端已经没有待发送的数据，应用也立刻决定关闭连接。

这里还要结合 TCP 延迟确认（Delayed ACK）来理解。延迟确认的目的，是让 ACK 有机会和窗口更新、应用响应或其他出站报文合并，减少纯 ACK 报文数量。RFC 1122 要求 ACK 不能被过度延迟，具体等待多久则由实现决定。在 Linux 等实现中，如果“确认对端 FIN”的 ACK 还在等待合并，本端应用又很快调用了 `close()` 或 `shutdown()`，内核就可以发出一个 FIN+ACK：既确认对端的 FIN，也表达“我这边也不再发送数据了”。

抓包时看到的流程就会变成：

1. 主动关闭方发送 FIN；
2. 被动关闭方发送 FIN+ACK；
3. 主动关闭方回复 ACK，并进入 `TIME_WAIT`。

这里有两个细节容易混淆：


## 53. java_real_candidate_116 — UNANSWERABLE

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** PostgreSQL 逻辑复制槽中的 confirmed_flush_lsn 和 restart_lsn 分别表示什么？

**Reference Answer:** 当前语料没有足够证据回答该问题。

## 54. java_real_candidate_117 — UNANSWERABLE

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** Kubernetes 的 CFS CPU throttling 为什么会造成 Java 服务尾延迟？

**Reference Answer:** 当前语料没有足够证据回答该问题。

## 55. java_real_candidate_118 — UNANSWERABLE

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** Apache Flink 的 unaligned checkpoint 如何处理反压？

**Reference Answer:** 当前语料没有足够证据回答该问题。

## 56. java_real_candidate_121 — UNANSWERABLE

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** Project Loom 的 ScopedValue 与 ThreadLocal 在继承语义上有什么区别？

**Reference Answer:** 当前语料没有足够证据回答该问题。

## 57. java_real_candidate_122 — UNANSWERABLE

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** Pulsar BookKeeper 的 ensemble、write quorum 和 ack quorum 如何协作？

**Reference Answer:** 当前语料没有足够证据回答该问题。

## 58. java_real_candidate_124 — UNANSWERABLE

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** Raft joint consensus 如何保证成员变更期间的安全性？

**Reference Answer:** 当前语料没有足够证据回答该问题。

## 59. java_real_candidate_125 — UNANSWERABLE

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** WebRTC ICE restart 会在什么情况下重新收集 candidate？

**Reference Answer:** 当前语料没有足够证据回答该问题。

## 60. java_real_candidate_131 — MULTI_SECTION

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** 面试官追问 synchronized 和 ReentrantLock：两者分别在哪一层实现，需要可中断、公平或超时获取锁时该怎么选？

**Reference Answer:** synchronized 的实现与优化在 JVM 层；ReentrantLock 是 JDK API，需要显式 lock/unlock 并用 try/finally 兜底释放。需要等待可中断、可配置公平策略或超时获取锁时，应选择 ReentrantLock。

**Evidence 1:** `JavaGuide/docs/java/concurrent/java-concurrent-questions-02.md` offset `[27520, 27748)`

`synchronized` 是依赖于 JVM 实现的，前面我们也讲到了 虚拟机团队在 JDK1.6 为 `synchronized` 关键字进行了很多优化，但是这些优化都是在虚拟机层面实现的，并没有直接暴露给我们。

`ReentrantLock` 是 JDK 层面实现的（也就是 API 层面，需要 `lock()` 和 `unlock()` 方法配合 `try/finally` 语句块来完成），所以我们可以通过查看它的源代码，来看它是如何实现的。


**Evidence 2:** `JavaGuide/docs/java/concurrent/java-concurrent-questions-02.md` offset `[27794, 28438)`

相比 `synchronized`，`ReentrantLock` 增加了一些高级功能。主要来说主要有三点：

- **等待可中断** : `ReentrantLock` 提供了一种能够中断等待锁的线程的机制，通过 `lock.lockInterruptibly()` 来实现这个机制。也就是说当前线程在等待获取锁的过程中，如果其他线程中断当前线程「 `interrupt()` 」，当前线程就会抛出 `InterruptedException` 异常，可以捕捉该异常进行相应处理。
- **可配置公平策略** : `ReentrantLock` 可以指定公平或非公平策略，默认是非公平的，可通过 `ReentrantLock(boolean fair)` 构造方法配置。`synchronized` 不提供公平性配置，也不承诺等待线程按先后顺序获得监视器。
- **通知机制更强大**：`ReentrantLock` 通过绑定多个 `Condition` 对象，可以实现分组唤醒和选择性通知。这解决了 `synchronized` 只能随机唤醒或全部唤醒的效率问题，为复杂的线程协作场景提供了强大的支持。
- **支持超时**：`ReentrantLock` 提供了 `tryLock(timeout)` 的方法，可以指定等待获取锁的最长等待时间，如果超过了等待时间，就会获取锁失败，不会一直等待。

如果你想使用上述功能，那么选择 `ReentrantLock` 是一个不错的选择。


## 61. java_real_candidate_132 — MULTI_SECTION

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** synchronized 和 ReentrantLock 都叫可重入锁，这个“可重入”具体指什么？两者能力边界又有什么不同？

**Reference Answer:** 可重入是指线程持有某把锁时还能再次获取同一把锁，避免嵌套调用把自己锁死。synchronized 和 ReentrantLock 都具备这一点，但 ReentrantLock 还提供等待可中断、公平策略、多个 Condition 和超时获取等高级能力。

**Evidence 1:** `JavaGuide/docs/java/concurrent/java-concurrent-questions-02.md` offset `[26741, 27468)`

**可重入锁** 也叫递归锁，指的是线程可以再次获取自己的内部锁。比如一个线程获得了某个对象的锁，此时这个对象锁还没有释放，当其再次想要获取这个对象的锁的时候还是可以获取的，如果是不可重入锁的话，就会造成死锁。

JDK 中常用的锁（如 synchronized、ReentrantLock、ReentrantReadWriteLock）是可重入的，但并不是所有 Lock 实现都支持可重入，例如 StampedLock 就是不可重入的。

在下面的代码中，`method1()` 和 `method2()` 都被 `synchronized` 关键字修饰，`method1()` 调用了 `method2()`。

```java
public class SynchronizedDemo {
    public synchronized void method1() {
        System.out.println("方法1");
        method2();
    }

    public synchronized void method2() {
        System.out.println("方法2");
    }
}
```

由于 `synchronized` 锁是可重入的，同一个线程在调用 `method1()` 时可以直接获得当前对象的锁，执行 `method2()` 的时候可以再次获取这个对象的锁，不会产生死锁问题。假如 `synchronized` 是不可重入锁的话，由于该对象的锁已被当前线程所持有且无法释放，这就导致线程在执行 `method2()` 时获取锁失败，会出现死锁问题。


**Evidence 2:** `JavaGuide/docs/java/concurrent/java-concurrent-questions-02.md` offset `[27794, 28438)`

相比 `synchronized`，`ReentrantLock` 增加了一些高级功能。主要来说主要有三点：

- **等待可中断** : `ReentrantLock` 提供了一种能够中断等待锁的线程的机制，通过 `lock.lockInterruptibly()` 来实现这个机制。也就是说当前线程在等待获取锁的过程中，如果其他线程中断当前线程「 `interrupt()` 」，当前线程就会抛出 `InterruptedException` 异常，可以捕捉该异常进行相应处理。
- **可配置公平策略** : `ReentrantLock` 可以指定公平或非公平策略，默认是非公平的，可通过 `ReentrantLock(boolean fair)` 构造方法配置。`synchronized` 不提供公平性配置，也不承诺等待线程按先后顺序获得监视器。
- **通知机制更强大**：`ReentrantLock` 通过绑定多个 `Condition` 对象，可以实现分组唤醒和选择性通知。这解决了 `synchronized` 只能随机唤醒或全部唤醒的效率问题，为复杂的线程协作场景提供了强大的支持。
- **支持超时**：`ReentrantLock` 提供了 `tryLock(timeout)` 的方法，可以指定等待获取锁的最长等待时间，如果超过了等待时间，就会获取锁失败，不会一直等待。

如果你想使用上述功能，那么选择 `ReentrantLock` 是一个不错的选择。


## 62. java_real_candidate_140 — MULTI_SECTION

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** 缓存雪崩、穿透和击穿经常被混在一起，按触发条件把三者区分清楚。

**Reference Answer:** 雪崩是缓存整体故障或大量失效，让大批流量同时压向数据库；穿透是请求的数据在缓存和数据库中都不存在，导致请求持续绕过缓存；击穿是单个热点 key 失效瞬间，大量并发请求直接访问数据库。

**Evidence 1:** `advanced-java/docs/high-concurrency/redis-caching-avalanche-and-caching-penetration.md` offset `[202, 884)`

对于系统 A，假设每天高峰期每秒 5000 个请求，本来缓存在高峰期可以扛住每秒 4000 个请求，但是缓存机器意外发生了全盘宕机。缓存挂了，此时 1 秒 5000 个请求全部落数据库，数据库必然扛不住，它会报一下警，然后就挂了。此时，如果没有采用什么特别的方案来处理这个故障，DBA 很着急，重启数据库，但是数据库立马又被新的流量给打死了。

这就是缓存雪崩。

![redis-caching-avalanche](./images/redis-caching-avalanche.png)

大约在 3 年前，国内比较知名的一个互联网公司，曾因为缓存事故，导致雪崩，后台系统全部崩溃，事故从当天下午持续到晚上凌晨 3~4 点，公司损失了几千万。

缓存雪崩的事前事中事后的解决方案如下：

-   事前：Redis 高可用，主从+哨兵，Redis cluster，避免全盘崩溃。
-   事中：本地 ehcache 缓存 + hystrix 限流&降级，避免 MySQL 被打死。
-   事后：Redis 持久化，一旦重启，自动从磁盘上加载数据，快速恢复缓存数据。

![redis-caching-avalanche-solution](./images/redis-caching-avalanche-solution.png)

用户发送一个请求，系统 A 收到请求后，先查本地 ehcache 缓存，如果没查到再查 Redis。如果 ehcache 和 Redis 都没有，再查数据库，将数据库中的结果，写入 ehcache 和 Redis 中。


**Evidence 2:** `advanced-java/docs/high-concurrency/redis-caching-avalanche-and-caching-penetration.md` offset `[1133, 1615)`

对于系统 A，假设一秒 5000 个请求，结果其中 4000 个请求是黑客发出的恶意攻击。

黑客发出的那 4000 个攻击，缓存中查不到，每次你去数据库里查，也查不到。

举个栗子。数据库 id 是从 1 开始的，结果黑客发过来的请求 id 全部都是负数。这样的话，缓存中不会有，请求每次都“**视缓存于无物**”，直接查询数据库。这种恶意攻击场景的缓存穿透就会直接把数据库给打死。

![redis-caching-penetration](./images/redis-caching-penetration.png)

解决方式很简单，每次系统 A 从数据库中只要没查到，就写一个空值到缓存里去，比如 `set -999 UNKNOWN` 。然后设置一个过期时间，这样的话，下次有相同的 key 来访问的时候，在缓存失效之前，都可以直接从缓存中取数据。

当然，如果黑客如果每次使用不同的负数 id 来攻击，写空值的方法可能就不奏效了。更为经常的做法是在缓存之前增加布隆过滤器，将数据库中所有可能的数据哈希映射到布隆过滤器中。然后对每个请求进行如下判断：


**Evidence 3:** `advanced-java/docs/high-concurrency/redis-caching-avalanche-and-caching-penetration.md` offset `[1864, 2226)`

缓存击穿，就是说某个 key 非常热点，访问非常频繁，处于集中式高并发访问的情况，当这个 key 在失效的瞬间，大量的请求就击穿了缓存，直接请求数据库，就像是在一道屏障上凿开了一个洞。

不同场景下的解决方式可如下：

-   若缓存的数据是基本不会发生更新的，则可尝试将该热点数据设置为永不过期。
-   若缓存的数据更新不频繁，且缓存刷新的整个流程耗时较少的情况下，则可以采用基于 Redis、zookeeper 等分布式中间件的分布式互斥锁，或者本地互斥锁以保证仅少量的请求能请求数据库并重新构建缓存，其余线程则在锁释放后能访问到新缓存。
-   若缓存的数据更新频繁或者在缓存刷新的流程耗时较长的情况下，可以利用定时线程在缓存过期前主动地重新构建缓存或者延后缓存的过期时间，以保证所有的请求能一直访问到对应的缓存。


## 63. java_real_candidate_141 — MULTI_SECTION

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** 面对缓存雪崩、穿透和热点 key 击穿，保护数据库的手段为什么不能用同一套？

**Reference Answer:** 雪崩要从 Redis 高可用、本地缓存、限流降级和持久化恢复入手；穿透可用布隆过滤器先筛掉确定不存在的 key；热点击穿则可采用永不过期、互斥重建或提前刷新、延后过期。

**Evidence 1:** `advanced-java/docs/high-concurrency/redis-caching-avalanche-and-caching-penetration.md` offset `[202, 884)`

对于系统 A，假设每天高峰期每秒 5000 个请求，本来缓存在高峰期可以扛住每秒 4000 个请求，但是缓存机器意外发生了全盘宕机。缓存挂了，此时 1 秒 5000 个请求全部落数据库，数据库必然扛不住，它会报一下警，然后就挂了。此时，如果没有采用什么特别的方案来处理这个故障，DBA 很着急，重启数据库，但是数据库立马又被新的流量给打死了。

这就是缓存雪崩。

![redis-caching-avalanche](./images/redis-caching-avalanche.png)

大约在 3 年前，国内比较知名的一个互联网公司，曾因为缓存事故，导致雪崩，后台系统全部崩溃，事故从当天下午持续到晚上凌晨 3~4 点，公司损失了几千万。

缓存雪崩的事前事中事后的解决方案如下：

-   事前：Redis 高可用，主从+哨兵，Redis cluster，避免全盘崩溃。
-   事中：本地 ehcache 缓存 + hystrix 限流&降级，避免 MySQL 被打死。
-   事后：Redis 持久化，一旦重启，自动从磁盘上加载数据，快速恢复缓存数据。

![redis-caching-avalanche-solution](./images/redis-caching-avalanche-solution.png)

用户发送一个请求，系统 A 收到请求后，先查本地 ehcache 缓存，如果没查到再查 Redis。如果 ehcache 和 Redis 都没有，再查数据库，将数据库中的结果，写入 ehcache 和 Redis 中。


**Evidence 2:** `advanced-java/docs/high-concurrency/redis-caching-avalanche-and-caching-penetration.md` offset `[1616, 1836)`

-   请求数据的 key 不存在于布隆过滤器中，可以确定数据就一定不会存在于数据库中，系统可以立即返回不存在。
-   请求数据的 key 存在于布隆过滤器中，则继续再向缓存中查询。

使用布隆过滤器能够对访问的请求起到了一定的初筛作用，避免了因数据不存在引起的查询压力。

![redis-caching-avoid-penetration](./images/redis-caching-avoid-penetration.png)


**Evidence 3:** `advanced-java/docs/high-concurrency/redis-caching-avalanche-and-caching-penetration.md` offset `[1864, 2226)`

缓存击穿，就是说某个 key 非常热点，访问非常频繁，处于集中式高并发访问的情况，当这个 key 在失效的瞬间，大量的请求就击穿了缓存，直接请求数据库，就像是在一道屏障上凿开了一个洞。

不同场景下的解决方式可如下：

-   若缓存的数据是基本不会发生更新的，则可尝试将该热点数据设置为永不过期。
-   若缓存的数据更新不频繁，且缓存刷新的整个流程耗时较少的情况下，则可以采用基于 Redis、zookeeper 等分布式中间件的分布式互斥锁，或者本地互斥锁以保证仅少量的请求能请求数据库并重新构建缓存，其余线程则在锁释放后能访问到新缓存。
-   若缓存的数据更新频繁或者在缓存刷新的流程耗时较长的情况下，可以利用定时线程在缓存过期前主动地重新构建缓存或者延后缓存的过期时间，以保证所有的请求能一直访问到对应的缓存。


## 64. java_real_candidate_143 — MULTI_SECTION

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** 乐观锁和悲观锁对并发冲突的基本假设是什么，它们分别会让竞争线程怎样等待？

**Reference Answer:** 悲观锁假设共享资源容易发生冲突，访问前就加锁，让其他线程阻塞到锁释放。乐观锁假设多数访问不会冲突，执行时不加锁不等待，只在提交修改时验证数据是否被其他线程改变。

**Evidence 1:** `JavaGuide/docs/java/concurrent/optimistic-lock-and-pessimistic-lock.md` offset `[410, 916)`

悲观锁总是假设最坏的情况，认为共享资源每次被访问的时候就会出现问题（比如共享数据被修改），所以每次在获取资源操作的时候都会上锁，这样其他线程想拿到这个资源就会阻塞直到锁被上一个持有者释放。也就是说，**共享资源每次只给一个线程使用，其它线程阻塞，用完后再把资源转让给其它线程**。

像 Java 中 `synchronized` 和 `ReentrantLock` 等独占锁就是悲观锁思想的实现。

```java
public void performSynchronisedTask() {
    synchronized (this) {
        // 需要同步的操作
    }
}

private Lock lock = new ReentrantLock();
lock.lock();
try {
   // 需要同步的操作
} finally {
    lock.unlock();
}
```

高并发的场景下，激烈的锁竞争会造成线程阻塞，大量阻塞线程会导致系统的上下文切换，增加系统的性能开销。并且，悲观锁还可能会存在死锁问题（线程获得锁的顺序不当时），影响代码的正常运行。


**Evidence 2:** `JavaGuide/docs/java/concurrent/optimistic-lock-and-pessimistic-lock.md` offset `[929, 1537)`

乐观锁总是假设最好的情况，认为共享资源每次被访问的时候不会出现问题，线程可以不停地执行，无需加锁也无需等待，只是在提交修改的时候去验证对应的资源（也就是数据）是否被其它线程修改了（具体方法可以使用版本号机制或 CAS 算法）。

在 Java 中 `java.util.concurrent.atomic` 包下面的原子变量类（比如 `AtomicInteger`、`LongAdder`）就是使用了乐观锁的一种实现方式 **CAS** 实现的。
![JUC原子类概览](https://oss.javaguide.cn/github/javaguide/java/JUC%E5%8E%9F%E5%AD%90%E7%B1%BB%E6%A6%82%E8%A7%88-20230814005211968.png)

```java
// LongAdder 在高并发场景下会比 AtomicInteger 和 AtomicLong 的性能更好
// 代价就是会消耗更多的内存空间（空间换时间）
LongAdder sum = new LongAdder();
sum.increment();
```

高并发的场景下，乐观锁相比悲观锁来说，不存在锁竞争造成线程阻塞，也不会有死锁问题，在性能上往往会更胜一筹。但是，如果冲突频繁发生（写占比非常多的情况），会频繁失败并重试，这样同样会非常影响性能，导致 CPU 飙升。


## 65. java_real_candidate_147 — MULTI_SECTION

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** JDK 8 的 HashMap 和 ConcurrentHashMap 底层结构看起来很像，并发能力为什么完全不同？

**Reference Answer:** 两者都使用数组、链表和红黑树处理哈希冲突；普通 HashMap 主要靠扩容和树化改善查询，并不提供并发保护。ConcurrentHashMap 额外用 Node、CAS 与 synchronized 保证并发安全，并把锁粒度缩小到桶首节点。

**Evidence 1:** `JavaGuide/docs/java/collection/java-collection-questions-02.md` offset `[7989, 8473)`

相比于之前的版本， JDK1.8 之后在解决哈希冲突时有了较大的变化，当链表长度大于阈值（默认为 8）（将链表转换成红黑树前会判断，如果当前数组的长度小于 64，那么会选择先进行数组扩容，而不是转换为红黑树）时，将链表转化为红黑树。

这样做的目的是减少搜索时间：链表的查询效率为 O(n)（n 是链表的长度），红黑树是一种自平衡二叉搜索树，其查询效率为 O(log n)。当链表较短时，O(n) 和 O(log n) 的性能差异不明显。但当链表变长时，查询性能会显著下降。

![jdk1.8之后的内部结构-HashMap](https://oss.javaguide.cn/github/javaguide/java/collection/jdk1.8_hashmap.png)

**为什么优先扩容而非直接转为红黑树？**

数组扩容能减少哈希冲突的发生概率（即将元素重新分散到新的、更大的数组中），这在多数情况下比直接转换为红黑树更高效。

红黑树需要保持自平衡，维护成本较高。并且，过早引入红黑树反而会增加复杂度。

**为什么选择阈值 8 和 64？**


**Evidence 2:** `JavaGuide/docs/java/collection/java-collection-questions-02.md` offset `[18277, 18738)`

![Java8 ConcurrentHashMap 存储结构](https://oss.javaguide.cn/github/javaguide/java/collection/java8_concurrenthashmap.png)

Java 8 几乎完全重写了 `ConcurrentHashMap`，代码量从原来 Java 7 中的 1000 多行，变成了现在的 6000 多行。

`ConcurrentHashMap` 取消了 `Segment` 分段锁，采用 `Node + CAS + synchronized` 来保证并发安全。数据结构跟 `HashMap` 1.8 的结构类似，数组+链表/红黑二叉树。Java 8 在链表长度超过一定阈值（8）时将链表（寻址时间复杂度为 O(N)）转换为红黑树（寻址时间复杂度为 O(log(N))）。

Java 8 中，锁粒度更细，更新非空桶时通常使用 `synchronized` 锁定桶的首节点，不同桶上的更新通常可以并行执行，读取操作也不会使用这些桶锁。


**Evidence 3:** `JavaGuide/docs/java/collection/java-collection-questions-02.md` offset `[12306, 12664)`

`HashMap` 不是线程安全的。在多线程环境下对 `HashMap` 进行并发写操作，可能会导致两种主要问题：

1. **数据丢失**：并发 `put` 操作可能导致一个线程的写入被另一个线程覆盖。
2. **无限循环**：在 JDK 7 及以前的版本中，并发扩容时，由于头插法可能导致链表形成环，从而在 `get` 操作时引发无限循环，CPU 飙升至 100%。

数据丢失这个在 JDK1.7 和 JDK 1.8 中都存在，这里以 JDK 1.8 为例进行介绍。

JDK 1.8 后，在 `HashMap` 中，多个键值对可能会被分配到同一个桶（bucket），并以链表或红黑树的形式存储。多个线程对 `HashMap` 的 `put` 操作会导致线程不安全，具体来说会有数据覆盖的风险。

举个例子：


## 66. java_real_candidate_148 — MULTI_SECTION

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** 并发写 Map 时，直接用 HashMap 会出什么问题，ConcurrentHashMap 在 JDK 8 里如何缩小冲突范围？

**Reference Answer:** HashMap 并发写可能丢数据，旧版本并发扩容还可能形成链表环。JDK 8 ConcurrentHashMap 采用 CAS 与 synchronized，更新非空桶时通常只锁桶首节点，不同桶可并行更新。

**Evidence 1:** `JavaGuide/docs/java/collection/java-collection-questions-02.md` offset `[12306, 12664)`

`HashMap` 不是线程安全的。在多线程环境下对 `HashMap` 进行并发写操作，可能会导致两种主要问题：

1. **数据丢失**：并发 `put` 操作可能导致一个线程的写入被另一个线程覆盖。
2. **无限循环**：在 JDK 7 及以前的版本中，并发扩容时，由于头插法可能导致链表形成环，从而在 `get` 操作时引发无限循环，CPU 飙升至 100%。

数据丢失这个在 JDK1.7 和 JDK 1.8 中都存在，这里以 JDK 1.8 为例进行介绍。

JDK 1.8 后，在 `HashMap` 中，多个键值对可能会被分配到同一个桶（bucket），并以链表或红黑树的形式存储。多个线程对 `HashMap` 的 `put` 操作会导致线程不安全，具体来说会有数据覆盖的风险。

举个例子：


**Evidence 2:** `JavaGuide/docs/java/collection/java-collection-questions-02.md` offset `[18277, 18738)`

![Java8 ConcurrentHashMap 存储结构](https://oss.javaguide.cn/github/javaguide/java/collection/java8_concurrenthashmap.png)

Java 8 几乎完全重写了 `ConcurrentHashMap`，代码量从原来 Java 7 中的 1000 多行，变成了现在的 6000 多行。

`ConcurrentHashMap` 取消了 `Segment` 分段锁，采用 `Node + CAS + synchronized` 来保证并发安全。数据结构跟 `HashMap` 1.8 的结构类似，数组+链表/红黑二叉树。Java 8 在链表长度超过一定阈值（8）时将链表（寻址时间复杂度为 O(N)）转换为红黑树（寻址时间复杂度为 O(log(N))）。

Java 8 中，锁粒度更细，更新非空桶时通常使用 `synchronized` 锁定桶的首节点，不同桶上的更新通常可以并行执行，读取操作也不会使用这些桶锁。


## 67. java_real_candidate_151 — MULTI_SECTION

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** poll 相比 select 改掉了哪些接口限制，又有哪些 O(N) 性能问题原封不动地留下了？

**Reference Answer:** select 的 fd_set 有固定表示范围，调用后集合被改写，需每轮重建，并在线性扫描中找就绪 fd。poll 改用 pollfd 数组，取消固定 1024 上限并分离 events/revents，但仍需每次复制完整数组、返回后 O(N) 遍历。

**Evidence 1:** `JavaGuide/docs/cs-basics/operating-system/io-multiplexing.md` offset `[3617, 4118)`

**第一，fd 数量有上限**。在 Linux/glibc 环境里，`fd_set` 位图的大小由 glibc 的常量 `FD_SETSIZE` 决定，默认是 1024，只能安全表示 0~1023 的 fd——这个限制来自用户态 glibc 的固定大小数据结构和 `FD_*` 宏，而不是 Linux 内核本身。对超出范围的 fd 使用这些宏属于未定义行为，也别指望靠重定义 `FD_SETSIZE` 或重新编译内核绕过去。真要盯更多连接，正确做法是换用 poll、epoll。

**第二，每次调用都要把位图在用户态和内核态之间来回拷一遍**。调用前你在用户态填好位图，`select` 把它拷进内核；返回时内核改写位图（把没就绪的位清掉），再拷回用户态。内核实际检查和回写的范围由 `nfds` 决定，所以 fd 编号越大、监听越多，这一来一回越费。

**第三，位图是“传入即传出”参数（value-result）**。内核返回时会把没就绪的位清零，所以你下一轮必须 `FD_ZERO` + 重新 `FD_SET` 一遍，老的关心列表不能复用。代码里那句“每轮都得重新清空”就是被这个逼出来的。


**Evidence 2:** `JavaGuide/docs/cs-basics/operating-system/io-multiplexing.md` offset `[4345, 5210)`

`poll` 和 `select` 是同代产物，思路一致，但换掉了数据结构。它不用位图，改用一个 `pollfd` 结构体数组：

```c
#include <poll.h>

struct pollfd {
    int   fd;       // 要监听的文件描述符
    short events;   // 你关心的事件，调用前填，比如 POLLIN（可读）
    short revents;  // 实际发生的事件，由内核回填
};

int poll(struct pollfd *fds, nfds_t nfds, int timeout);
```

主循环长这样：

```c
struct pollfd fds[MAX];
fds[0].fd = listenfd;
fds[0].events = POLLIN;
// 其余 fds[i].fd = connfd; fds[i].events = POLLIN;

while (1) {
    int ready = poll(fds, nfds, -1);      // timeout 传 -1 表示一直阻塞
    for (int i = 0; i < nfds; i++) {
        if (fds[i].revents & POLLIN) {    // 内核把结果写在 revents 里
            // 处理读事件
        }
    }
}
```

相比 `select`，`poll` 改对了两件事：

**没有 1024 的硬上限**。监听多少个 fd 取决于你传入的数组多大，不再受 `FD_SETSIZE` 卡死，上限主要看进程能打开的 fd 数。

**关心的事件和发生的事件分开了**。`events` 是你填的（输入），`revents` 是内核回填的（输出），两个字段各管各的。这样下一轮不用像 `select` 那样把整个关心列表重置，`events` 保持不动就行。


**Evidence 3:** `JavaGuide/docs/cs-basics/operating-system/io-multiplexing.md` offset `[5211, 5369)`

但 `poll` 没解决 `select` 最要命的两个性能问题：每次调用还是要把整个数组从用户态拷到内核态，返回后还是要 O(N) 遍历整个数组才能找出哪些 fd 就绪。连接规模一上去，开销照样是线性增长。

说白了，`poll` 是把 `select` 的接口擦干净了，性能模型没变。真正的质变在 epoll。


## 68. java_real_candidate_152 — MULTI_SECTION

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** 海量连接但只有少量活跃时，epoll 相比 poll 的关键变化到底在哪里？

**Reference Answer:** poll 每次都把完整 fd 数组交给内核并线性扫描。epoll 把注册集合长期留在内核，epoll_wait 只返回真正就绪的 fd；其就绪链表与回调机制让等待阶段的遍历规模更接近活跃事件数。

**Evidence 1:** `JavaGuide/docs/cs-basics/operating-system/io-multiplexing.md` offset `[5211, 5369)`

但 `poll` 没解决 `select` 最要命的两个性能问题：每次调用还是要把整个数组从用户态拷到内核态，返回后还是要 O(N) 遍历整个数组才能找出哪些 fd 就绪。连接规模一上去，开销照样是线性增长。

说白了，`poll` 是把 `select` 的接口擦干净了，性能模型没变。真正的质变在 epoll。


**Evidence 2:** `JavaGuide/docs/cs-basics/operating-system/io-multiplexing.md` offset `[6180, 7103)`

```c
int epfd = epoll_create1(0);              // 第一步：建实例

struct epoll_event ev;
ev.events = EPOLLIN;                       // 关心可读，默认水平触发
ev.data.fd = listenfd;
epoll_ctl(epfd, EPOLL_CTL_ADD, listenfd, &ev);  // 第二步：注册一次就够

struct epoll_event events[MAX_EVENTS];
while (1) {
    // 第三步：只返回真正就绪的 fd，n 就是就绪个数
    int n = epoll_wait(epfd, events, MAX_EVENTS, -1);
    for (int i = 0; i < n; i++) {          // 只遍历就绪的，不扫描全集
        int fd = events[i].data.fd;
        if (fd == listenfd) {
            int connfd = accept(listenfd, NULL, NULL);
            ev.events = EPOLLIN;
            ev.data.fd = connfd;
            epoll_ctl(epfd, EPOLL_CTL_ADD, connfd, &ev);  // 新连接注册进去
        } else {
            // 处理 fd 上的读事件
        }
    }
}
```

对比 `select` 那段代码，差别一眼就看出来：注册 fd 和等事件被拆开了，`epoll_wait` 返回的 `events` 数组里**全是就绪的 fd**，遍历它就行，不用再拿所有 fd 挨个问。

这个差别不是接口设计上的小聪明，而是底层数据结构换了。一个 epoll 实例在内核里对应一个 `eventpoll` 结构，里面有两样关键东西：


**Evidence 3:** `JavaGuide/docs/cs-basics/operating-system/io-multiplexing.md` offset `[7104, 7732)`

- **一棵红黑树（rbr）**：存所有通过 `epoll_ctl` 注册进来的 fd（每个 fd 对应一个 `epitem` 节点）。增删改是 O（log N） 的树操作。fd 只在这里登记一次，之后一直待着，不像 select/poll 每次调用都要把全量列表搬进内核。
- **一条就绪链表（rdllist）**：一个双向链表，专门存“已经就绪”的 fd。

![epoll 内部架构：epoll_ctl 维护 interest list，fd 就绪后通过回调进入 ready list，epoll_wait 返回就绪事件](https://oss.javaguide.cn/github/javaguide/cs-basics/operating-system/io-multiplexing-epoll-architecture.png)

关键在于回调机制。`epoll_ctl` 注册 fd 时，内核会给这个 fd 挂一个回调函数。当网卡来数据、某个 fd 变得可读时，这个回调被触发，把对应的就绪对象挂进就绪链表，并唤醒阻塞在 `epoll_wait` 上的线程。于是 `epoll_wait` 要做的只是看一眼就绪链表空不空——有就把里面的事件拷给用户态，没有就睡觉等回调来唤醒。（补一句：红黑树、就绪链表都是当前内核的实现方式，`epoll` 对用户态承诺的只是“注册集合 + 就绪列表”这层抽象语义，别把树结构当成稳定的 ABI。）


## 69. java_real_candidate_153 — MULTI_SECTION

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** Spring 里的 IoC 和 AOP 分别解决哪类耦合问题，为什么不能把它们当成同一个概念？

**Reference Answer:** IoC 把对象创建和管理交给容器，降低对象依赖与替换实现的耦合；AOP 把日志、事务、权限、限流等横切关注点从核心业务中分离。前者管理对象依赖，后者组织横切逻辑，作用层面不同。

**Evidence 1:** `JavaGuide/docs/system-design/framework/spring/ioc-and-aop.md` offset `[518, 1032)`

IoC （Inversion of Control ）即控制反转/反转控制。它是一种思想不是一个技术实现。描述的是：Java 开发领域对象的创建以及管理的问题。

例如：现有类 A 依赖于类 B

- **传统的开发方式** ：往往是在类 A 中手动通过 new 关键字来 new 一个 B 的对象出来
- **使用 IoC 思想的开发方式** ：不通过 new 关键字来创建对象，而是通过 IoC 容器(Spring 框架) 来帮助我们实例化对象。我们需要哪个对象，直接从 IoC 容器里面去取即可。

从以上两种开发方式的对比来看：我们 “丧失了一个权力” (创建、管理对象的权力)，从而也得到了一个好处（不用再考虑对象的创建、管理等一系列的事情）

**为什么叫控制反转?**

- **控制** ：指的是对象创建（实例化、管理）的权力
- **反转** ：控制权交给外部环境（IoC 容器）

![IoC 图解](https://oss.javaguide.cn/github/javaguide/system-design/framework/spring/IoC&Aop-ioc-illustration.png)


**Evidence 2:** `JavaGuide/docs/system-design/framework/spring/ioc-and-aop.md` offset `[2544, 2799)`

AOP（Aspect Oriented Programming）即面向切面编程，AOP 是 OOP（面向对象编程）的一种延续，二者互补，并不对立。

AOP 的目的是将横切关注点（如日志记录、事务管理、权限控制、接口限流、接口幂等等）从核心业务逻辑中分离出来，通过动态代理、字节码操作等技术，实现代码的复用和解耦，提高代码的可维护性和可扩展性。OOP 的目的是将业务逻辑按照对象的属性和行为进行封装，通过类、对象、继承、多态等概念，实现代码的模块化和层次化（也能实现代码的复用），提高代码的可读性和可维护性。


## 70. java_real_candidate_154 — MULTI_SECTION

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** 用 Redis 和 ZooKeeper 实现分布式锁时，获取与释放锁的核心数据结构和操作分别是什么？

**Reference Answer:** Redis 的简易实现用 SET NX 配合过期时间创建锁，并用校验 value 的 Lua 脚本删除锁。ZooKeeper 则创建临时顺序节点，序号最小者获锁，失败者监听前一节点，释放时删除节点。

**Evidence 1:** `advanced-java/docs/distributed-system/distributed-lock-redis-vs-zookeeper.md` offset `[373, 962)`

第一个最普通的实现方式，就是在 Redis 里使用 `SET key value [EX seconds] [PX milliseconds] NX` 创建一个 key，这样就算加锁。其中：

-   `NX`：表示只有 `key` 不存在的时候才会设置成功，如果此时 redis 中存在这个 `key`，那么设置失败，返回 `nil`。
-   `EX seconds`：设置 `key` 的过期时间，精确到秒级。意思是 `seconds` 秒后锁自动释放，别人创建的时候如果发现已经有了就不能加锁了。
-   `PX milliseconds`：同样是设置 `key` 的过期时间，精确到毫秒级。

比如执行以下命令：

```r
SET resource_name my_random_value PX 30000 NX
```

释放锁就是删除 key ，但是一般可以用 `lua` 脚本删除，判断 value 一样才删除：

```lua
-- 删除锁的时候，找到 key 对应的 value，跟自己传过去的 value 做比较，如果是一样的才删除。
if redis.call("get",KEYS[1]) == ARGV[1] then
    return redis.call("del",KEYS[1])
else
    return 0
end
```


**Evidence 2:** `JavaGuide/docs/distributed-system/distributed-lock-implementations.md` offset `[8812, 9438)`

ZooKeeper 分布式锁是基于 **临时顺序节点** 和 **Watcher（事件监听器）** 实现的。

获取锁：

1. 首先我们要有一个持久节点 `/locks`，客户端获取锁就是在 `/locks` 下创建临时顺序节点。
2. 假设客户端 1 创建了 `/locks/lock1` 节点，创建成功之后，会判断 `lock1` 是否是 `/locks` 下最小的子节点。
3. 如果 `lock1` 是最小的子节点，则获取锁成功。否则，获取锁失败。
4. 如果获取锁失败，则说明有其他的客户端已经成功获取锁。客户端 1 并不会不停地循环去尝试加锁，而是在前一个节点比如 `/locks/lock0` 上注册一个事件监听器。这个监听器的作用是当前一个节点释放锁之后通知客户端 1（避免无效自旋），这样客户端 1 就加锁成功了。

释放锁：

1. 成功获取锁的客户端在执行完业务流程之后，会将对应的子节点删除。
2. 成功获取锁的客户端在出现故障之后，对应的子节点由于是临时顺序节点，也会被自动删除，避免了锁无法被释放。
3. 我们前面说的事件监听器其实监听的就是这个子节点删除事件，子节点删除就意味着锁被释放。

![](https://oss.javaguide.cn/github/javaguide/distributed-system/distributed-lock/distributed-lock-zookeeper.png)


## 71. java_real_candidate_155 — MULTI_SECTION

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** 客户端崩溃或没抢到锁时，Redis 与 ZooKeeper 的等待和自动释放语义有什么差别？

**Reference Answer:** Redis 通常依赖锁的过期时间避免永久占锁，普通竞争者需要重试；ZooKeeper 临时节点随会话消失，可在客户端故障后自动删除，等待者只监听前一顺序节点，在删除事件发生后再尝试获取。

**Evidence 1:** `advanced-java/docs/distributed-system/distributed-lock-redis-vs-zookeeper.md` offset `[9439, 9753)`

-   redis 分布式锁，其实**需要自己不断去尝试获取锁**，比较消耗性能。
-   zk 分布式锁，获取不到锁，注册个监听器即可，不需要不断主动尝试获取锁，性能开销较小。

另外一点就是，如果是 Redis 获取锁的那个客户端 出现 bug 挂了，那么只能等待超时时间之后才能释放锁；而 zk 的话，因为创建的是临时 znode，只要客户端挂了，znode 就没了，此时就自动释放锁。

Redis 分布式锁大家没发现好麻烦吗？遍历上锁，计算时间等等......zk 的分布式锁语义清晰实现简单。

所以先不分析太多的东西，就说这两点，我个人实践认为 zk 的分布式锁比 Redis 的分布式锁牢靠、而且模型简单易用。


**Evidence 2:** `JavaGuide/docs/distributed-system/distributed-lock-implementations.md` offset `[11228, 11600)`

不过，ZooKeeper 同样需要考虑 GC 停顿、网络分区和 session timeout。客户端长时间 GC 或网络分区导致 session 过期时，ZooKeeper 会删除临时节点并允许新客户端加锁，而旧客户端可能还没感知到会话失效，仍以为自己持锁。对于正确性要求高的场景，仍应结合 Fencing Token 防止旧客户端恢复后写入陈旧数据。

使用 Redis 实现分布式锁的时候，我们是通过过期时间来避免锁无法被释放导致死锁问题的，而 ZooKeeper 可以利用临时节点的特性处理客户端崩溃后的锁释放问题。

假设不使用顺序节点的话，所有尝试获取锁的客户端都会对持有锁的子节点加监听器。当该锁被释放之后，势必会造成所有尝试获取锁的客户端来争夺锁，这样对性能不友好。使用顺序节点之后，只需要监听前一个节点就好了，对性能更友好。


**Evidence 3:** `JavaGuide/docs/distributed-system/distributed-lock-implementations.md` offset `[11623, 12000)`

> Watcher（事件监听器），是 ZooKeeper 中的一个很重要的特性。ZooKeeper 允许用户在指定节点上注册一些 Watcher，并且在一些特定事件触发的时候，ZooKeeper 服务端会将事件通知到感兴趣的客户端上去，该机制是 ZooKeeper 实现分布式协调服务的重要特性。

同一时间段内，可能会有很多客户端同时获取锁，但只有一个可以获取成功。如果获取锁失败，则说明有其他的客户端已经成功获取锁。获取锁失败的客户端并不会不停地循环去尝试加锁，而是在前一个节点注册一个事件监听器。

这个事件监听器的作用是：**当前一个节点对应的客户端释放锁之后（也就是前一个节点被删除之后，监听的是删除事件），通知获取锁失败的客户端（唤醒等待的线程，Java 中的 `wait/notifyAll`），让它尝试去获取锁，然后就成功获取锁了。**


## 72. java_real_candidate_157 — HARD_NEGATIVE

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** 业务要求锁等待可中断、可配置公平性并支持超时，ReentrantLock 分别提供了什么能力？

**Reference Answer:** 可用 lockInterruptibly 中断等待，通过构造参数配置公平或非公平策略，并用 tryLock(timeout) 限定最长等待时间。

**Evidence 1:** `JavaGuide/docs/java/concurrent/java-concurrent-questions-02.md` offset `[27794, 28438)`

相比 `synchronized`，`ReentrantLock` 增加了一些高级功能。主要来说主要有三点：

- **等待可中断** : `ReentrantLock` 提供了一种能够中断等待锁的线程的机制，通过 `lock.lockInterruptibly()` 来实现这个机制。也就是说当前线程在等待获取锁的过程中，如果其他线程中断当前线程「 `interrupt()` 」，当前线程就会抛出 `InterruptedException` 异常，可以捕捉该异常进行相应处理。
- **可配置公平策略** : `ReentrantLock` 可以指定公平或非公平策略，默认是非公平的，可通过 `ReentrantLock(boolean fair)` 构造方法配置。`synchronized` 不提供公平性配置，也不承诺等待线程按先后顺序获得监视器。
- **通知机制更强大**：`ReentrantLock` 通过绑定多个 `Condition` 对象，可以实现分组唤醒和选择性通知。这解决了 `synchronized` 只能随机唤醒或全部唤醒的效率问题，为复杂的线程协作场景提供了强大的支持。
- **支持超时**：`ReentrantLock` 提供了 `tryLock(timeout)` 的方法，可以指定等待获取锁的最长等待时间，如果超过了等待时间，就会获取锁失败，不会一直等待。

如果你想使用上述功能，那么选择 `ReentrantLock` 是一个不错的选择。


**Hard Negative 1:** `JavaGuide/docs/java/concurrent/java-concurrent-questions-02.md` offset `[26741, 27468)`

**可重入锁** 也叫递归锁，指的是线程可以再次获取自己的内部锁。比如一个线程获得了某个对象的锁，此时这个对象锁还没有释放，当其再次想要获取这个对象的锁的时候还是可以获取的，如果是不可重入锁的话，就会造成死锁。

JDK 中常用的锁（如 synchronized、ReentrantLock、ReentrantReadWriteLock）是可重入的，但并不是所有 Lock 实现都支持可重入，例如 StampedLock 就是不可重入的。

在下面的代码中，`method1()` 和 `method2()` 都被 `synchronized` 关键字修饰，`method1()` 调用了 `method2()`。

```java
public class SynchronizedDemo {
    public synchronized void method1() {
        System.out.println("方法1");
        method2();
    }

    public synchronized void method2() {
        System.out.println("方法2");
    }
}
```

由于 `synchronized` 锁是可重入的，同一个线程在调用 `method1()` 时可以直接获得当前对象的锁，执行 `method2()` 的时候可以再次获取这个对象的锁，不会产生死锁问题。假如 `synchronized` 是不可重入锁的话，由于该对象的锁已被当前线程所持有且无法释放，这就导致线程在执行 `method2()` 时获取锁失败，会出现死锁问题。


**Hard Negative 2:** `JavaGuide/docs/java/concurrent/java-concurrent-questions-02.md` offset `[27520, 27748)`

`synchronized` 是依赖于 JVM 实现的，前面我们也讲到了 虚拟机团队在 JDK1.6 为 `synchronized` 关键字进行了很多优化，但是这些优化都是在虚拟机层面实现的，并没有直接暴露给我们。

`ReentrantLock` 是 JDK 层面实现的（也就是 API 层面，需要 `lock()` 和 `unlock()` 方法配合 `try/finally` 语句块来完成），所以我们可以通过查看它的源代码，来看它是如何实现的。


## 73. java_real_candidate_158 — HARD_NEGATIVE

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** synchronized 修饰实例方法与静态方法时，锁住的对象分别是什么？

**Reference Answer:** 修饰实例方法时锁当前对象实例；修饰静态方法时锁当前 Class，对该类的所有实例生效。

**Evidence 1:** `JavaGuide/docs/java/concurrent/java-concurrent-questions-02.md` offset `[19074, 19695)`

`synchronized` 关键字的使用方式主要有下面 3 种：

1. 修饰实例方法
2. 修饰静态方法
3. 修饰代码块

**1、修饰实例方法**（锁当前对象实例）

给当前对象实例加锁，进入同步代码前要获得 **当前对象实例的锁**。

```java
synchronized void method() {
    //业务代码
}
```

**2、修饰静态方法**（锁当前类）

给当前类加锁，会作用于类的所有对象实例，进入同步代码前要获得 **当前 class 的锁**。

这是因为静态成员不属于任何一个实例对象，归整个类所有，不依赖于类的特定实例，被类的所有实例共享。

```java
synchronized static void method() {
    //业务代码
}
```

静态 `synchronized` 方法和非静态 `synchronized` 方法之间的调用互斥么？不互斥！如果一个线程 A 调用一个实例对象的非静态 `synchronized` 方法，而线程 B 需要调用这个实例对象所属类的静态 `synchronized` 方法，是允许的，不会发生互斥现象，因为访问静态 `synchronized` 方法占用的锁是当前类的锁，而访问非静态 `synchronized` 方法占用的锁是当前实例对象锁。

**3、修饰代码块**（锁指定对象/类）

对括号里指定的对象/类加锁：


**Hard Negative 1:** `JavaGuide/docs/java/concurrent/java-concurrent-questions-02.md` offset `[27794, 28438)`

相比 `synchronized`，`ReentrantLock` 增加了一些高级功能。主要来说主要有三点：

- **等待可中断** : `ReentrantLock` 提供了一种能够中断等待锁的线程的机制，通过 `lock.lockInterruptibly()` 来实现这个机制。也就是说当前线程在等待获取锁的过程中，如果其他线程中断当前线程「 `interrupt()` 」，当前线程就会抛出 `InterruptedException` 异常，可以捕捉该异常进行相应处理。
- **可配置公平策略** : `ReentrantLock` 可以指定公平或非公平策略，默认是非公平的，可通过 `ReentrantLock(boolean fair)` 构造方法配置。`synchronized` 不提供公平性配置，也不承诺等待线程按先后顺序获得监视器。
- **通知机制更强大**：`ReentrantLock` 通过绑定多个 `Condition` 对象，可以实现分组唤醒和选择性通知。这解决了 `synchronized` 只能随机唤醒或全部唤醒的效率问题，为复杂的线程协作场景提供了强大的支持。
- **支持超时**：`ReentrantLock` 提供了 `tryLock(timeout)` 的方法，可以指定等待获取锁的最长等待时间，如果超过了等待时间，就会获取锁失败，不会一直等待。

如果你想使用上述功能，那么选择 `ReentrantLock` 是一个不错的选择。


**Hard Negative 2:** `JavaGuide/docs/java/concurrent/java-concurrent-questions-02.md` offset `[26741, 27468)`

**可重入锁** 也叫递归锁，指的是线程可以再次获取自己的内部锁。比如一个线程获得了某个对象的锁，此时这个对象锁还没有释放，当其再次想要获取这个对象的锁的时候还是可以获取的，如果是不可重入锁的话，就会造成死锁。

JDK 中常用的锁（如 synchronized、ReentrantLock、ReentrantReadWriteLock）是可重入的，但并不是所有 Lock 实现都支持可重入，例如 StampedLock 就是不可重入的。

在下面的代码中，`method1()` 和 `method2()` 都被 `synchronized` 关键字修饰，`method1()` 调用了 `method2()`。

```java
public class SynchronizedDemo {
    public synchronized void method1() {
        System.out.println("方法1");
        method2();
    }

    public synchronized void method2() {
        System.out.println("方法2");
    }
}
```

由于 `synchronized` 锁是可重入的，同一个线程在调用 `method1()` 时可以直接获得当前对象的锁，执行 `method2()` 的时候可以再次获取这个对象的锁，不会产生死锁问题。假如 `synchronized` 是不可重入锁的话，由于该对象的锁已被当前线程所持有且无法释放，这就导致线程在执行 `method2()` 时获取锁失败，会出现死锁问题。


## 74. java_real_candidate_167 — HARD_NEGATIVE

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** 布隆过滤器怎样拦住缓存穿透请求，它在哪一种判断下可以立即返回不存在？

**Reference Answer:** 请求 key 不在布隆过滤器中时，可以确定数据库也不存在该数据并立即返回；只有可能存在时才继续查缓存。

**Evidence 1:** `advanced-java/docs/high-concurrency/redis-caching-avalanche-and-caching-penetration.md` offset `[1616, 1836)`

-   请求数据的 key 不存在于布隆过滤器中，可以确定数据就一定不会存在于数据库中，系统可以立即返回不存在。
-   请求数据的 key 存在于布隆过滤器中，则继续再向缓存中查询。

使用布隆过滤器能够对访问的请求起到了一定的初筛作用，避免了因数据不存在引起的查询压力。

![redis-caching-avoid-penetration](./images/redis-caching-avoid-penetration.png)


**Hard Negative 1:** `advanced-java/docs/high-concurrency/redis-caching-avalanche-and-caching-penetration.md` offset `[1864, 2226)`

缓存击穿，就是说某个 key 非常热点，访问非常频繁，处于集中式高并发访问的情况，当这个 key 在失效的瞬间，大量的请求就击穿了缓存，直接请求数据库，就像是在一道屏障上凿开了一个洞。

不同场景下的解决方式可如下：

-   若缓存的数据是基本不会发生更新的，则可尝试将该热点数据设置为永不过期。
-   若缓存的数据更新不频繁，且缓存刷新的整个流程耗时较少的情况下，则可以采用基于 Redis、zookeeper 等分布式中间件的分布式互斥锁，或者本地互斥锁以保证仅少量的请求能请求数据库并重新构建缓存，其余线程则在锁释放后能访问到新缓存。
-   若缓存的数据更新频繁或者在缓存刷新的流程耗时较长的情况下，可以利用定时线程在缓存过期前主动地重新构建缓存或者延后缓存的过期时间，以保证所有的请求能一直访问到对应的缓存。


**Hard Negative 2:** `advanced-java/docs/high-concurrency/redis-caching-avalanche-and-caching-penetration.md` offset `[202, 884)`

对于系统 A，假设每天高峰期每秒 5000 个请求，本来缓存在高峰期可以扛住每秒 4000 个请求，但是缓存机器意外发生了全盘宕机。缓存挂了，此时 1 秒 5000 个请求全部落数据库，数据库必然扛不住，它会报一下警，然后就挂了。此时，如果没有采用什么特别的方案来处理这个故障，DBA 很着急，重启数据库，但是数据库立马又被新的流量给打死了。

这就是缓存雪崩。

![redis-caching-avalanche](./images/redis-caching-avalanche.png)

大约在 3 年前，国内比较知名的一个互联网公司，曾因为缓存事故，导致雪崩，后台系统全部崩溃，事故从当天下午持续到晚上凌晨 3~4 点，公司损失了几千万。

缓存雪崩的事前事中事后的解决方案如下：

-   事前：Redis 高可用，主从+哨兵，Redis cluster，避免全盘崩溃。
-   事中：本地 ehcache 缓存 + hystrix 限流&降级，避免 MySQL 被打死。
-   事后：Redis 持久化，一旦重启，自动从磁盘上加载数据，快速恢复缓存数据。

![redis-caching-avalanche-solution](./images/redis-caching-avalanche-solution.png)

用户发送一个请求，系统 A 收到请求后，先查本地 ehcache 缓存，如果没查到再查 Redis。如果 ehcache 和 Redis 都没有，再查数据库，将数据库中的结果，写入 ehcache 和 Redis 中。


## 75. java_real_candidate_174 — HARD_NEGATIVE

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** HashMap 并发 put 为什么可能丢数据，JDK 7 并发扩容还有什么极端后果？

**Reference Answer:** 并发 put 可能让一个线程的写入覆盖另一个线程；JDK 7 及以前并发扩容使用头插法时可能形成链表环，get 随后无限循环并把 CPU 打满。

**Evidence 1:** `JavaGuide/docs/java/collection/java-collection-questions-02.md` offset `[12306, 12664)`

`HashMap` 不是线程安全的。在多线程环境下对 `HashMap` 进行并发写操作，可能会导致两种主要问题：

1. **数据丢失**：并发 `put` 操作可能导致一个线程的写入被另一个线程覆盖。
2. **无限循环**：在 JDK 7 及以前的版本中，并发扩容时，由于头插法可能导致链表形成环，从而在 `get` 操作时引发无限循环，CPU 飙升至 100%。

数据丢失这个在 JDK1.7 和 JDK 1.8 中都存在，这里以 JDK 1.8 为例进行介绍。

JDK 1.8 后，在 `HashMap` 中，多个键值对可能会被分配到同一个桶（bucket），并以链表或红黑树的形式存储。多个线程对 `HashMap` 的 `put` 操作会导致线程不安全，具体来说会有数据覆盖的风险。

举个例子：


**Hard Negative 1:** `JavaGuide/docs/java/collection/java-collection-questions-02.md` offset `[18277, 18738)`

![Java8 ConcurrentHashMap 存储结构](https://oss.javaguide.cn/github/javaguide/java/collection/java8_concurrenthashmap.png)

Java 8 几乎完全重写了 `ConcurrentHashMap`，代码量从原来 Java 7 中的 1000 多行，变成了现在的 6000 多行。

`ConcurrentHashMap` 取消了 `Segment` 分段锁，采用 `Node + CAS + synchronized` 来保证并发安全。数据结构跟 `HashMap` 1.8 的结构类似，数组+链表/红黑二叉树。Java 8 在链表长度超过一定阈值（8）时将链表（寻址时间复杂度为 O(N)）转换为红黑树（寻址时间复杂度为 O(log(N))）。

Java 8 中，锁粒度更细，更新非空桶时通常使用 `synchronized` 锁定桶的首节点，不同桶上的更新通常可以并行执行，读取操作也不会使用这些桶锁。


**Hard Negative 2:** `JavaGuide/docs/java/collection/java-collection-questions-02.md` offset `[7989, 8473)`

相比于之前的版本， JDK1.8 之后在解决哈希冲突时有了较大的变化，当链表长度大于阈值（默认为 8）（将链表转换成红黑树前会判断，如果当前数组的长度小于 64，那么会选择先进行数组扩容，而不是转换为红黑树）时，将链表转化为红黑树。

这样做的目的是减少搜索时间：链表的查询效率为 O(n)（n 是链表的长度），红黑树是一种自平衡二叉搜索树，其查询效率为 O(log n)。当链表较短时，O(n) 和 O(log n) 的性能差异不明显。但当链表变长时，查询性能会显著下降。

![jdk1.8之后的内部结构-HashMap](https://oss.javaguide.cn/github/javaguide/java/collection/jdk1.8_hashmap.png)

**为什么优先扩容而非直接转为红黑树？**

数组扩容能减少哈希冲突的发生概率（即将元素重新分散到新的、更大的数组中），这在多数情况下比直接转换为红黑树更高效。

红黑树需要保持自平衡，维护成本较高。并且，过早引入红黑树反而会增加复杂度。

**为什么选择阈值 8 和 64？**


## 76. java_real_candidate_175 — HARD_NEGATIVE

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** JDK 8 ConcurrentHashMap 取消 Segment 后，靠什么保证并发安全，锁粒度落在哪里？

**Reference Answer:** 它使用 Node、CAS 与 synchronized 保证安全；更新非空桶时通常锁住桶首节点，不同桶更新可以并行。

**Evidence 1:** `JavaGuide/docs/java/collection/java-collection-questions-02.md` offset `[18277, 18738)`

![Java8 ConcurrentHashMap 存储结构](https://oss.javaguide.cn/github/javaguide/java/collection/java8_concurrenthashmap.png)

Java 8 几乎完全重写了 `ConcurrentHashMap`，代码量从原来 Java 7 中的 1000 多行，变成了现在的 6000 多行。

`ConcurrentHashMap` 取消了 `Segment` 分段锁，采用 `Node + CAS + synchronized` 来保证并发安全。数据结构跟 `HashMap` 1.8 的结构类似，数组+链表/红黑二叉树。Java 8 在链表长度超过一定阈值（8）时将链表（寻址时间复杂度为 O(N)）转换为红黑树（寻址时间复杂度为 O(log(N))）。

Java 8 中，锁粒度更细，更新非空桶时通常使用 `synchronized` 锁定桶的首节点，不同桶上的更新通常可以并行执行，读取操作也不会使用这些桶锁。


**Hard Negative 1:** `JavaGuide/docs/java/collection/java-collection-questions-02.md` offset `[17463, 18260)`

![Java7 ConcurrentHashMap 存储结构](https://oss.javaguide.cn/github/javaguide/java/collection/java7_concurrenthashmap.png)

首先将数据分为一段一段（这个“段”就是 `Segment`）的存储，然后给每一段数据配一把锁，当一个线程占用锁访问其中一个段数据时，其他段的数据也能被其他线程访问。

**`ConcurrentHashMap` 是由 `Segment` 数组结构和 `HashEntry` 数组结构组成**。

`Segment` 继承了 `ReentrantLock`,所以 `Segment` 是一种可重入锁，扮演锁的角色。`HashEntry` 用于存储键值对数据。

```java
static class Segment<K,V> extends ReentrantLock implements Serializable {
}
```

一个 `ConcurrentHashMap` 里包含一个 `Segment` 数组，`Segment` 的个数一旦**初始化就不能改变**。 `Segment` 数组的大小默认是 16，也就是说默认可以同时支持 16 个线程并发写。

`Segment` 的结构和 `HashMap` 类似，是一种数组和链表结构，一个 `Segment` 包含一个 `HashEntry` 数组，每个 `HashEntry` 是一个链表结构的元素，每个 `Segment` 守护着一个 `HashEntry` 数组里的元素，当对 `HashEntry` 数组的数据进行修改时，必须首先获得对应的 `Segment` 的锁。也就是说，对同一 `Segment` 的并发写入会被阻塞，不同 `Segment` 的写入是可以并发执行的。


**Hard Negative 2:** `JavaGuide/docs/java/collection/java-collection-questions-02.md` offset `[12306, 12664)`

`HashMap` 不是线程安全的。在多线程环境下对 `HashMap` 进行并发写操作，可能会导致两种主要问题：

1. **数据丢失**：并发 `put` 操作可能导致一个线程的写入被另一个线程覆盖。
2. **无限循环**：在 JDK 7 及以前的版本中，并发扩容时，由于头插法可能导致链表形成环，从而在 `get` 操作时引发无限循环，CPU 飙升至 100%。

数据丢失这个在 JDK1.7 和 JDK 1.8 中都存在，这里以 JDK 1.8 为例进行介绍。

JDK 1.8 后，在 `HashMap` 中，多个键值对可能会被分配到同一个桶（bucket），并以链表或红黑树的形式存储。多个线程对 `HashMap` 的 `put` 操作会导致线程不安全，具体来说会有数据覆盖的风险。

举个例子：


## 77. java_real_candidate_177 — HARD_NEGATIVE

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** 同一进程里的线程共享哪些资源，又有哪些执行现场必须各自保存？

**Reference Answer:** 线程共享代码段、数据段、堆、文件描述符和 Socket 等进程资源；各自保留栈、寄存器、程序计数器、线程 ID、调度优先级和 TLS。

**Evidence 1:** `JavaGuide/docs/cs-basics/operating-system/process-and-thread.md` offset `[4049, 4617)`

![线程共享资源和私有执行现场](https://oss.javaguide.cn/github/javaguide/cs-basics/operating-system/thread-shared-and-private-content.png)

从操作系统角度看，同一进程内的线程共享进程的大部分资源，例如：

- 代码段、数据段、堆等进程地址空间里的内存区域；
- 打开的文件描述符、Socket、工作目录；
- 进程 ID、地址空间、信号处理配置中的一部分；
- 全局变量和堆对象。

如果换到 Java/JVM 语境，Java 线程还会共享同一个 JVM 进程里的堆、方法区/元空间等运行时数据区域。方法区/元空间不是通用操作系统概念，放在 JVM 这一层理解更合适。

在 Linux 用户态，同一进程内的多个线程调用 `getpid()` 通常看到的是同一个线程组 ID，也就是平时说的进程 ID；但每个线程在内核里仍有自己的 task/TID，可以用 `gettid()` 区分。

每个线程也有自己的私有内容：

- 栈：保存函数调用、局部变量、返回地址等。
- 寄存器和程序计数器：记录线程当前执行到哪里。
- 线程 ID、调度优先级、线程本地存储（TLS）。
- 线程状态和少量内核用于恢复执行的上下文信息。



**Hard Negative 1:** `JavaGuide/docs/cs-basics/operating-system/process-and-thread.md` offset `[5691, 6050)`

按“谁负责调度”来看，线程可以分为用户级线程和内核级线程。

**用户级线程**由用户态运行时或线程库管理，内核通常看不到这些线程。它的好处是创建、切换不一定需要系统调用；问题是如果所有用户线程只对应一个内核调度实体，那么其中一个线程发起阻塞系统调用，可能拖住整个进程，也很难利用多核。

**内核级线程**由操作系统内核创建和调度。某个线程阻塞，内核还能调度同进程的其他线程；多个线程也能在多核上并行执行。代价是创建、销毁、阻塞、唤醒、切换都要内核参与。

常见线程模型有三类：

![常见的三种线程模型](https://oss.javaguide.cn/github/javaguide/java/new-features/process-and-thread-three-thread-models.png)


**Hard Negative 2:** `JavaGuide/docs/cs-basics/operating-system/process-and-thread.md` offset `[7256, 7657)`

纤程（Fiber）和协程通常运行在用户态，由应用或运行时调度。操作系统真正调度的是承载它们的内核线程，而不是每一个纤程或协程。因此，这类轻量执行单元切换时通常不需要陷入内核，成本可以更低。

但它们不是“免费线程”。如果运行时没有把阻塞 I/O 改造成可挂起、可恢复的形式，一个用户态任务阻塞住承载线程，同一承载线程上的其他任务也会受影响。另外，不同语言、运行时、CPU 架构和调用栈深度都会影响切换成本，不能把某个基准测试里的纳秒数字当成通用结论。

Java 21 引入的虚拟线程就是一个典型例子。它仍然是 `java.lang.Thread`，但不会长期独占一个操作系统线程。虚拟线程运行时会挂载到平台线程（platform thread）上，平台线程再对应底层的系统内核线程；当虚拟线程执行 JDK 支持的可挂起阻塞 I/O 时，JDK 可以先把它卸载下来，让这个平台线程去运行别的虚拟线程。


## 78. java_real_candidate_178 — HARD_NEGATIVE

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** select 在 fd 数量、集合传递和就绪查找上分别有什么扩展性问题？

**Reference Answer:** fd_set 有固定表示上限；集合每次都要在用户态和内核态来回复制，返回时还会被改写；应用最终仍需 O(N) 扫描候选 fd 才能找出就绪项。

**Evidence 1:** `JavaGuide/docs/cs-basics/operating-system/io-multiplexing.md` offset `[3617, 4118)`

**第一，fd 数量有上限**。在 Linux/glibc 环境里，`fd_set` 位图的大小由 glibc 的常量 `FD_SETSIZE` 决定，默认是 1024，只能安全表示 0~1023 的 fd——这个限制来自用户态 glibc 的固定大小数据结构和 `FD_*` 宏，而不是 Linux 内核本身。对超出范围的 fd 使用这些宏属于未定义行为，也别指望靠重定义 `FD_SETSIZE` 或重新编译内核绕过去。真要盯更多连接，正确做法是换用 poll、epoll。

**第二，每次调用都要把位图在用户态和内核态之间来回拷一遍**。调用前你在用户态填好位图，`select` 把它拷进内核；返回时内核改写位图（把没就绪的位清掉），再拷回用户态。内核实际检查和回写的范围由 `nfds` 决定，所以 fd 编号越大、监听越多，这一来一回越费。

**第三，位图是“传入即传出”参数（value-result）**。内核返回时会把没就绪的位清零，所以你下一轮必须 `FD_ZERO` + 重新 `FD_SET` 一遍，老的关心列表不能复用。代码里那句“每轮都得重新清空”就是被这个逼出来的。


**Evidence 2:** `JavaGuide/docs/cs-basics/operating-system/io-multiplexing.md` offset `[4119, 4328)`

**第四，返回后还得自己 O(N) 遍历**。`select` 的返回值只给出就绪 fd 的数量，具体哪些 fd 就绪体现在被原地改写的 `fd_set` 中。应用仍要遍历候选范围并调用 `FD_ISSET`；一万个连接哪怕只有一个来数据，也可能要检查一万次。

`timeout` 这个参数倒是有点用：传 NULL 一直阻塞，传一个 0 值的 `timeval` 表示不等立即返回（轮询），传具体值表示最多等多久。


**Hard Negative 1:** `JavaGuide/docs/cs-basics/operating-system/io-multiplexing.md` offset `[4345, 5210)`

`poll` 和 `select` 是同代产物，思路一致，但换掉了数据结构。它不用位图，改用一个 `pollfd` 结构体数组：

```c
#include <poll.h>

struct pollfd {
    int   fd;       // 要监听的文件描述符
    short events;   // 你关心的事件，调用前填，比如 POLLIN（可读）
    short revents;  // 实际发生的事件，由内核回填
};

int poll(struct pollfd *fds, nfds_t nfds, int timeout);
```

主循环长这样：

```c
struct pollfd fds[MAX];
fds[0].fd = listenfd;
fds[0].events = POLLIN;
// 其余 fds[i].fd = connfd; fds[i].events = POLLIN;

while (1) {
    int ready = poll(fds, nfds, -1);      // timeout 传 -1 表示一直阻塞
    for (int i = 0; i < nfds; i++) {
        if (fds[i].revents & POLLIN) {    // 内核把结果写在 revents 里
            // 处理读事件
        }
    }
}
```

相比 `select`，`poll` 改对了两件事：

**没有 1024 的硬上限**。监听多少个 fd 取决于你传入的数组多大，不再受 `FD_SETSIZE` 卡死，上限主要看进程能打开的 fd 数。

**关心的事件和发生的事件分开了**。`events` 是你填的（输入），`revents` 是内核回填的（输出），两个字段各管各的。这样下一轮不用像 `select` 那样把整个关心列表重置，`events` 保持不动就行。


**Hard Negative 2:** `JavaGuide/docs/cs-basics/operating-system/io-multiplexing.md` offset `[8446, 9122)`

epoll 支持两种触发模式，这是它比 select/poll 多出来的一个能力，也是面试和实战里最容易踩坑的地方。

**水平触发（LT，Level Triggered）** 是默认模式。只要 fd 上还有数据没读完（或者还有空间可写），每次 `epoll_wait` 都会一直通知你。select 和 poll 只有这一种模式。

**边缘触发（ET，Edge Triggered）** 要显式加 `EPOLLET` 标志。它只在状态**发生变化**的那一刻通知一次。

用一个具体场景说清楚区别（这也是 Linux man page 里的经典例子）：假设对端往一个 socket 写了 2 KB 数据。

- LT 模式：`epoll_wait` 通知你可读。你只读了 1 KB，缓冲区里还剩 1 KB。下次 `epoll_wait` 还会继续通知你“这儿有数据没读完”，直到你把 2 KB 读干净。
- ET 模式：`epoll_wait` 通知你一次。你只读了 1 KB 就走了，那剩下的 1 KB——除非对端又写了新数据、状态再次发生变化，`epoll_wait` 不会主动再为它通知你。这 1 KB 可能就长期躺在缓冲区里，连接迟迟得不到处理。

![水平触发和边缘触发对比：LT 在数据未读完时会持续通知，ET 只在状态变化时通知一次](https://oss.javaguide.cn/github/javaguide/cs-basics/operating-system/io-multiplexing-lt-vs-et.png)


## 79. java_real_candidate_179 — HARD_NEGATIVE

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** ZooKeeper 临时节点为什么能降低客户端崩溃后永久占锁的风险？

**Reference Answer:** 临时节点生命周期绑定客户端会话，会话消失节点自动删除；即使客户端异常未主动释放锁，也能在会话失效后清理占锁节点。

**Evidence 1:** `JavaGuide/docs/distributed-system/distributed-lock-implementations.md` offset `[10679, 11227)`

每个数据节点在 ZooKeeper 中被称为 **znode**，它是 ZooKeeper 中数据的最小单元。

我们通常是将 znode 分为 4 大类：

- **持久（PERSISTENT）节点**：一旦创建就一直存在即使 ZooKeeper 集群宕机，直到将其删除。
- **临时（EPHEMERAL）节点**：临时节点的生命周期是与 **客户端会话（session）** 绑定的，**会话消失则节点消失**。并且，**临时节点只能做叶子节点**，不能创建子节点。
- **持久顺序（PERSISTENT_SEQUENTIAL）节点**：除了具有持久（PERSISTENT）节点的特性之外，子节点的名称还具有顺序性。比如 `/node1/app0000000001`、`/node1/app0000000002`。
- **临时顺序（EPHEMERAL_SEQUENTIAL）节点**：除了具备临时（EPHEMERAL）节点的特性之外，子节点的名称还具有顺序性。

可以看出，临时节点相比持久节点，最主要的是对会话失效的情况处理不一样，临时节点会话消失则对应的节点消失。这样的话，如果客户端发生异常导致没来得及释放锁也没关系，会话失效节点会自动被删除，可以避免客户端进程崩溃后永久占锁。


**Hard Negative 1:** `advanced-java/docs/distributed-system/distributed-lock-redis-vs-zookeeper.md` offset `[373, 962)`

第一个最普通的实现方式，就是在 Redis 里使用 `SET key value [EX seconds] [PX milliseconds] NX` 创建一个 key，这样就算加锁。其中：

-   `NX`：表示只有 `key` 不存在的时候才会设置成功，如果此时 redis 中存在这个 `key`，那么设置失败，返回 `nil`。
-   `EX seconds`：设置 `key` 的过期时间，精确到秒级。意思是 `seconds` 秒后锁自动释放，别人创建的时候如果发现已经有了就不能加锁了。
-   `PX milliseconds`：同样是设置 `key` 的过期时间，精确到毫秒级。

比如执行以下命令：

```r
SET resource_name my_random_value PX 30000 NX
```

释放锁就是删除 key ，但是一般可以用 `lua` 脚本删除，判断 value 一样才删除：

```lua
-- 删除锁的时候，找到 key 对应的 value，跟自己传过去的 value 做比较，如果是一样的才删除。
if redis.call("get",KEYS[1]) == ARGV[1] then
    return redis.call("del",KEYS[1])
else
    return 0
end
```


**Hard Negative 2:** `JavaGuide/docs/distributed-system/distributed-lock-implementations.md` offset `[11623, 12000)`

> Watcher（事件监听器），是 ZooKeeper 中的一个很重要的特性。ZooKeeper 允许用户在指定节点上注册一些 Watcher，并且在一些特定事件触发的时候，ZooKeeper 服务端会将事件通知到感兴趣的客户端上去，该机制是 ZooKeeper 实现分布式协调服务的重要特性。

同一时间段内，可能会有很多客户端同时获取锁，但只有一个可以获取成功。如果获取锁失败，则说明有其他的客户端已经成功获取锁。获取锁失败的客户端并不会不停地循环去尝试加锁，而是在前一个节点注册一个事件监听器。

这个事件监听器的作用是：**当前一个节点对应的客户端释放锁之后（也就是前一个节点被删除之后，监听的是删除事件），通知获取锁失败的客户端（唤醒等待的线程，Java 中的 `wait/notifyAll`），让它尝试去获取锁，然后就成功获取锁了。**


## 80. java_real_candidate_180 — HARD_NEGATIVE

- [ ] Evidence offsets replay exactly
- [ ] Question sounds like a real Java backend interview
- [ ] Answer is concise, grounded, and adds no external fact
- [ ] Multi/Hard-Negative relationship is logically valid (if applicable)

**Question:** Kafka 生产者配置 acks=all 后，一次写入在什么条件下才算成功？

**Reference Answer:** leader 接收消息且所有 follower 都完成同步后才算写成功；条件未满足时生产者会继续重试。

**Evidence 1:** `advanced-java/docs/high-concurrency/how-to-ensure-the-reliable-transmission-of-messages.md` offset `[5985, 6098)`

如果按照上述的思路设置了 `acks=all` ，一定不会丢，要求是，你的 leader 接收到消息，所有的 follower 都同步到了消息之后，才认为本次写成功了。如果没满足这个条件，生产者会自动不断的重试，重试无限次。


**Hard Negative 1:** `advanced-java/docs/high-concurrency/how-to-ensure-the-reliable-transmission-of-messages.md` offset `[1212, 1769)`

所以一般来说，如果你要确保说写 RabbitMQ 的消息别丢，可以开启 `confirm` 模式，在生产者那里设置开启 `confirm` 模式之后，你每次写的消息都会分配一个唯一的 id，然后如果写入了 RabbitMQ 中，RabbitMQ 会给你回传一个 `ack` 消息，告诉你说这个消息 ok 了。如果 RabbitMQ 没能处理这个消息，会回调你的一个 `nack` 接口，告诉你这个消息接收失败，你可以重试。而且你可以结合这个机制自己在内存里维护每个消息 id 的状态，如果超过一定时间还没接收到这个消息的回调，那么你可以重发。

事务机制和 `confirm` 机制最大的不同在于，**事务机制是同步的**，你提交一个事务之后会**阻塞**在那儿，但是 `confirm` 机制是**异步**的，你发送个消息之后就可以发送下一个消息，然后那个消息 RabbitMQ 接收了之后会异步回调你的一个接口通知你这个消息接收到了。

所以一般在生产者这块**避免数据丢失**，都是用 `confirm` 机制的。

> 已经在 transaction 事务模式的 channel 是不能再设置成 confirm 模式的，即这两种模式是不能共存的。

客户端实现生产者 `confirm` 有 3 种方式：


**Hard Negative 2:** `advanced-java/docs/high-concurrency/how-to-ensure-the-reliable-transmission-of-messages.md` offset `[6254, 6563)`

解决发送时消息丢失的问题可以采用 RocketMQ 自带的**事务消息**机制

事务消息原理：首先生产者会发送一个**half 消息**(对原始消息的封装)，该消息对消费者不可见，MQ 通过 ACK 机制返回消息接受状态， 生产者执行本地事务并且返回给 MQ 一个状态(Commit、RollBack 等)，如果是 Commit 的话 MQ 就会把消息给到下游， RollBack 的话就会丢弃该消息，状态如果为 UnKnow 的话会过一段时间回查本地事务状态，默认回查 15 次，一直是 UnKnow 状态的话就会丢弃此消息。

为什么先发一个 half 消息，作用就是先判断下 MQ 有没有问题，服务正不正常。

