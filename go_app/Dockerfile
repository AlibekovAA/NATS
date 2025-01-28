FROM golang:1.21 AS builder

WORKDIR /app

LABEL maintainer="aslan.alibekov.2017@mail.ru"
LABEL version="0.1.0"
LABEL description="Go NATS Client Application"

COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o main .

FROM alpine:latest

WORKDIR /app

LABEL maintainer="aslan.alibekov.2017@mail.ru"
LABEL version="0.1.0"
LABEL description="Go NATS Client Application"

RUN apk add --no-cache tzdata

COPY --from=builder /app/main .

ENV TZ=Europe/Moscow

ENTRYPOINT ["/app/main"]
