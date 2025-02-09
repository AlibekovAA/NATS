package nats

import (
	"time"

	"go_app/internal/infrastructure/logger"

	"github.com/nats-io/nats.go"
)

type Client struct {
	conn *nats.Conn
	log  *logger.Logger
}

func New(addr string, log *logger.Logger) (*Client, error) {
	opts := []nats.Option{
		nats.MaxReconnects(5),
		nats.ReconnectWait(2 * time.Second),
	}

	conn, err := nats.Connect(addr, opts...)
	if err != nil {
		return nil, err
	}

	return &Client{
		conn: conn,
		log:  log,
	}, nil
}

func (c *Client) makeHandler(fn func([]byte) ([]byte, error)) nats.MsgHandler {
	return func(msg *nats.Msg) {
		response, err := fn(msg.Data)
		if err != nil {
			msg.Respond([]byte(err.Error()))
			return
		}
		if response != nil {
			msg.Respond(response)
		}
	}
}

func (c *Client) Subscribe(topic string, handler func([]byte) ([]byte, error)) error {
	_, err := c.conn.Subscribe(topic, c.makeHandler(handler))
	if err != nil {
		return err
	}
	return nil
}

func (c *Client) Close() error {
	c.log.Println("Closing NATS connection...")
	return c.conn.Drain()
}
