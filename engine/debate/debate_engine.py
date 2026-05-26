import asyncio
import re
from litellm import acompletion

class DebateEngine:
    def __init__(self, models=None):
        # We assume the environment variables for these providers are set.
        self.models = models or [
            "groq/llama3-70b-8192",
            "gemini/gemini-1.5-pro-latest",
            "openrouter/anthropic/claude-3.5-sonnet"
        ]

    async def get_model_response(self, model: str, messages: list) -> str:
        try:
            response = await acompletion(
                model=model,
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error querying {model}: {e}")
            return f"Error from {model}: {e}"

    async def generate_proposals(self, task: str) -> dict:
        print(f"Generating proposals for: {task}")
        messages = [
            {"role": "system", "content": "You are an expert software engineer. Analyze the following implementation plan and provide your best implementation proposal. Be detailed and concise."},
            {"role": "user", "content": f"Task/Plan: {task}"}
        ]

        tasks = [self.get_model_response(model, messages) for model in self.models]
        responses = await asyncio.gather(*tasks)

        return dict(zip(self.models, responses))

    async def debate(self, task: str, proposals: dict) -> dict:
        print("Starting debate round...")

        debate_messages = []
        for model, proposal in proposals.items():
            debate_messages.append(f"Proposal from {model}:\n{proposal}\n---")

        combined_proposals = "\n".join(debate_messages)

        debate_tasks = []
        for model in self.models:
            messages = [
                {"role": "system", "content": "You are a software engineer in a debate. Review the following proposals from different models for the given task. Critique them, identify flaws, and suggest improvements. Resolve conflicts and vote on the best approach or a synthesis of the best parts. Conclude with a clear 'VOTE: [Your chosen approach]'."},
                {"role": "user", "content": f"Task/Plan: {task}\n\nProposals:\n{combined_proposals}"}
            ]
            debate_tasks.append(self.get_model_response(model, messages))

        responses = await asyncio.gather(*debate_tasks)
        return dict(zip(self.models, responses))

    def extract_vote(self, response: str) -> str:
        match = re.search(r'VOTE:\s*(.*)', response, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        return "No clear vote"

    async def resolve_consensus(self, task: str, debate_results: dict) -> str:
        print("Resolving consensus...")
        votes = {model: self.extract_vote(response) for model, response in debate_results.items()}
        print(f"Votes collected: {list(votes.values())}")

        combined_votes = "\n".join([f"{model} voted for:\n{vote}\n---" for model, vote in votes.items()])

        messages = [
            {"role": "system", "content": "You are the debate moderator. Based on the following votes and syntheses from the debate participants, determine the final consensus. Output the final, agreed-upon implementation plan resolving any conflicts."},
            {"role": "user", "content": f"Task: {task}\n\nVotes:\n{combined_votes}"}
        ]

        moderator_model = self.models[0]
        print(f"Moderator {moderator_model} generating final consensus plan...")
        final_plan = await self.get_model_response(moderator_model, messages)
        return final_plan

    async def run_debate(self, task: str) -> dict:
        proposals = await self.generate_proposals(task)
        debate_results = await self.debate(task, proposals)
        final_plan = await self.resolve_consensus(task, debate_results)

        return {
            "task": task,
            "proposals": proposals,
            "debate": debate_results,
            "final_plan": final_plan
        }

if __name__ == "__main__":
    async def main():
        engine = DebateEngine()
        print("DebateEngine initialized.")

    asyncio.run(main())
