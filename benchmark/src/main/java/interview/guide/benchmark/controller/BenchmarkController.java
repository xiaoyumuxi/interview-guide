package interview.guide.benchmark.controller;

import interview.guide.benchmark.metrics.BenchmarkMetrics;
import interview.guide.benchmark.service.BenchmarkLlmService;
import interview.guide.benchmark.service.BenchmarkLlmService.LlmCallResult;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/benchmark")
@ConditionalOnProperty(name = "benchmark.client.enabled", havingValue = "true", matchIfMissing = true)
public class BenchmarkController {

  private final BenchmarkLlmService llmService;
  private final BenchmarkMetrics metrics;

  public BenchmarkController(BenchmarkLlmService llmService, BenchmarkMetrics metrics) {
    this.llmService = llmService;
    this.metrics = metrics;
  }

  @PostMapping("/llm")
  public LlmCallResult callLlm() {
    return llmService.call();
  }

  @GetMapping("/state")
  public BenchmarkMetrics.Snapshot state() {
    return metrics.snapshot();
  }

  @PostMapping("/state/reset")
  public BenchmarkMetrics.Snapshot reset() {
    metrics.reset();
    return metrics.snapshot();
  }
}
