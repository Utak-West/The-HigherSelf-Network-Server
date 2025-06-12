"""
Task Queue Service using Celery for the Higher Self Network Server.
Provides distributed task scheduling and execution for agent operations.
"""

import os
from datetime import timedelta

from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()

# Configure Celery with Redis as broker and backend
task_queue = Celery(
    "higherself_tasks",
    broker=os.environ.get("REDIS_URI", "redis://localhost:6379/0"),
    backend=os.environ.get("REDIS_URI", "redis://localhost:6379/0"),
)

# Configure Celery settings
task_queue.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "agents.*": {"queue": "agent_tasks"},
        "workflows.*": {"queue": "workflow_tasks"},
        "integrations.*": {"queue": "integration_tasks"},
        "mcp_tools.*": {"queue": "mcp_tasks"},
        "monitoring.*": {"queue": "monitoring_tasks"},
    },
    task_default_queue="default",
    worker_prefetch_multiplier=1,  # One task per worker to avoid blocking
    task_acks_late=True,  # Acknowledge tasks after execution
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks to prevent memory leaks
    task_soft_time_limit=600,  # 10 minute soft timeout
    task_time_limit=1200,  # 20 minute hard timeout
    worker_send_task_events=True,  # Send task-related events for monitoring
    task_send_sent_event=True,  # Enable events for monitoring
    task_track_started=True,  # Track when tasks are started
)

# Define periodic tasks
task_queue.conf.beat_schedule = {
    "check-system-health": {
        "task": "monitoring.tasks.check_system_health",
        "schedule": timedelta(minutes=5),
    },
    "sync-agent-registry": {
        "task": "agents.tasks.sync_agent_registry",
        "schedule": timedelta(minutes=10),
    },
    "refresh-mcp-tools": {
        "task": "mcp_tools.tasks.refresh_mcp_tools_registry",
        "schedule": timedelta(hours=1),
    },
    "purge-old-metrics": {
        "task": "monitoring.tasks.purge_old_metrics",
        "schedule": crontab(hour=3, minute=0),  # Run daily at 3am
    },
    "backup-database": {
        "task": "db.tasks.create_database_backup",
        "schedule": crontab(hour=1, minute=0),  # Run daily at 1am
    },
}

# Include task modules
task_queue.autodiscover_tasks(
    [
        "agents.tasks",
        "workflows.tasks",
        "integrations.tasks",
        "mcp_tools.tasks",
        "monitoring.tasks",
        "db.tasks",
    ]
)

# Create Prometheus metrics collector
if os.environ.get("ENABLE_METRICS", "true").lower() == "true":
    try:
        import time

        from prometheus_client import Counter, Gauge, Histogram

        # Task metrics
        TASK_LATENCY = Histogram(
            "celery_task_latency_seconds",
            "Task execution latency in seconds",
            ["task_name", "queue"],
        )
        TASK_ERRORS = Counter(
            "celery_task_errors_total", "Count of task errors", ["task_name", "queue"]
        )
        TASKS_ACTIVE = Gauge("celery_tasks_active", "Number of active tasks", ["queue"])

        # Task success/failure tracking
        @task_queue.on_after_configure.connect
        def setup_task_monitoring(sender, **kwargs):
            """Setup task monitoring hooks."""

            @task_queue.task_prerun.connect
            def task_prerun_handler(task_id, task, *args, **kwargs):
                """Handler executed before task runs."""
                task.start_time = time.time()
                queue = task.request.delivery_info.get("routing_key", "default")
                TASKS_ACTIVE.labels(queue=queue).inc()

            @task_queue.task_postrun.connect
            def task_postrun_handler(task_id, task, retval, state, *args, **kwargs):
                """Handler executed after task completes."""
                if hasattr(task, "start_time"):
                    queue = task.request.delivery_info.get("routing_key", "default")
                    latency = time.time() - task.start_time
                    TASK_LATENCY.labels(task_name=task.name, queue=queue).observe(
                        latency
                    )
                    TASKS_ACTIVE.labels(queue=queue).dec()

                    if state == "FAILURE":
                        TASK_ERRORS.labels(task_name=task.name, queue=queue).inc()

            logger.info("Celery prometheus metrics integration enabled")

    except ImportError:
        logger.warning("Prometheus client not installed, metrics will not be available")


# Register exception handlers
@task_queue.task
def handle_task_exception(task_id, exception, traceback, task_name):
    """Handle and log task exceptions."""
    logger.error(f"Task {task_name} (ID: {task_id}) failed with error: {exception}")
    logger.error(f"Traceback: {traceback}")

    # Record error in MongoDB
    try:
        from services.mongodb_service import mongo_service

        mongo_service.insert_one(
            "task_errors",
            {
                "task_id": task_id,
                "task_name": task_name,
                "error": str(exception),
                "traceback": traceback,
                "timestamp": time.time(),
            },
        )
    except Exception as e:
        logger.error(f"Failed to record task error in MongoDB: {e}")


@task_queue.task
def log_task_success(task_id, result, task_name, duration):
    """Log successful task completion for analytics."""
    if duration > 10:  # Only log tasks that took more than 10 seconds
        logger.info(
            f"Task {task_name} (ID: {task_id}) completed successfully in {duration:.2f}s"
        )

        # Record in MongoDB for analytics
        try:
            from services.mongodb_service import mongo_service

            mongo_service.insert_one(
                "task_performance",
                {
                    "task_id": task_id,
                    "task_name": task_name,
                    "duration": duration,
                    "timestamp": time.time(),
                },
            )
        except Exception as e:
            logger.error(f"Failed to record task performance in MongoDB: {e}")


# Helper function to create tasks with proper error handling
def create_task(func):
    """Decorator to create a task with proper error handling."""

    @task_queue.task(bind=True)
    def wrapper(self, *args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            log_task_success.delay(self.request.id, "Success", self.name, duration)
            return result
        except Exception as exc:
            handle_task_exception.delay(
                self.request.id, str(exc), traceback.format_exc(), self.name
            )
            raise

    return wrapper
