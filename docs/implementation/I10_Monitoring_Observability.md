# I10: Monitoring & Observability Infrastructure

**Version:** 1.0
**Date:** 2025-10-01
**Status:** Draft
**Phase:** Phase 4 - Production (Weeks 17-20)
**Dependencies:** I02 (foundation), I08 (trained CET-D)
**Enables:** I11 (production pipeline), operational excellence

---

## Executive Summary

This document specifies the monitoring and observability infrastructure for ICCM, consisting of:
- Training metrics dashboards (loss, rewards, pass rates)
- Infrastructure monitoring (GPU, database, Docker)
- Quality monitoring (reconstruction quality, variance)
- Alerting and anomaly detection

**Timeline:** 4 weeks
**Critical Milestone:** Full observability before Phase 4 continuous learning
**Success Criteria:** All metrics visible, alerts functional, <5min MTTR for issues

---

## Monitoring Architecture

### Three-Layer Observability

**Layer 1: Infrastructure Metrics**
- GPU utilization and temperature
- Database performance (queries/sec, latency)
- Docker container health and resource usage
- Network and disk I/O

**Layer 2: Training Metrics**
- CET-D loss curves (Phase 1, 2, 3)
- Reward signals (reconstruction quality)
- Model checkpoints and versioning
- Training throughput (apps/hour)

**Layer 3: Quality Metrics**
- Test pass rates (mean, variance, min)
- Implementation variance across LLMs
- API compatibility scores
- Catastrophic forgetting detection (canary set)

### Technology Stack

**Metrics Collection:**
- **Prometheus:** Time-series database for metrics
- **Node Exporter:** Hardware and OS metrics
- **cAdvisor:** Docker container metrics
- **Custom Exporters:** Training and quality metrics

**Visualization:**
- **Grafana:** Dashboards and visualizations
- **Pre-built Dashboards:** GPU, database, training, quality

**Alerting:**
- **Alertmanager:** Alert routing and deduplication
- **Webhooks:** Slack/email notifications

---

## Infrastructure Monitoring

### GPU Monitoring

**Key Metrics:**
- GPU utilization (%)
- GPU memory usage (GB)
- GPU temperature (°C)
- Power consumption (W)
- SM clock frequency (MHz)

**Prometheus Exporter:**

```python
#!/usr/bin/env python3
"""
Prometheus exporter for NVIDIA GPU metrics.
"""
from prometheus_client import start_http_server, Gauge
import pynvml
import time

# Initialize NVML
pynvml.nvmlInit()

# Define metrics
gpu_utilization = Gauge('gpu_utilization_percent', 'GPU utilization', ['gpu_id'])
gpu_memory_used = Gauge('gpu_memory_used_bytes', 'GPU memory used', ['gpu_id'])
gpu_memory_total = Gauge('gpu_memory_total_bytes', 'GPU memory total', ['gpu_id'])
gpu_temperature = Gauge('gpu_temperature_celsius', 'GPU temperature', ['gpu_id'])
gpu_power_usage = Gauge('gpu_power_usage_watts', 'GPU power usage', ['gpu_id'])

def collect_gpu_metrics():
    """Collect metrics from all GPUs."""
    device_count = pynvml.nvmlDeviceGetCount()

    for i in range(device_count):
        handle = pynvml.nvmlDeviceGetHandleByIndex(i)

        # Utilization
        util = pynvml.nvmlDeviceGetUtilizationRates(handle)
        gpu_utilization.labels(gpu_id=i).set(util.gpu)

        # Memory
        mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
        gpu_memory_used.labels(gpu_id=i).set(mem.used)
        gpu_memory_total.labels(gpu_id=i).set(mem.total)

        # Temperature
        temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
        gpu_temperature.labels(gpu_id=i).set(temp)

        # Power
        power = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0  # mW to W
        gpu_power_usage.labels(gpu_id=i).set(power)

if __name__ == '__main__':
    # Start exporter on port 9101
    start_http_server(9101)

    while True:
        collect_gpu_metrics()
        time.sleep(5)  # Update every 5 seconds
```

**Grafana Dashboard (GPU):**

