package interview.guide.benchmark.metrics;

import com.sun.management.OperatingSystemMXBean;
import interview.guide.benchmark.config.LlmExecutorProperties;
import io.micrometer.core.instrument.Gauge;
import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.Timer;

import java.lang.management.ManagementFactory;
import java.lang.management.MemoryMXBean;
import java.lang.management.ThreadMXBean;
import java.time.Duration;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.atomic.LongAdder;

public final class BenchmarkMetrics {

  private final ExecutorService executor;
  private final LlmExecutorProperties properties;
  private final ThreadMXBean threadMxBean = ManagementFactory.getThreadMXBean();
  private final MemoryMXBean memoryMxBean = ManagementFactory.getMemoryMXBean();
  private final OperatingSystemMXBean operatingSystemMxBean =
      (OperatingSystemMXBean) ManagementFactory.getOperatingSystemMXBean();
  private final AtomicInteger activeTasks = new AtomicInteger();
  private final AtomicInteger peakActiveTasks = new AtomicInteger();
  private final AtomicLong completedRequests = new AtomicLong();
  private final AtomicLong failedRequests = new AtomicLong();
  private final LongAdder totalQueueWaitNanos = new LongAdder();
  private final LongAdder totalExecutionNanos = new LongAdder();
  private final Timer queueWaitTimer;
  private final Timer executionTimer;

  public BenchmarkMetrics(
      ExecutorService executor,
      LlmExecutorProperties properties,
      MeterRegistry meterRegistry
  ) {
    this.executor = executor;
    this.properties = properties;
    this.queueWaitTimer = Timer.builder("benchmark.llm.queue.wait")
        .description("Time between executor submission and task start")
        .publishPercentileHistogram()
        .register(meterRegistry);
    this.executionTimer = Timer.builder("benchmark.llm.execution")
        .description("Time spent executing the blocking Spring AI call")
        .publishPercentileHistogram()
        .register(meterRegistry);
    Gauge.builder("benchmark.llm.executor.active", activeTasks, AtomicInteger::get)
        .register(meterRegistry);
    Gauge.builder("benchmark.llm.executor.queue", this, ignored -> executorQueueSize())
        .register(meterRegistry);
  }

  public void taskStarted() {
    int active = activeTasks.incrementAndGet();
    peakActiveTasks.accumulateAndGet(active, Math::max);
  }

  public void taskFinished(long queueWaitNanos, long executionNanos, boolean success) {
    activeTasks.decrementAndGet();
    completedRequests.incrementAndGet();
    if (!success) {
      failedRequests.incrementAndGet();
    }
    totalQueueWaitNanos.add(queueWaitNanos);
    totalExecutionNanos.add(executionNanos);
    queueWaitTimer.record(Duration.ofNanos(queueWaitNanos));
    executionTimer.record(Duration.ofNanos(executionNanos));
  }

  public synchronized void reset() {
    completedRequests.set(0);
    failedRequests.set(0);
    peakActiveTasks.set(activeTasks.get());
    totalQueueWaitNanos.reset();
    totalExecutionNanos.reset();
    threadMxBean.resetPeakThreadCount();
  }

  public Snapshot snapshot() {
    long completed = completedRequests.get();
    return new Snapshot(
        properties.type(),
        properties.type().equals("fixed") ? properties.fixedPoolSize() : 0,
        activeTasks.get(),
        peakActiveTasks.get(),
        executorPoolSize(),
        executorQueueSize(),
        completed,
        failedRequests.get(),
        averageMillis(totalQueueWaitNanos.sum(), completed),
        averageMillis(totalExecutionNanos.sum(), completed),
        threadMxBean.getThreadCount(),
        threadMxBean.getPeakThreadCount(),
        properties.type().equals("virtual") ? activeTasks.get() : 0,
        properties.type().equals("virtual") ? peakActiveTasks.get() : 0,
        operatingSystemMxBean.getProcessCpuLoad(),
        operatingSystemMxBean.getProcessCpuTime(),
        memoryMxBean.getHeapMemoryUsage().getUsed(),
        memoryMxBean.getHeapMemoryUsage().getCommitted(),
        memoryMxBean.getNonHeapMemoryUsage().getUsed()
    );
  }

  private int executorPoolSize() {
    if (executor instanceof ThreadPoolExecutor threadPoolExecutor) {
      return threadPoolExecutor.getPoolSize();
    }
    return 0;
  }

  private int executorQueueSize() {
    if (executor instanceof ThreadPoolExecutor threadPoolExecutor) {
      return threadPoolExecutor.getQueue().size();
    }
    return 0;
  }

  private static double averageMillis(long totalNanos, long count) {
    return count == 0 ? 0.0 : totalNanos / 1_000_000.0 / count;
  }

  public record Snapshot(
      String mode,
      int configuredFixedPoolSize,
      int activeExecutorTasks,
      int peakActiveExecutorTasks,
      int executorPoolSize,
      int executorQueueSize,
      long completedRequests,
      long failedRequests,
      double averageQueueWaitMs,
      double averageExecutionMs,
      int livePlatformThreads,
      int peakPlatformThreads,
      int liveVirtualExecutorTasks,
      int peakVirtualExecutorTasks,
      double processCpuLoad,
      long processCpuTimeNanos,
      long heapUsedBytes,
      long heapCommittedBytes,
      long nonHeapUsedBytes
  ) {}
}
