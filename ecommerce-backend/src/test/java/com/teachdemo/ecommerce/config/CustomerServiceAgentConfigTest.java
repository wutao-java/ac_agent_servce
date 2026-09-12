package com.teachdemo.ecommerce.config;

import static org.junit.jupiter.api.Assertions.assertEquals;

import com.sun.net.httpserver.HttpServer;
import com.teachdemo.ecommerce.dto.AgentChatRequest;
import com.teachdemo.ecommerce.security.AgentServiceAuthenticationFilter;
import com.teachdemo.ecommerce.service.RestCustomerServiceAgentClient;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.Map;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.web.client.RestClient;

class CustomerServiceAgentConfigTest {

    @Test
    void sendsServiceTokenWhenCallingAgent() throws IOException {
        AtomicReference<String> receivedToken = new AtomicReference<>();
        HttpServer server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        server.createContext("/chat", exchange -> {
            receivedToken.set(exchange.getRequestHeaders().getFirst(
                AgentServiceAuthenticationFilter.SERVICE_TOKEN_HEADER));
            byte[] response = "{\"answer\":\"ok\"}".getBytes(StandardCharsets.UTF_8);
            exchange.getResponseHeaders().set(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE);
            exchange.sendResponseHeaders(200, response.length);
            try (var responseBody = exchange.getResponseBody()) {
                responseBody.write(response);
            }
        });
        server.start();

        try {
            CustomerServiceAgentProperties properties = new CustomerServiceAgentProperties();
            properties.setBaseUrl("http://127.0.0.1:" + server.getAddress().getPort());
            properties.setAuthToken("service-token");
            RestClient restClient = new CustomerServiceAgentConfig()
                .customerServiceAgentRestClient(properties, RestClient.builder());

            new RestCustomerServiceAgentClient(restClient).chat(new AgentChatRequest(
                "cs-1", "user-1", "用户", "GOLD", "LOW", "你好", Map.of()));

            assertEquals("service-token", receivedToken.get());
        } finally {
            server.stop(0);
        }
    }
}
