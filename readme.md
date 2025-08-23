## API Design

GET /agents

payload

```
{}
```

response

```json
{
  "agents": [
    {
      "id": UUID,
      "type": "manager" | "worker"
      "name": string,
      "description": string
    }
  ]
}
```

POST /chat_intro - Websocket

Messages exclusively with the manager for the introduction of the interaction.

payload

```json
{
  "messages": [
    {
      "role": "user" | "system",
      "content": string
    }
  ],
  "stop": bool
}
```

response

```json
{
  "messages": [
    {
      "role": "user" | "system",
      "content": string
    }
  ],
  "stop": bool
}
```

GET /chats - WebSocket

payload

```json
{
  "chats": [
    {
      "agent_id": UUID,
      "messages": [
        {
          "agent_event_type": "chatter" | "question" | "final-answer"
          "role": "user" | "system",
          "content": string,
        }
      ],
    }
  ]
  "stop": bool
}
```

response

```json
{
  "chats": [
    {
      "agent_id": UUID,
      "messages": [
        {
          "agent_event_type": "chatter" | "question" | "final-answer"
          "role": "user" | "system",
          "content": string,
        }
      ],
    }
  ]
  "stop": bool
}
```