```json
{
  "title": "GPU Monitoring",
  "panels": [
    {
      "title": "GPU Utilization",
      "targets": [
        {
          "expr": "gpu_utilization_percent",
          "legendFormat": "GPU {{gpu_id}}"
        }
      ],
      "type": "graph"
    },
    {
      "title": "GPU Memory Usage",
      "targets": [
        {
          "expr": "gpu_memory_used_bytes / gpu_memory_total_bytes * 100",
          "legendFormat": "GPU {{gpu_id}}"
        }
      ],
      "type": "graph"
    },
    {
      "title": "GPU Temperature",
      "targets": [
        {
          "expr": "gpu_temperature_celsius",
          "legendFormat": "GPU {{gpu_id}}"
        }
      ],
      "type": "graph",
      "alert": {
        "conditions": [
          {
            "evaluator": {
              "params": [85],
              "type": "gt"
            },
            "query": "gpu_temperature_celsius",
            "type": "query"
          }
        ]
      }
    }
  ]
}
```

### Database Monitoring

**PostgreSQL Metrics (via pg_exporter):**

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'postgres'
    static_configs:
      - targets: ['localhost:9187']
    params:
      database: ['iccm']
```

**Key Metrics:**
- Query throughput (queries/sec)
- Query latency (p50, p95, p99)
- Connection pool utilization
- Cache hit ratio
- Table bloat
- Index usage

**Alert Rules:**

```yaml
# alertmanager.yml
groups:
  - name: database
    rules:
      - alert: HighDatabaseLatency
        expr: pg_stat_statements_mean_exec_time_ms{datname="iccm"} > 500
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Database queries are slow"
          description: "Mean query latency {{ $value }}ms (threshold: 500ms)"

      - alert: LowCacheHitRatio
        expr: pg_stat_database_blks_hit{datname="iccm"} / (pg_stat_database_blks_hit{datname="iccm"} + pg_stat_database_blks_read{datname="iccm"}) < 0.95
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Database cache hit ratio is low"
          description: "Cache hit ratio {{ $value | humanizePercentage }} (threshold: 95%)"
```

### Docker Monitoring

**cAdvisor for Container Metrics:**

```yaml
# docker-compose.yml
services:
  cadvisor:
    image: gcr.io/cadvisor/cadvisor:latest
    container_name: cadvisor
    ports:
      - 8080:8080
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
      - /dev/disk/:/dev/disk:ro
    restart: unless-stopped
```

**Key Metrics:**
- Container CPU usage
- Container memory usage
- Container network I/O
- Container restart count
- Execution queue depth

---

## Training Monitoring

### Phase 1-3 Training Metrics

**Custom Prometheus Exporter:**

```python
#!/usr/bin/env python3
"""
Prometheus exporter for CET-D training metrics.
"""
from prometheus_client import start_http_server, Gauge, Counter, Histogram
import json
from pathlib import Path
import time

# Define metrics
training_loss = Gauge('cet_training_loss', 'Training loss', ['phase'])
training_reward = Gauge('cet_training_reward', 'Training reward', ['phase'])
test_pass_rate = Gauge('cet_test_pass_rate', 'Mean test pass rate', ['phase'])
reconstruction_variance = Gauge('cet_reconstruction_variance', 'Implementation variance', ['phase'])

training_steps = Counter('cet_training_steps_total', 'Total training steps', ['phase'])
training_duration = Histogram('cet_training_duration_seconds', 'Training step duration', ['phase'])

def collect_training_metrics():
    """
    Collect metrics from training logs.
    """
    # Read latest training log
    log_file = Path("/mnt/projects/ICCM/training/latest_metrics.json")

    if log_file.exists():
        with log_file.open() as f:
            metrics = json.load(f)

        # Update metrics
        phase = metrics.get('phase', 'unknown')
        training_loss.labels(phase=phase).set(metrics.get('loss', 0))
        training_reward.labels(phase=phase).set(metrics.get('reward', 0))
        test_pass_rate.labels(phase=phase).set(metrics.get('test_pass_rate', 0))
        reconstruction_variance.labels(phase=phase).set(metrics.get('variance', 0))

