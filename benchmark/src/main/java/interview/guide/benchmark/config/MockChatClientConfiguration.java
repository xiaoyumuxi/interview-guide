package interview.guide.benchmark.config;

import com.openai.client.OpenAIClient;
import com.openai.client.OpenAIClientImpl;
import com.openai.core.ClientOptions;
import com.openai.core.Timeout;
import com.openai.credential.BearerTokenCredential;
import io.micrometer.observation.ObservationRegistry;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.openai.OpenAiChatModel;
import org.springframework.ai.openai.OpenAiChatOptions;
import org.springframework.ai.openai.http.okhttp.SpringAiOpenAiHttpClient;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.time.Duration;

@Configuration
@ConditionalOnProperty(name = "benchmark.client.enabled", havingValue = "true", matchIfMissing = true)
public class MockChatClientConfiguration {

  @Bean
  ChatClient mockChatClient(
      MockLlmProperties properties,
      ObservationRegistry observationRegistry
  ) {
    Timeout timeout = Timeout.builder()
        .connect(Duration.ofSeconds(10))
        .read(Duration.ofMinutes(5))
        .build();
    ClientOptions options = ClientOptions.Companion.builder()
        .apiKey("benchmark-key")
        .credential(BearerTokenCredential.create("benchmark-key"))
        .baseUrl(properties.baseUrl())
        .timeout(timeout)
        .httpClient(SpringAiOpenAiHttpClient.builder().timeout(timeout).build())
        .build();
    OpenAIClient openAiClient = new OpenAIClientImpl(options);
    OpenAiChatOptions chatOptions = OpenAiChatOptions.builder()
        .model("mock-llm")
        .temperature(0.2)
        .build();
    OpenAiChatModel chatModel = OpenAiChatModel.builder()
        .openAiClient(openAiClient)
        .openAiClientAsync(openAiClient.async())
        .options(chatOptions)
        .observationRegistry(observationRegistry)
        .build();
    return ChatClient.builder(chatModel).build();
  }
}
