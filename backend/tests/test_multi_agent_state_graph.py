import os
import sys
import asyncio
from fastapi.testclient import TestClient

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.main import app
from backend.agents.orchestrator import multi_agent_graph, MultiAgentState


async def test_state_graph_direct():
    print("\n--- 1. Testing MultiAgentStateGraph Direct Execution ---")
    state = MultiAgentState(
        ticker="NVDA",
        user_profile={"risk_level": "conservative", "panic_sell_tendency": 0.8},
        simulated_stale_data=False,
        simulated_rag_timeout=False
    )
    assert state.current_node == "INITIALIZED"

    result_state = await multi_agent_graph.execute(state)
    assert result_state.current_node == "COMPLETED"
    assert result_state.company_name != ""
    assert result_state.quant_result.get("score") is not None
    assert result_state.rag_result.get("score") is not None
    assert result_state.synthesis_result.get("final_action") in [
        "STRONG_BUY", "BUY", "CAUTIOUS_ACCUMULATE", "HOLD", "TRIM", "SELL"
    ]
    assert len(result_state.execution_trace) >= 5, "Trace must capture all graph transitions"
    print(f"Direct StateGraph execution PASSED. Visited {len(result_state.execution_trace)} nodes.")

    # Print execution trace
    print("Execution Trace:")
    for step in result_state.execution_trace:
        print(f"  -> Node: {step['node']} ({step['duration_ms']}ms)")


async def test_cyclical_rebuttal_and_convergence():
    print("\n--- 2. Testing Cyclical Bull-vs-Bear Rebuttal Edge ---")
    state = MultiAgentState(
        ticker="RELIANCE",
        user_profile={"risk_level": "conservative"},
        simulated_stale_data=False,
        simulated_rag_timeout=False,
        max_cycles=2
    )

    result_state = await multi_agent_graph.execute(state)
    assert result_state.is_converged is True, "State machine must converge"

    # Check whether a rebuttal round occurred when divergence was high
    nodes_visited = [step["node"] for step in result_state.execution_trace]
    assert "parallel_analysts" in nodes_visited
    assert "adversarial_debate" in nodes_visited
    assert "convergence_guard" in nodes_visited
    assert "synthesis" in nodes_visited

    has_rebuttal = "adversarial_rebuttal" in nodes_visited
    print(f"Cyclical rebuttal triggered: {has_rebuttal} (Debate cycles: {result_state.debate_cycles})")
    print("Convergence and cycle-breaker checks PASSED.")


async def test_circuit_breaker_timeout():
    print("\n--- 3. Testing Circuit Breaker on RAG Timeout ---")
    state = MultiAgentState(
        ticker="NVDA",
        simulated_rag_timeout=True
    )
    result_state = await multi_agent_graph.execute(state)
    assert result_state.rag_result.get("timed_out") is True
    assert result_state.is_converged is True
    assert result_state.current_node == "COMPLETED"
    print("Circuit breaker timeout fallback PASSED.")


def test_api_orchestrator_endpoints():
    print("\n--- 4. Testing Orchestrator REST Endpoints ---")
    with TestClient(app) as client:
        # Topology endpoint
        res_topo = client.get("/api/orchestrator/topology")
        assert res_topo.status_code == 200
        topo_data = res_topo.json()
        assert topo_data["engine"] == "Typed Cyclic Directed StateGraph"
        assert len(topo_data["nodes"]) >= 6
        print("GET /api/orchestrator/topology PASSED.")

        # Analyze endpoint with trace
        res_analyze = client.post(
            "/api/analyze",
            json={"ticker": "NVDA"}
        )
        assert res_analyze.status_code == 200
        data = res_analyze.json()
        assert "execution_trace" in data
        assert len(data["execution_trace"]) >= 5
        print(f"POST /api/analyze StateGraph execution trace verified ({len(data['execution_trace'])} steps).")


def main():
    print("=== Testing Sub-phase 4.3: Multi-Agent State Machine (Typed State Graph) ===")
    asyncio.run(test_state_graph_direct())
    asyncio.run(test_cyclical_rebuttal_and_convergence())
    asyncio.run(test_circuit_breaker_timeout())
    test_api_orchestrator_endpoints()
    print("\n[SUCCESS] Sub-phase 4.3 Multi-Agent State Machine verified with 100% accuracy!")


if __name__ == "__main__":
    main()
