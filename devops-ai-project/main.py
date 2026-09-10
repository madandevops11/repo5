import os
import requests

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from kubernetes import client, config


# ============================================================
# Configuration
# ============================================================

OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://172.31.20.63:11434"
)

MODEL = os.getenv(
    "OLLAMA_MODEL",
    "qwen2.5:1.5b"
)


# ============================================================
# FastAPI
# ============================================================

app = FastAPI(
    title="AI Kubernetes Log Analyzer",
    version="6.1"
)


# ============================================================
# Kubernetes Client
# ============================================================

try:
    config.load_incluster_config()
except Exception:
    try:
        config.load_kube_config()
    except Exception:
        pass


core_v1 = client.CoreV1Api()


# ============================================================
# Request Model
# ============================================================

class AnalyzeRequest(BaseModel):
    logs: str


# ============================================================
# Health Check
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "ai-log-analyzer",
        "version": "6.1"
    }


# ============================================================
# Ollama AI
# ============================================================

def ask_ai(prompt: str):

    try:

        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )

        response.raise_for_status()

        data = response.json()

        return data.get(
            "response",
            "AI returned no response."
        )

    except requests.exceptions.Timeout:

        return "AI analysis timed out."

    except Exception as e:

        return f"AI analysis failed: {str(e)}"


# ============================================================
# Simple Log Analysis
# ============================================================

@app.post("/analyze")
def analyze(request: AnalyzeRequest):

    prompt = f"""
You are a Kubernetes DevOps troubleshooting assistant.

Analyze the following Kubernetes application logs.

LOGS:
{request.logs}

Provide:

1. Current Status
2. Problem
3. Likely Root Cause
4. Evidence
5. Recommended kubectl Commands
6. Recommended Fix

Do not invent problems that are not supported by the logs.
"""

    analysis = ask_ai(prompt)

    return {
        "model": MODEL,
        "analysis": analysis
    }


# ============================================================
# Kubernetes Pod Analysis
# ============================================================

