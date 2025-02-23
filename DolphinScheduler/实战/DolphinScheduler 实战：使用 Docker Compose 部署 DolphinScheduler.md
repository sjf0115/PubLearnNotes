

```yaml
version: "3.8"

services:
  dolphinscheduler-postgresql:
    image: bitnami/postgresql:11.11.0
    ports:
      - "5432:5432"
    profiles: ["all", "schema"]
    environment:
      POSTGRESQL_USERNAME: root
      POSTGRESQL_PASSWORD: root
      POSTGRESQL_DATABASE: dolphinscheduler
    volumes:
      - dolphinscheduler-postgresql:/bitnami/postgresql
    healthcheck:
      test: ["CMD", "bash", "-c", "cat < /dev/null > /dev/tcp/127.0.0.1/5432"]
      interval: 5s
      timeout: 60s
      retries: 120
    networks:
      - dolphinscheduler

  dolphinscheduler-zookeeper:
    image: bitnami/zookeeper:3.6.2
    profiles: ["all"]
    environment:
      ALLOW_ANONYMOUS_LOGIN: "yes"
      ZOO_4LW_COMMANDS_WHITELIST: srvr,ruok,wchs,cons
    volumes:
      - dolphinscheduler-zookeeper:/bitnami/zookeeper
    healthcheck:
      test: ["CMD", "bash", "-c", "cat < /dev/null > /dev/tcp/127.0.0.1/2181"]
      interval: 5s
      timeout: 60s
      retries: 120
    networks:
      - dolphinscheduler

  dolphinscheduler-schema-initializer:
    image: ${HUB}/dolphinscheduler-tools:${TAG}
    env_file: .env
    profiles: ["schema"]
    command: [ tools/bin/upgrade-schema.sh ]
    depends_on:
      dolphinscheduler-postgresql:
        condition: service_healthy
    volumes:
      - dolphinscheduler-logs:/opt/dolphinscheduler/logs
      - dolphinscheduler-shared-local:/opt/soft
      - dolphinscheduler-resource-local:/dolphinscheduler
    networks:
      - dolphinscheduler

  dolphinscheduler-api:
    image: ${HUB}/dolphinscheduler-api:${TAG}
    ports:
      - "12345:12345"
      - "25333:25333"
    profiles: ["all"]
    env_file: .env
    healthcheck:
      test: [ "CMD", "curl", "http://localhost:12345/dolphinscheduler/actuator/health" ]
      interval: 30s
      timeout: 5s
      retries: 3
    depends_on:
      dolphinscheduler-zookeeper:
        condition: service_healthy
    volumes:
      - dolphinscheduler-logs:/opt/dolphinscheduler/logs
      - dolphinscheduler-shared-local:/opt/soft
      - dolphinscheduler-resource-local:/dolphinscheduler
    networks:
      - dolphinscheduler

  dolphinscheduler-alert:
    image: ${HUB}/dolphinscheduler-alert-server:${TAG}
    profiles: ["all"]
    env_file: .env
    healthcheck:
      test: [ "CMD", "curl", "http://localhost:50053/actuator/health" ]
      interval: 30s
      timeout: 5s
      retries: 3
    volumes:
      - dolphinscheduler-logs:/opt/dolphinscheduler/logs
    networks:
      - dolphinscheduler

  dolphinscheduler-master:
    image: ${HUB}/dolphinscheduler-master:${TAG}
    profiles: ["all"]
    env_file: .env
    healthcheck:
      test: [ "CMD", "curl", "http://localhost:5679/actuator/health" ]
      interval: 30s
      timeout: 5s
      retries: 3
    depends_on:
      dolphinscheduler-zookeeper:
        condition: service_healthy
    volumes:
      - dolphinscheduler-logs:/opt/dolphinscheduler/logs
      - dolphinscheduler-shared-local:/opt/soft
    networks:
      - dolphinscheduler

  dolphinscheduler-worker:
    image: ${HUB}/dolphinscheduler-worker:${TAG}
    profiles: ["all"]
    env_file: .env
    healthcheck:
      test: [ "CMD", "curl", "http://localhost:1235/actuator/health" ]
      interval: 30s
      timeout: 5s
      retries: 3
    depends_on:
      dolphinscheduler-zookeeper:
        condition: service_healthy
    volumes:
      - dolphinscheduler-worker-data:/tmp/dolphinscheduler
      - dolphinscheduler-logs:/opt/dolphinscheduler/logs
      - dolphinscheduler-shared-local:/opt/soft
      - dolphinscheduler-resource-local:/dolphinscheduler
    networks:
      - dolphinscheduler

networks:
  dolphinscheduler:
    driver: bridge

volumes:
  dolphinscheduler-postgresql:
  dolphinscheduler-zookeeper:
  dolphinscheduler-worker-data:
  dolphinscheduler-logs:
  dolphinscheduler-shared-local:
  dolphinscheduler-resource-local:

```




