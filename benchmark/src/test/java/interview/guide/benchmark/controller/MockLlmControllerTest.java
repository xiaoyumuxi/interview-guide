package interview.guide.benchmark.controller;

import interview.guide.benchmark.config.MockLlmProperties;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.time.Duration;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

class MockLlmControllerTest {

  @Test
  @DisplayName("Mock Endpoint 返回 OpenAI Chat Completions 兼容结构")
  void returnsOpenAiCompatibleResponse() {
    MockLlmController controller = new MockLlmController(
        new MockLlmProperties(
            true,
            "http://127.0.0.1:18081/v1",
            Duration.ZERO
        )
    );

    Map<String, Object> response = controller.completion(
        Map.of("model", "mock-llm")
    );

    assertThat(response)
        .containsEntry("object", "chat.completion")
        .containsEntry("model", "mock-llm");
    assertThat(response.get("choices")).asList().hasSize(1);
    assertThat(response.get("usage")).isInstanceOf(Map.class);
  }
}
