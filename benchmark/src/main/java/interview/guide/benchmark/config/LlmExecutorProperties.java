package interview.guide.benchmark.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties("llm.executor")
public record LlmExecutorProperties(
    String type,
    int fixedPoolSize,
    int queueCapacity
) {

  public LlmExecutorProperties {
    type = type == null || type.isBlank() ? "fixed" : type.trim().toLowerCase();
    fixedPoolSize = fixedPoolSize > 0 ? fixedPoolSize : 32;
    queueCapacity = queueCapacity > 0 ? queueCapacity : 10_000;
    if (!type.equals("fixed") && !type.equals("virtual")) {
      throw new IllegalArgumentException("llm.executor.type must be fixed or virtual");
    }
  }
}