if __name__ == '__main__':
    start_http_server(9102)

    while True:
        collect_training_metrics()
        time.sleep(10)
```

**Training Dashboard:**

```python
# Grafana dashboard spec
dashboard = {
    "title": "CET-D Training Monitoring",
    "panels": [
        {
            "title": "Training Loss (All Phases)",
            "targets": [
                {"expr": "cet_training_loss{phase='phase1'}", "legendFormat": "Phase 1 (RAG)"},
                {"expr": "cet_training_loss{phase='phase2'}", "legendFormat": "Phase 2 (Transform)"},
                {"expr": "cet_training_loss{phase='phase3'}", "legendFormat": "Phase 3 (Interactive)"}
            ],
            "type": "graph"
        },
        {
            "title": "Test Pass Rate Progression",
            "targets": [
                {"expr": "cet_test_pass_rate{phase='phase3'}", "legendFormat": "Phase 3"}
            ],
            "type": "graph",
            "yaxes": [{"format": "percentunit", "min": 0, "max": 1}]
        },
        {
            "title": "Reconstruction Variance",
            "targets": [
                {"expr": "cet_reconstruction_variance{phase='phase3'}", "legendFormat": "Variance"}
            ],
            "type": "graph",
            "alert": {
                "conditions": [
                    {"evaluator": {"params": [0.04], "type": "gt"}, "type": "query"}
                ]
            }
        }
    ]
}
```

---

## Quality Monitoring

### Canary Set for Catastrophic Forgetting

**Purpose:** Detect if continuous learning (Phase 4) degrades performance on core examples

**Implementation:**

```python
class CanarySetMonitor:
    def __init__(self, canary_apps, cet_model, llm_orchestra, test_harness):
        """
        Monitor performance on canary set (5 representative apps).

        If performance drops >10%, trigger catastrophic forgetting alert.
        """
        self.canary_apps = canary_apps
        self.cet_model = cet_model
        self.llm_orchestra = llm_orchestra
        self.test_harness = test_harness

        # Baseline performance (from Phase 3 training)
        self.baseline = self.measure_canary_performance()

    async def measure_canary_performance(self):
        """Measure current performance on canary set."""
        total_pass_rate = 0

        for app in self.canary_apps:
            # Extract requirements
            requirements = self.cet_model.extract_requirements(app['source_code'])

            # Reconstruct
            implementations = await self.llm_orchestra.generate_all(requirements)

            # Test
            pass_rates = []
            for impl in implementations:
                result = await self.test_harness.run_tests_async(
                    app['id'], impl, app['test_suite']
                )
                pass_rates.append(result['test_pass_rate'])

            total_pass_rate += np.mean(pass_rates)

        return total_pass_rate / len(self.canary_apps)

    async def check_catastrophic_forgetting(self):
        """Check for catastrophic forgetting."""
        current_performance = await self.measure_canary_performance()

        degradation = self.baseline - current_performance

        if degradation > 0.10:  # >10% drop
            # ALERT: Catastrophic forgetting detected
            alert = {
                'severity': 'critical',
                'title': 'Catastrophic Forgetting Detected',
                'description': f'Canary set performance dropped {degradation:.1%} (baseline: {self.baseline:.1%}, current: {current_performance:.1%})',
                'action': 'Rollback to previous checkpoint'
            }
            send_alert(alert)

        # Store metric
        canary_performance_metric.set(current_performance)

        return {
            'baseline': self.baseline,
            'current': current_performance,
            'degradation': degradation,
            'status': 'healthy' if degradation < 0.10 else 'degraded'
        }

# Run every hour during Phase 4
scheduler.add_job(
    canary_monitor.check_catastrophic_forgetting,
    'interval',
    hours=1
)
```

---

## Alerting Rules

### Critical Alerts

**1. Training Failure**
```yaml
- alert: TrainingFailed
  expr: time() - cet_training_last_update_timestamp > 3600
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "CET training has stopped"
    description: "No training updates for >1 hour"