@app.get("/analyze-pod/{namespace}/{pod_name}")
def analyze_pod(namespace: str, pod_name: str):

    # ========================================================
    # Get Pod
    # ========================================================

    try:

        pod = core_v1.read_namespaced_pod(
            name=pod_name,
            namespace=namespace
        )

    except Exception as e:

        raise HTTPException(
            status_code=404,
            detail=f"Unable to read pod: {str(e)}"
        )


    # ========================================================
    # Pod Phase
    # ========================================================

    pod_phase = pod.status.phase


    # ========================================================
    # Container Status
    # ========================================================

    container_statuses = []

    total_restarts = 0

    crash_loop_detected = False
    image_pull_problem = False
    oom_killed = False
    active_container_problem = False


    statuses = pod.status.container_statuses or []


    for container in statuses:

        restart_count = container.restart_count or 0

        total_restarts += restart_count


        ready = container.ready

        state = "Unknown"
        reason = None
        exit_code = None


        # ----------------------------------------------------
        # Current state
        # ----------------------------------------------------

        if container.state:

            if container.state.running:

                state = "Running"

            elif container.state.waiting:

                state = "Waiting"

                reason = container.state.waiting.reason

            elif container.state.terminated:

                state = "Terminated"

                reason = container.state.terminated.reason

                exit_code = container.state.terminated.exit_code


        # ----------------------------------------------------
        # Detect current failures
        # ----------------------------------------------------

        if reason in [
            "CrashLoopBackOff",
            "BackOff"
        ]:

            crash_loop_detected = True

            active_container_problem = True


        if reason in [
            "ImagePullBackOff",
            "ErrImagePull"
        ]:

            image_pull_problem = True

            active_container_problem = True


        if reason == "OOMKilled":

            oom_killed = True

            active_container_problem = True


        if state == "Terminated" and exit_code not in [
            None,
            0
        ]:

            active_container_problem = True


        # ----------------------------------------------------
        # Container result
        # ----------------------------------------------------

        container_statuses.append({

            "name": container.name,

            "ready": ready,

            "restart_count": restart_count,

            "state": state,

            "reason": reason,

            "exit_code": exit_code

        })


    # ========================================================
    # Detect Readiness
    # ========================================================

    all_ready = True


    for container in container_statuses:

        if not container["ready"]:

            all_ready = False


    # ========================================================
    # Kubernetes Events
    # ========================================================

    kubernetes_events = []


    try:

        events = core_v1.list_namespaced_event(
            namespace=namespace,
            field_selector=f"involvedObject.name={pod_name}"
        )


        for event in events.items:

            event_time = (
                event.last_timestamp
                or event.event_time
                or event.first_timestamp
            )


            kubernetes_events.append({

                "type": event.type,

                "reason": event.reason,

                "message": event.message,

                "time": (
                    event_time.isoformat()
                    if event_time
                    else None
                )

            })


            # ------------------------------------------------
            # Historical CrashLoop / BackOff detection
            # ------------------------------------------------

            if event.reason in [
                "BackOff",
                "Failed"
            ]:

                message = event.message or ""

                if (
                    "restarting failed container" in message.lower()
                    or "back-off restarting failed container"
                    in message.lower()
                ):

                    crash_loop_detected = True


            # ------------------------------------------------
            # Historical image pull problem
            # ------------------------------------------------

            if event.reason in [
                "Failed",
                "ErrImagePull",
                "ImagePullBackOff"
            ]:

                message = event.message or ""

                if (
                    "pull image" in message.lower()
                    or "pulling image" in message.lower()
                    or "failed to pull image" in message.lower()
                ):

                    image_pull_problem = True


    except Exception as e:

        kubernetes_events.append({

            "type": "Warning",

            "reason": "EventReadFailed",

            "message": str(e),

            "time": None

        })


    # ========================================================
    # Current Logs
    # ========================================================

    current_logs = ""


    try:

        current_logs = core_v1.read_namespaced_pod_log(
            name=pod_name,
            namespace=namespace,
            tail_lines=200
        )

    except Exception as e:

        current_logs = f"Unable to retrieve current logs: {str(e)}"


    # ========================================================
    # Previous Logs
    # ========================================================

    previous_logs = ""


    try:

        previous_logs = core_v1.read_namespaced_pod_log(
            name=pod_name,
            namespace=namespace,
            previous=True,
            tail_lines=200
        )

    except Exception:

        previous_logs = (
            "No previous container logs available."
        )


    # ========================================================
    # Last Terminated State
    # ========================================================

    last_terminated = []


    for container in statuses:

        if container.last_state and container.last_state.terminated:

            terminated = container.last_state.terminated


            last_terminated.append({

                "name": container.name,

                "reason": terminated.reason,

                "exit_code": terminated.exit_code,

                "signal": terminated.signal,

                "message": terminated.message,

                "finished_at": (
                    terminated.finished_at.isoformat()
                    if terminated.finished_at
                    else None
                )

            })


            # ------------------------------------------------
            # Detect previous OOMKilled
            # ------------------------------------------------

            if terminated.reason == "OOMKilled":

                oom_killed = True


            # ------------------------------------------------
            # Detect previous abnormal termination
            # ------------------------------------------------

            if (
                terminated.exit_code is not None
                and terminated.exit_code != 0
            ):

                active_container_problem = True


    # ========================================================
    # Classification
    # ========================================================

    if (
        crash_loop_detected
        and any(
            c["state"] == "Waiting"
            and c["reason"] in [
                "CrashLoopBackOff",
                "BackOff"
            ]
            for c in container_statuses
        )
    ):

        current_health = "Critical"

        detected_problem = "CrashLoopBackOff"


    elif image_pull_problem and not all_ready:

        current_health = "Critical"

        detected_problem = (
            "ImagePullBackOff / ErrImagePull"
        )


    elif oom_killed and not all_ready:

        current_health = "Critical"

        detected_problem = "OOMKilled"


    elif pod_phase == "Pending":

        current_health = "Warning"

        detected_problem = "Pod Pending"


    elif active_container_problem and not all_ready:

        current_health = "Warning"

        detected_problem = "Container problem"


    elif (
        pod_phase == "Running"
        and all_ready
        and total_restarts > 0
    ):

        current_health = "Warning"

        detected_problem = (
            "Recovered container instability"
        )


    elif (
        pod_phase == "Running"
        and all_ready
        and crash_loop_detected
        and total_restarts > 0
    ):

        current_health = "Warning"

        detected_problem = (
            "Recovered container instability"
        )


    elif (
        pod_phase == "Running"
        and all_ready
    ):

        current_health = "Healthy"

        detected_problem = "No current problem"


    else:

        current_health = "Warning"

        detected_problem = (
            "Pod is not fully healthy"
        )


    # ========================================================
    # AI Prompt
    # ========================================================

    prompt = f"""
You are an expert Kubernetes DevOps troubleshooting assistant.

The Kubernetes application has already performed the primary
health assessment.

You MUST treat the following values as authoritative.

============================================================
CURRENT HEALTH
============================================================

{current_health}


============================================================
DETECTED PROBLEM
============================================================

{detected_problem}


============================================================
POD INFORMATION
============================================================

Namespace:
{namespace}

Pod:
{pod_name}

Pod Phase:
{pod_phase}

Total Restart Count:
{total_restarts}

Container Status:
{container_statuses}

Last Terminated State:
{last_terminated}


============================================================
KUBERNETES EVENTS
============================================================

{kubernetes_events}


============================================================
CURRENT LOGS
============================================================

{current_logs}


============================================================
PREVIOUS LOGS
============================================================

{previous_logs}


============================================================
IMPORTANT RULES
============================================================

1. Trust CURRENT HEALTH and DETECTED PROBLEM.

2. Do NOT claim that a Running pod is healthy if the
   container is not Ready or is repeatedly restarting.

3. Pod phase Running does NOT necessarily mean the
   application is healthy.

4. Restart count is important evidence.

5. CrashLoopBackOff means the container is repeatedly
   failing and Kubernetes is restarting it.

6. ImagePullBackOff means Kubernetes cannot pull the
   container image.

7. OOMKilled means the container was killed because of
   memory exhaustion.

8. Do not invent firewall, networking, CPU, memory or
   configuration problems without evidence.

9. Do not treat historical Kubernetes events as current
   failures if the container has recovered.

10. If the pod is currently Running and Ready but has
    restart_count > 0, classify it as recovered instability,
    not fully healthy.

11. Use previous logs to identify failures that caused
    container restarts.

12. Separate CURRENT PROBLEM from HISTORICAL EVENTS.

13. Use logs and Kubernetes events as supporting evidence.

14. If evidence is insufficient, explicitly say so.

15. Only recommend valid kubectl commands.

16. Only recommend commands relevant to the detected problem.

17. Do not recommend kubectl exec unless useful.

18. Do not invent Kubernetes events.

============================================================
RESPONSE FORMAT
============================================================

Current Status:
Healthy / Warning / Critical

Problem:
Describe the detected current problem.

Likely Root Cause:
Explain the most likely cause using evidence.

Evidence:
List concrete evidence.

Historical Events:
Mention relevant historical events separately.

Recommended kubectl Commands:
Give only useful commands.

Recommended Fix:
Give the appropriate remediation.

If the pod is healthy:
No immediate fix required; continue monitoring.
"""


    # ========================================================
    # Ask AI
    # ========================================================

    analysis = ask_ai(prompt)


    # ========================================================
    # Return Result
    # ========================================================

    return {

        "namespace": namespace,

        "pod": pod_name,

        "model": MODEL,

        "current_health": current_health,

        "detected_problem": detected_problem,

        "pod_phase": pod_phase,

        "total_restarts": total_restarts,

        "container_status": container_statuses,

        "last_terminated": last_terminated,

        "kubernetes_events": kubernetes_events,

        "current_logs": current_logs,

        "previous_logs": previous_logs,

        "analysis": analysis

    }
