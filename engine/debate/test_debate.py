import asyncio
import os
from debate_engine import DebateEngine

async def test_debate():
    # Only test the logic flow by mocking the acompletion function to avoid requiring actual API keys for unit testing
    from unittest.mock import patch

    # Mock response classes
    class MockMessage:
        def __init__(self, content):
            self.content = content

    class MockChoice:
        def __init__(self, content):
            self.message = MockMessage(content)

    class MockResponse:
        def __init__(self, content):
            self.choices = [MockChoice(content)]

    async def mock_acompletion(model, messages, **kwargs):
        # Determine if it's proposal or debate based on the system prompt
        system_content = messages[0].get("content", "")

        if "provide your best implementation proposal" in system_content:
            return MockResponse(f"This is a mocked proposal from {model}. I propose to do X and Y.")
        elif "Review the following proposals" in system_content:
            return MockResponse(f"This is a mocked debate response from {model}. I reviewed the proposals and I VOTE: synthesize X and Y from model {model}.")
        elif "determine the final consensus" in system_content:
            return MockResponse(f"This is the final consensus plan. We will do X and Y based on the votes.")
        else:
            return MockResponse(f"Mocked response from {model}.")

    with patch('debate_engine.acompletion', side_effect=mock_acompletion):
        engine = DebateEngine()
        task = "Write a simple function to calculate the Fibonacci sequence in Python."
        print(f"Starting test debate for task: {task}")

        results = await engine.run_debate(task)

        assert "task" in results
        assert "proposals" in results
        assert "debate" in results
        assert "final_plan" in results

        for model in engine.models:
            assert model in results["proposals"]
            assert f"mocked proposal from {model}" in results["proposals"][model]

            assert model in results["debate"]
            assert f"mocked debate response from {model}" in results["debate"][model]

        assert "We will do X and Y based on the votes" in results["final_plan"]

        print("Debate engine ran successfully through proposals, debate, and consensus stages!")
        print("Proposals generated:", len(results["proposals"]))
        print("Debate responses generated:", len(results["debate"]))
        print("Final plan length:", len(results["final_plan"]))

if __name__ == "__main__":
    asyncio.run(test_debate())
