
```
docker run -d  --name we-mp-rss  -p 8001:8001 -v ./data:/app/data  ghcr.io/rachelos/we-mp-rss:latest


docker run -d \
  --name we-mp-rss \
  -p 8001:8001 \
  -e DB=sqlite:///db.db \
  -e USERNAME:admin \
  -e PASSWORD:admin@123 \
  -e INTERVAL:600 \
  -v $(pwd)/db.db:/app/db.db \
  ghcr.io/rachelos/we-mp-rss:stable-used
```

```
docker run -d \
  --name we-mp-rss \
  -p 8001:8001 \
  -e DB=sqlite:///db.db \
  -e USERNAME:admin \
  -e PASSWORD:admin@123 \
  -e INTERVAL:600 \
  -v $(pwd)/db.db:/app/db.db \
  ghcr.io/rachelos/we-mp-rss:stable-used
```




```yml
services:
  we-mp-rss:
    image: ghcr.io/rachelos/we-mp-rss:latest
    container_name: we-mp-rss
    environment:
      DB: mysql+pymysql://root:root@localhost:3306/we-mp-rss?charset=utf8mb4
      USERNAME: admin
      MYSQL_USER: admin
      PASSWORD: admin@123
    ports:
      - "8001:8001"
    volumes:
      - data:/app/data
    networks:
      - pub-network

volumes:
  data:

networks:
  pub-network:
      external: true
```
