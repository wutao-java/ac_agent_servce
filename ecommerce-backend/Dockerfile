# syntax=docker/dockerfile:1.6
FROM maven:3.9.6-eclipse-temurin-17 AS builder
WORKDIR /workspace

COPY docker ./docker
RUN mkdir -p /root/.m2 \
    && cp docker/maven-settings.xml /root/.m2/settings.xml

COPY pom.xml .

# 课程发布包可以携带 docker/m2-cache.tar.gz，先预热容器内 Maven 仓库；缺失依赖再走远程下载。
RUN --mount=type=cache,target=/root/.m2/repository \
    mkdir -p /root/.m2/repository \
    && if [ -f docker/m2-cache.tar.gz ]; then tar -xzf docker/m2-cache.tar.gz -C /root/.m2/repository; fi \
    && find /root/.m2/repository \( -name '*.lastUpdated' -o -name 'resolver-status.properties' \) -delete \
    && if [ -f docker/m2-cache.tar.gz ]; then \
        mvn -o -s /root/.m2/settings.xml -q -DskipTests dependency:go-offline \
        || mvn -s /root/.m2/settings.xml -q -DskipTests dependency:go-offline; \
    else \
        mvn -s /root/.m2/settings.xml -q -DskipTests dependency:go-offline; \
    fi

COPY src ./src
# BuildKit 缓存 /root/.m2/repository，避免同一台机器反复构建时重复下载依赖。
RUN --mount=type=cache,target=/root/.m2/repository \
    mvn -s /root/.m2/settings.xml -q -DskipTests package

FROM eclipse-temurin:17-jre
WORKDIR /app
COPY --from=builder /workspace/target/ecommerce-backend-0.0.1-SNAPSHOT.jar app.jar
EXPOSE 8081
ENTRYPOINT ["java", "-jar", "app.jar"]