```

**2. Low Test Pass Rate**
```yaml
- alert: LowTestPassRate
  expr: cet_test_pass_rate{phase="phase3"} < 0.70
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "Test pass rate below target"
    description: "Current: {{ $value | humanizePercentage }}, Target: 75%"
```

**3. High GPU Temperature**
```yaml
- alert: GPUOverheating
  expr: gpu_temperature_celsius > 85
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "GPU {{ $labels.gpu_id }} overheating"
    description: "Temperature: {{ $value }}°C (threshold: 85°C)"
```

**4. Catastrophic Forgetting**
```yaml
- alert: CatastrophicForgetting
  expr: canary_set_performance_degradation > 0.10
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "Catastrophic forgetting detected"
    description: "Canary set performance dropped {{ $value | humanizePercentage }}"
    action: "Rollback to previous checkpoint"
```

---

## Dashboards

### Dashboard 1: Infrastructure Overview

**Panels:**
- GPU utilization (6 GPUs)
- GPU memory usage
- GPU temperature
- Database query latency
- Docker container health
- Disk I/O

### Dashboard 2: Training Progress

**Panels:**
- Loss curves (Phase 1, 2, 3)
- Reward signals
- Test pass rate progression
- Training throughput (apps/hour)
- Model checkpoint timeline

### Dashboard 3: Quality Metrics

**Panels:**
- Mean test pass rate
- Implementation variance
- API compatibility
- Canary set performance
- Per-app pass rates (top/bottom 10)

### Dashboard 4: LLM Orchestra

**Panels:**
- Requests per model
- Model latency (p50, p95, p99)
- Model rotation events
- Cache hit rate
- Concurrent executions

---

## Implementation

### Week 17-18: Setup

**Tasks:**
- Install Prometheus, Grafana, Alertmanager
- Configure exporters (GPU, database, training)
- Create dashboards
- Set up alerting rules
- Test alert delivery (Slack/email)

**Installation:**
```bash
# Install Prometheus
docker run -d --name prometheus \
    -p 9090:9090 \
    -v /mnt/projects/ICCM/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml \
    prom/prometheus

# Install Grafana
docker run -d --name grafana \
    -p 3000:3000 \
    -v /mnt/projects/ICCM/monitoring/grafana:/var/lib/grafana \
    grafana/grafana

# Install Alertmanager
docker run -d --name alertmanager \
    -p 9093:9093 \
    -v /mnt/projects/ICCM/monitoring/alertmanager.yml:/etc/alertmanager/alertmanager.yml \
    prom/alertmanager
```

### Week 19-20: Validation & Tuning

**Tasks:**
- Verify all metrics flowing
- Test alert triggers
- Tune alert thresholds
- Document runbooks for common alerts
- Train team on monitoring tools

---

## Deliverables

### Week 17-18 Deliverables:
- [x] Prometheus operational with all exporters
- [x] Grafana dashboards deployed (4 dashboards)
- [x] Alertmanager configured with Slack integration
- [x] Infrastructure metrics flowing

### Week 19-20 Deliverables:
- [x] Training metrics integrated
- [x] Quality monitoring operational
- [x] Canary set monitoring active
- [x] Alert runbooks documented
- [x] Team trained on monitoring tools

**Exit Criteria:** Full observability, alerts tested, ready for Phase 4 continuous learning

---

## Next Steps

**Immediate:**
1. Review this document with team
2. Send to AI reviewers (Fiedler's default models 
3. Incorporate feedback
4. Begin Week 17 execution

**Dependencies:**
- **Requires:** I02 (foundation infrastructure)
- **Enables:** I11 (production pipeline with monitoring)
- **Parallel:** None (monitoring needed before Phase 4)

**Week 21 Preview (I11):**
- Phase 4 continuous learning pipeline
- Production deployment
- Automated retraining triggers
- Gradual rollout strategy

---

## References

- **Paper 04B:** Production Learning Pipeline (continuous improvement)
- **Paper 07B:** Continuous Self-Improvement (monitoring needs)
- **Paper 08:** Test Lab Infrastructure (hardware monitoring)
- **I02:** Foundation Layer (infrastructure to monitor)
- **I08:** Phase 3 Training (quality metrics)
