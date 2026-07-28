package interview.guide.benchmark.config;

import interview.guide.benchmark.metrics.BenchmarkMetrics;
import io.micrometer.core.instrument.MeterRegistry;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.ThreadFactory;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

@Configuration
@ConditionalOnProperty(name = "benchmark.client.enabled", havingValue = "true", matchIfMissing = true)
public class BenchmarkExecutorConfiguration {

  @Bean(destroyMethod = "shutdown")
  ExecutorService llmExecutor(LlmExecutorProperties properties) {
    if (properties.type().equals("virtual")) {
      ThreadFactory factory = Thread.ofVirtual().name("llm-virtual-", 0).factory();
      return new ThreadPerTaskExecutorAdapter(factory);
    }

    AtomicInteger sequence = new AtomicInteger();
    ThreadFactory factory = task -> {
      Thread thread = new Thread(task, "llm-fixed-" + sequence.incrementAndGet());
      thread.setDaemon(false);
      return thread;
    };
    return new ThreadPoolExecutor(
        properties.fixedPoolSize(),
        properties.fixedPoolSize(),
        0L,
        TimeUnit.MILLISECONDS,
        new LinkedBlockingQueue<>(properties.queueCapacity()),
        factory,
        new ThreadPoolExecutor.AbortPolicy()
    );
  }

  @Bean
  BenchmarkMetrics benchmarkMetrics(
      ExecutorService llmExecutor,
      LlmExecutorProperties properties,
      MeterRegistry meterRegistry
  ) {
    return new BenchmarkMetrics(llmExecutor, properties, meterRegistry);
  }

  private static final class ThreadPerTaskExecutorAdapter
      extends java.util.concurrent.AbstractExecutorService {

    private final ExecutorService delegate;

    private ThreadPerTaskExecutorAdapter(ThreadFactory factory) {
      this.delegate = java.util.concurrent.Executors.newThreadPerTaskExecutor(factory);
    }

    @Override
    public void shutdown() {
      delegate.shutdown();
    }

    @Override
    public java.util.List<Runnable> shutdownNow() {
      return delegate.shutdownNow();
    }

    @Override
    public boolean isShutdown() {
      return delegate.isShutdown();
    }

    @Override
    public boolean isTerminated() {
      return delegate.isTerminated();
    }

    @Override
    public boolean awaitTermination(long timeout, TimeUnit unit) throws InterruptedException {
      return delegate.awaitTermination(timeout, unit);
    }

    @Override
    public void execute(Runnable command) {
      delegate.execute(command);
    }
  }
}
