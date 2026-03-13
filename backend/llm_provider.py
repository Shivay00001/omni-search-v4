import g4f
import asyncio
from typing import AsyncGenerator

async def generate_summary(query: str, context: str) -> str:
    """
    Generates a summary using g4f (free models). 
    Combines the user query with the scraped search context.
    """
    prompt = f"""
    You are a premium AI Search Assistant like Perplexity.
    Based on the following search result context, provide a comprehensive, clear, and accurate answer to the user query.
    
    CRITICAL INSTRUCTIONS:
    - Use a professional, objective tone.
    - Cite sources using [number] format (e.g., [1], [2]) corresponding to the order of appearance in the context.
    - If the context doesn't contain the answer, state that you couldn't find specific information but provide what is available.
    - Use Markdown for formatting (bold, lists, headers).
    
    User Query: {query}
    
    Search Context:
    {context}
    
    Answer:
    """
    
    try:
        response = await g4f.ChatCompletion.create_async(
            model="gpt-4", # Use string name for stability
            messages=[{"role": "user", "content": prompt}],
        )
        return str(response)
    except Exception as e:
        print(f"LLM Generation error: {e}")
        return f"Error occurred: {str(e)}"

async def stream_summary(query: str, context: str) -> AsyncGenerator[str, None]:
    """
    Streams the summary response (for real-time feel).
    """
    prompt = f"""
    You are a premium AI Search Assistant.
    Based on the following search result context, provide a comprehensive and accurate answer.
    Cite sources as [number].
    
    User Query: {query}
    
    Search Context:
    {context}
    
    Answer:
    """
    
    print(f"Streaming summary for context of length: {len(context)}")
    try:
        response = g4f.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            stream=True,
        )
        if not response:
            yield "No response from AI provider. Please try again later."
            return

        for message in response:
            if message:
                yield str(message)
                await asyncio.sleep(0.01)
    except Exception as e:
        print(f"Streaming error: {e}")
        yield f"Error: {str(e)}"

if __name__ == "__main__":
    # Test generation
    q = "What is the capital of France?"
    ctx = "[1] Source 1: Paris is the capital and most populous city of France."
    res = asyncio.run(generate_summary(q, ctx))
    print(res)
