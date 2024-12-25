# BSW Test
Line-provider service accepts requests on listing and updating `event` entries, storing them in-memory. Every update is published to a RabbitMQ queue by line-provider service.

Rmq-worker subscribes to given queue and manages storage of relevant `event` entries in redis db. This service also updates `bet` entries from redis when the corresponding `event.state` gets updated on line-provider side.

Bet-maker service accepts requests on listing relevant `event` entries, listing and creating `bet` entries.

## How to use
Build -> ```docker compose up --build```

Line-provider -> http://localhost:8080/docs

Bet-maker -> http://localhost:8081/docs

## Future improvements

- Compensation mechanisms for cases when services suddenly became inaccessible
- Indexed redis storage to get rid of scan
- Refactor api and db logic for the sake of readability and testing
- Test coverage