# Real-Time Architecture (Bonus)

## Overview

1,000 surveys/min with sub-5 second latency to dashboards.

## Architecture

```
Web/Mobile/Webhook
        |
        v
   API Gateway (FastAPI)
        |
        v
   Apache Kafka
   (survey-raw topic)
        |
        v
   Apache Flink
   - Validate rating
   - Normalize email
   - Dedupe (stateful)
   - Enrich with user data
        |
        v
   PostgreSQL
        |
        v
   Metabase (BI)
```

## Key Decisions

| Choice | Why | Alternative Considered |
|--------|-----|------------------------|
| **Kafka** | Replay capability, multiple consumers, handles bursts | SQS (no replay, single consumer) |
| **Flink** | Same cleaning logic as batch, stateful dedup, low latency | Spark Streaming (higher latency), Lambda (stateless) |
| **PostgreSQL** | 17 writes/sec is trivial. Simple, familiar, ACID | ClickHouse (overkill at this scale, migrate later if needed) |

## Failure Handling

- **Kafka**: Retains 7 days, replay if downstream crashes
- **Flink**: Checkpoints every 30s, restarts from last checkpoint
- **Invalid data**: Dead letter queue for manual review

## Latency

- API → Kafka: ~50ms
- Kafka → Flink: ~200ms
- Flink → Postgres: ~500ms
- **Total: ~1-2s**

## Scaling Path

| Volume | Action |
|--------|--------|
| 1,000/min (now) | Single instance of everything |
| 10,000/min | Add Kafka partitions, Flink parallelism |
| 100M+ rows | Migrate PostgreSQL → ClickHouse for faster aggregations |

## Cost Estimate

~$500-800/month (managed Kafka + Flink + PostgreSQL on AWS/GCP)

## What I'd Add Later

- **Sentiment analysis**: DistilBERT on `comment_text` to understand *why* ratings are low (e.g., HR's 3.66 rating → "40% mention ticket response time")
- **Slack alerts**: Notify team when sentiment < -0.5 AND rating <= 2
- **Anomaly detection**: Z-score on department averages to catch sudden drops

## Trade-offs vs Batch

| Batch | Real-Time |
|-------|-----------|
| ~$0, run when needed | ~$700/month, always on |
| Hours/days latency | Seconds latency |
| Simple (one script) | Complex (Kafka + Flink + monitoring) |

Real-time justified when business needs instant alerts on negative feedback.
