package interview.guide.benchmark.service;

import interview.guide.benchmark.metrics.BenchmarkMetrics;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.stereotype.Service;

import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Future;

@Service
@ConditionalOnProperty(name = "benchmark.client.enabled", havingValue = "true", matchIfMissing = true)
public class BenchmarkLlmService {

  private static final String FIXED_PROMPT =
      "Return the fixed benchmark response. This prompt must be identical for every request.";

  private final ChatClient chatClient;
  private final ExecutorService llmExecutor;
  private final BenchmarkMetrics metrics;

  public BenchmarkLlmService(
      @Qualifier("mockChatClient") ChatClient chatClient,
      @Qualifier("llmExecutor") ExecutorService llmExecutor,
      BenchmarkMetrics metrics
  ) {
    this.chatClient = chatClient;
    this.llmExecutor = llmExecutor;
    this.metrics = metrics;
  }

  public LlmCallResult call() {
    long submitNanos = System.nanoTime();
    Future<LlmCallResult> future = llmExecutor.submit(() -> executeCall(submitNanos));
    try {
      return future.get();
    } catch (InterruptedException e) {
      Thread.currentThread().interrupt();
      throw new IllegalStateException("Interrupted while waiting for benchmark LLM call", e);
    } catch (ExecutionException e) {
      Throwable cause = e.getCause() == null ? e : e.getCause();
      throw new IllegalStateException("Benchmark LLM call failed", cause);
    }
  }

  private LlmCallResult executeCall(long submitNanos) {
    long startNanos = System.nanoTime();
    long queueWaitNanos = startNanos - submitNanos;
    metrics.taskStarted();
    boolean success = false;
    try {
      String content = chatClient.prompt()
          .user(FIXED_PROMPT)
          .call()
          .content();
      long finishNanos = System.nanoTime();
      success = true;
      return new LlmCallResult(
          content,
          queueWaitNanos / 1_000_000.0,
          (finishNanos - startNanos) / 1_000_000.0,
          Thread.currentThread().isVirtual(),
          Thread.currentThread().getName()
      );
    } finally {
      long finishNanos = System.nanoTime();
      metrics.taskFinished(queueWaitNanos, finishNanos - startNanos, success);
    }
  }

  public record LlmCallResult(
      String content,
      double queueWaitMs,
      double executionMs,
      boolean virtualThread,
      String executorThread
  ) {}
}
