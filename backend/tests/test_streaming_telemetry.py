import os
import sys
import json
import asyncio
from fastapi.testclient import TestClient

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.main import app
from backend.agents.orchestrator import multi_agent_graph, MultiAgentState


async def test_streaming_generator_direct():
    print("\n--- 1. Testing stream_execute() generator directly ---")
    state = MultiAgentState(
        ticker="RELIANCE",
        user_profile={"risk_level": "moderate"},
        simulated_stale_data=False,
        simulated_rag_timeout=False
    )

    events = []
    async for event in multi_agent_graph.stream_execute(state):
        events.append(event)
        print(f"  [STREAM EVENT] {event['type']}")

    assert len(events) >= 6, f"Expected at least 6 events, got {len(events)}"
    event_types = [e["type"] for e in events]
    assert "pipeline_started" in event_types
    assert "market_context_loaded" in event_types
    assert "analysts_started" in event_types
    assert "analysts_completed" in event_types
    assert "debate_started" in event_types
    assert "synthesis_started" in event_types
    assert "complete" in event_types

    complete_payload = next(e["payload"] for e in events if e["type"] == "complete")
    assert complete_payload["ticker"] == "RELIANCE"
    assert "price_data" in complete_payload
    assert "agents" in complete_payload
    assert "debate" in complete_payload
    assert "synthesis" in complete_payload
    assert "telemetry" in complete_payload
    assert "execution_trace" in complete_payload
    print("[PASSED] stream_execute() direct generator test.")


def test_api_analysis_stream_endpoint():
    print("\n--- 2. Testing GET /api/analysis/stream/{ticker} SSE endpoint ---")
    with TestClient(app) as client:
        response = client.get("/api/analysis/stream/NVDA?risk_level=conservative")
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")

        lines = response.text.split("\n")
        events = []
        current_event = None

        for line in lines:
            line = line.strip()
            if line.startswith("event:"):
                current_event = line.replace("event:", "").strip()
            elif line.startswith("data:") and current_event:
                raw_data = line.replace("data:", "").strip()
                try:
                    payload = json.loads(raw_data)
                    events.append({"event": current_event, "data": payload})
                except json.JSONDecodeError:
                    pass
                current_event = None

        assert len(events) >= 5, f"Expected at least 5 streaming events, got {len(events)}"

        event_names = [e["event"] for e in events]
        assert "pipeline_started" in event_names
        assert "market_context_loaded" in event_names
        assert "analysts_started" in event_names
        assert "analysts_completed" in event_names
        assert "complete" in event_names

        complete_event = next(e for e in events if e["event"] == "complete")
        assert complete_event["data"]["ticker"] == "NVDA"
        print(f"[PASSED] GET /api/analysis/stream/NVDA verified. Received {len(events)} events.")


def main():
    print("=== Testing Sub-phase 5.1: Real-time Streaming Telemetry (SSE) ===")
    asyncio.run(test_streaming_generator_direct())
    test_api_analysis_stream_endpoint()
    print("\n[SUCCESS] Sub-phase 5.1 SSE Streaming Telemetry verified with 100% accuracy!")


if __name__ == "__main__":
    main()
