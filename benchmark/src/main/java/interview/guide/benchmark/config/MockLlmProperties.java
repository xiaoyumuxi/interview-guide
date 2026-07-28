package interview.guide.benchmark.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

import java.time.Duration;

@ConfigurationProperties("benchmark.mock")
public record MockLlmProperties(
    boolean enabled,
    String baseUrl,
    Duration delay
) {

  public MockLlmProperties {
    baseUrl = baseUrl == null || baseUrl.isBlank()
        ? "http://127.0.0.1:18081/v1"
        : baseUrl;
    delay = delay == null ? Duration.ofMillis(1_500) : delay;
  }
}
