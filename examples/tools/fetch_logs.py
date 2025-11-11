import sys
import json

LOGS = {
    "logs": [
        {
            "timestamp": "2025-01-01 12:00:00",
            "message": "Sample log entry 1",
            "level": "INFO",
            "source": "api",
            "tags": ["startup", "initialization"],
            "metadata": {
                "duration": 100,
                "status": "info",
            },
        },
        {
            "timestamp": "2025-01-01 12:00:01",
            "message": "Sample log entry 2",
            "level": "ERROR",
            "source": "worker",
            "tags": ["error", "database"],
            "metadata": {
                "duration": 250,
                "status": "error",
            },
        },
        {
            "timestamp": "2025-01-01 12:00:02",
            "message": "Sample log entry 3",
            "level": "WARNING",
            "source": "api",
            "tags": ["warning", "performance"],
            "metadata": {
                "duration": 180,
                "status": "warning",
            },
        },
        {
            "timestamp": "2025-01-01 12:00:03",
            "message": "Sample log entry 4",
            "level": "INFO",
            "source": "scheduler",
            "tags": ["cron", "background"],
            "metadata": {
                "duration": 50,
                "status": "info",
            },
        },
    ]
}


def main():
    if len(sys.argv) != 4:
        print("Usage: python demo_logs.py <app> <from_time> <to_time>", file=sys.stderr)
        print(
            "Example: python demo_logs.py api '2025-01-01 12:00:00' '2025-01-01 12:00:02'",
            file=sys.stderr,
        )
        sys.exit(1)

    app = sys.argv[1]

    filtered_logs = [log for log in LOGS["logs"] if log["source"] == app]

    print(json.dumps({"logs": filtered_logs}, indent=2))


if __name__ == "__main__":
    main()
