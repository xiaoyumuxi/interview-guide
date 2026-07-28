package interview.guide.benchmark.config;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;

import static org.assertj.core.api.Assertions.assertThat;

class BenchmarkExecutorConfigurationTest {

  private final BenchmarkExecutorConfiguration configuration =
      new BenchmarkExecutorConfiguration();

  @Test
  @DisplayName("fixed 模式创建 32 个平台线程的固定线程池")
  void createsFixedPlatformThreadPool() throws Exception {
    ExecutorService executor = configuration.llmExecutor(
        new LlmExecutorProperties("fixed", 32, 10_000)
    );
    try {
      assertThat(executor).isInstanceOf(ThreadPoolExecutor.class);
      ThreadPoolExecutor threadPool = (ThreadPoolExecutor) executor;
      assertThat(threadPool.getCorePoolSize()).isEqualTo(32);
      assertThat(threadPool.getMaximumPoolSize()).isEqualTo(32);
      assertThat(executor.submit(() -> Thread.currentThread().isVirtual()).get())
          .isFalse();
    } finally {
      executor.shutdownNow();
      assertThat(executor.awaitTermination(5, TimeUnit.SECONDS)).isTrue();
    }
  }

  @Test
  @DisplayName("virtual 模式为每个任务创建虚拟线程")
  void createsVirtualThreadPerTaskExecutor() throws Exception {
    ExecutorService executor = configuration.llmExecutor(
        new LlmExecutorProperties("virtual", 32, 10_000)
    );
    try {
      assertThat(executor.submit(() -> Thread.currentThread().isVirtual()).get())
          .isTrue();
    } finally {
      executor.shutdownNow();
      assertThat(executor.awaitTermination(5, TimeUnit.SECONDS)).isTrue();
    }
  }
}
