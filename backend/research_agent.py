import asyncio
from typing import List, Dict
from search_engine import search_web
from sentinel_provider import sentinel
import json

class ResearchAgent:
    """
    Agent responsible for 'Linear Search' logic.
    Breaks down a query into multiple sequential steps using semantic reasoning.
    """
    
    async def plan_research(self, query: str) -> List[str]:
        """Expands a single query into 3 distinct search queries."""
        prompt = f"""
        Break down the following research query into 3 distinct, high-impact search queries.
        The queries should be sequential and move from general context to specific details.
        
        Original Query: {query}
        
        Output format: JSON array of strings only.
        Example: ["query 1", "query 2", "query 3"]
        """
        try:
            plan_str = await sentinel.generate_full(prompt)
            # Find JSON array in the response
            start = plan_str.find('[')
            end = plan_str.rfind(']') + 1
            if start != -1 and end != -1:
                return json.loads(plan_str[start:end])
        except Exception as e:
            print(f"Research planning failed: {e}")
        
        return [query] # Fallback to original

    async def conduct_linear_research(self, query: str):
        """
        Executes the multi-step research or linear search.
        Yields status updates and results.
        """
        queries = await self.plan_research(query)
        all_results = []
        
        for i, sub_query in enumerate(queries):
            yield f"[STEP {i+1}]: Searching for '{sub_query}'...\n"
            results = await search_web(sub_query, max_results=3)
            all_results.extend(results)
            await asyncio.sleep(0.5)
            
        # Deduplicate by URL
        seen_urls = set()
        unique_results = []
        for r in all_results:
            if r["url"] not in seen_urls:
                unique_results.append(r)
                seen_urls.add(r["url"])
        
        from search_engine import rerank_results
        unique_results = rerank_results(query, unique_results)
        
        yield unique_results

    async def execute_agent_task(self, task_goal: str):
        """
        Executes a complex agentic task by decomposing it into steps.
        Simulates 'browser acting on behalf of user'.
        """
        yield f"[PLANNING] Decomposing task: {task_goal}"
        
        # 1. Plan steps
        prompt = f"Decompose this browser task into 4 actionable search/verification steps: {task_goal}"
        plan_raw = await sentinel.generate_response([{"role": "user", "content": prompt}])
        steps = [s.strip() for s in plan_raw.split('\n') if s.strip()][:4]
        
        all_data = []
        for i, step in enumerate(steps):
            yield f"[ACTION {i+1}] {step}"
            results = await search_web(step, max_results=4)
            all_data.extend(results)
            yield f"[STATUS] Gathered {len(results)} intelligence points for step {i+1}."
            await asyncio.sleep(1)
            
        yield "[FINALIZING] Synthesizing comprehensive action report..."
        yield all_data

research_agent = ResearchAgent()
