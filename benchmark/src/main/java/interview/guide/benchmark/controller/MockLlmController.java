package interview.guide.benchmark.controller;

import interview.guide.benchmark.config.MockLlmProperties;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.Instant;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/v1")
@ConditionalOnProperty(name = "benchmark.mock.enabled", havingValue = "true")
public class MockLlmController {

  private final MockLlmProperties properties;

  public MockLlmController(MockLlmProperties properties) {
    this.properties = properties;
  }

  @PostMapping(value = "/chat/completions", produces = MediaType.APPLICATION_JSON_VALUE)
  public Map<String, Object> completion(@RequestBody(required = false) Map<String, Object> request) {
    try {
      Thread.sleep(properties.delay());
    } catch (InterruptedException e) {
      Thread.currentThread().interrupt();
      throw new IllegalStateException("Mock LLM delay interrupted", e);
    }

    String model = request == null ? "mock-llm" : String.valueOf(request.getOrDefault("model", "mock-llm"));
    return Map.of(
        "id", "chatcmpl-benchmark",
        "object", "chat.completion",
        "created", Instant.now().getEpochSecond(),
        "model", model,
        "choices", List.of(Map.of(
            "index", 0,
            "message", Map.of(
                "role", "assistant",
                "content", "fixed benchmark response"
            ),
            "finish_reason", "stop"
        )),
        "usage", Map.of(
            "prompt_tokens", 12,
            "completion_tokens", 3,
            "total_tokens", 15
        )
    );
  }
}