```yaml
version: "3.8"

services:
  dolphinscheduler-zookeeper:
    image: bitnami/zookeeper:3.6.2
    profiles: ["all"]
    environment:
      ALLOW_ANONYMOUS_LOGIN: "yes"
      ZOO_4LW_COMMANDS_WHITELIST: srvr,ruok,wchs,cons
    volumes:
      - dolphinscheduler-zookeeper:/bitnami/zookeeper
    healthcheck:
      test: ["CMD", "bash", "-c", "cat < /dev/null > /dev/tcp/127.0.0.1/2181"]
      interval: 5s
      timeout: 60s
      retries: 120
    networks:
      - dolphinscheduler

  dolphinscheduler-schema-initializer:
    image: ${HUB}/dolphinscheduler-tools:${TAG}
    env_file: .env
    profiles: ["schema"]
    command: [ tools/bin/upgrade-schema.sh ]
    depends_on:
      postgresql:
        condition: service_healthy
    volumes:
      - dolphinscheduler-logs:/opt/dolphinscheduler/logs
      - dolphinscheduler-shared-local:/opt/soft
      - dolphinscheduler-resource-local:/dolphinscheduler
    networks:
      - dolphinscheduler

  dolphinscheduler-api:
    image: ${HUB}/dolphinscheduler-api:${TAG}
    ports:
      - "12345:12345"
      - "25333:25333"
    profiles: ["all"]
    env_file: .env
    healthcheck:
      test: [ "CMD", "curl", "http://localhost:12345/dolphinscheduler/actuator/health" ]
      interval: 30s
      timeout: 5s
      retries: 3
    depends_on:
      dolphinscheduler-zookeeper:
        condition: service_healthy
    volumes:
      - dolphinscheduler-logs:/opt/dolphinscheduler/logs
      - dolphinscheduler-shared-local:/opt/soft
      - dolphinscheduler-resource-local:/dolphinscheduler
    networks:
      - dolphinscheduler

  dolphinscheduler-alert:
    image: ${HUB}/dolphinscheduler-alert-server:${TAG}
    profiles: ["all"]
    env_file: .env
    healthcheck:
      test: [ "CMD", "curl", "http://localhost:50053/actuator/health" ]
      interval: 30s
      timeout: 5s
      retries: 3
    volumes:
      - dolphinscheduler-logs:/opt/dolphinscheduler/logs
    networks:
      - dolphinscheduler

  dolphinscheduler-master:
    image: ${HUB}/dolphinscheduler-master:${TAG}
    profiles: ["all"]
    env_file: .env
    healthcheck:
      test: [ "CMD", "curl", "http://localhost:5679/actuator/health" ]
      interval: 30s
      timeout: 5s
      retries: 3
    depends_on:
      dolphinscheduler-zookeeper:
        condition: service_healthy
    volumes:
      - dolphinscheduler-logs:/opt/dolphinscheduler/logs
      - dolphinscheduler-shared-local:/opt/soft
    networks:
      - dolphinscheduler

  dolphinscheduler-worker:
    image: ${HUB}/dolphinscheduler-worker:${TAG}
    profiles: ["all"]
    env_file: .env
    healthcheck:
      test: [ "CMD", "curl", "http://localhost:1235/actuator/health" ]
      interval: 30s
      timeout: 5s
      retries: 3
    depends_on:
      dolphinscheduler-zookeeper:
        condition: service_healthy
    volumes:
      - dolphinscheduler-worker-data:/tmp/dolphinscheduler
      - dolphinscheduler-logs:/opt/dolphinscheduler/logs
      - dolphinscheduler-shared-local:/opt/soft
      - dolphinscheduler-resource-local:/dolphinscheduler
    networks:
      - dolphinscheduler

networks:
  dolphinscheduler:
    driver: bridge

volumes:
  dolphinscheduler-postgresql:
  dolphinscheduler-zookeeper:
  dolphinscheduler-worker-data:
  dolphinscheduler-logs:
  dolphinscheduler-shared-local:
  dolphinscheduler-resource-local:

```
