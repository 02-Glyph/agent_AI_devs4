# agent/agents/exercise_agent.py
import asyncio
from agent.llm.openrouter_client import OpenRouterClient
from agent.tools.hub_client import hub_get, hub_post
from agent.tools.fetch_url import fetch_url
from agent.tools.filter_csv import filter_csv
from agent.core.types import Message, ToolSpec, AgentResponse
from agent.llm.factory import create_llm_client
import os
from dotenv import load_dotenv


load_dotenv()


SYSTEM_PROMPT = """
You are an autonomous AI agent solving programming exercises.
You will receive an exercise description and must solve it step by step.


- When filtering text data, use the exact characters from the exercise description including Polish diacritics (ą, ę, ó, ś, ź, ż, ć, ń). Never transliterate Polish characters.


You have access to these tools:
- hub_get(endpoint, params)     — GET from hub.ag3nts.org
- hub_post(endpoint, payload)   — POST to hub.ag3nts.org
- fetch_url(url, params)        — GET from any external URL
- filter_csv(filters)           — Filter last fetched CSV before processing
- ask_human(question)           — ask the user for clarification


KRYTYCZNE FORMATOWANIE:
- PRZECZYTAJ PRZYKŁAD W EXERCISE - to jest DOKŁADNY format payload dla hub_post  
- filter_csv zwraca surowe dane CSV (birthDate/birthPlace/job) - PRZETWÓRZ do formatu przykładu
- NIE kopiuj surowego wyniku filter_csv do /verify - ZMIEŃ kolumny wg przykładu
- born = int(birthDate), city = birthPlace, tags = job.split(", ")
- Wyślij WSZYSTKIE pasujące osoby (nie pomijaj żadnej!)


Rules:
- apikey is injected automatically by hub tools — NEVER ask the user for it
- Placeholders like 'tutaj-twój-klucz' in URLs are replaced automatically by tools
- CRITICAL: When fetching a CSV, you MUST call filter_csv in the very next step before doing anything else. Never pass raw CSV text to the LLM.
- When you have the final answer POST it to the correct endpoint EXACTLY LIKE IN EXAMPLE
- Report back the flag you receive
- Only use ask_human if something is truly ambiguous
- NEVER write Python code in your responses. Use only the provided tools.
- NEVER use fetch_url to fetch a CSV that was already fetched with hub_get.
- After filter_csv returns results, analyze them directly and post the answer IN EXAMPLE FORMAT.
"""


TOOLS: list[ToolSpec] = [
    ToolSpec(
        name="hub_get",
        description="GET request to hub.ag3nts.org. Use the endpoint exactly as shown in the exercise — placeholders like 'tutaj-twój-klucz' are replaced automatically.",
        input_schema={
            "type": "object",
            "properties": {
                "endpoint": {"type": "string", "description": "Path after hub.ag3nts.org, e.g. /data/key/people.csv"},
                "params": {"type": "object", "description": "Optional query params", "additionalProperties": True},
            },
            "required": ["endpoint"],
        },
    ),
    ToolSpec(
        name="hub_post",
        description="POST request to hub.ag3nts.org. Use for submitting answers.",
        input_schema={
            "type": "object",
            "properties": {
                "endpoint": {"type": "string", "description": "Path after hub.ag3nts.org, e.g. /verify"},
                "payload": {"type": "object", "description": "JSON payload to send (apikey added automatically)"},
            },
            "required": ["endpoint", "payload"],
        },
    ),
    ToolSpec(
        name="fetch_url",
        description="GET request to any external URL. Use for fetching data from third-party sources.",
        input_schema={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Full URL to fetch"},
                "params": {"type": "object", "description": "Optional query params", "additionalProperties": True},
            },
            "required": ["url"],
        },
    ),
    ToolSpec(
        name="filter_csv",
        description="Filter the last fetched CSV by given criteria. ALWAYS call this immediately after fetching any CSV — never pass raw CSV to the LLM. Do NOT pass csv_text — it is handled automatically.",
        input_schema={
            "type": "object",
            "properties": {
                "filters": {
                    "type": "object",
                    "description": "Filter criteria. Use exact column names for exact match (e.g. gender, birthPlace). Use birthDate_min/birthDate_max for year range (integers).",
                    "additionalProperties": True,
                },
            },
            "required": ["filters"],
        },
    ),
    ToolSpec(
        name="ask_human",
        description="Ask the user for clarification when the exercise is ambiguous or missing info.",
        input_schema={
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "Question to ask the user"},
            },
            "required": ["question"],
        },
    ),
]


async def ask_human(question: str) -> str:
    print(f"\n[AGENT NEEDS INPUT]: {question}")
    return input("Your answer: ")


class ExerciseAgent:
    def __init__(self):
        self.llm = create_llm_client()
        self._last_csv: str | None = None


    def _truncate_content(self, content: str) -> str:
        """Truncate content to safe size"""
        if len(content) > 20000:  # Zmniejszony limit
            return (
                content[:20000]
                + f"\n...[TRUNCATED — {len(content)} chars total. Use filter_csv to process this data.]"
            )
        return content


    def _truncate_history(self, messages: list[Message], max_tokens: int = 120000) -> list[Message]:
        """Bezpieczne truncate - zawsze zachowaj system+user+tools"""
        if len(messages) <= 4:  # system+user+assistant+tool
            return messages
            
        total_chars = sum(len(msg.content or "") for msg in messages)
        if total_chars <= max_tokens * 4:
            return messages
        
        # MINIMUM: system + pierwszy user + ostatnie wiadomości
        result = [messages[0], messages[1]]  # system + exercise_text
        
        # Dodaj ostatnie wiadomości aż do limitu rozmiaru
        remaining_chars = max_tokens * 3  # miejsce na tools/response
        for msg in reversed(messages[2:]):  # od najnowszych, pomiń system+user
            msg_chars = len(msg.content or "")
            if remaining_chars > msg_chars + 1000:  # margines bezpieczeństwa
                result.insert(-1, msg)  # wstaw przed ostatnią (user)
                remaining_chars -= msg_chars
            else:
                break
        
        print(f"[TRUNCATE] Z {len(messages)} → {len(result)} msg ({sum(len(m.content or '') for m in result)//1000}k chars)")
        return result[-25:]  # ostatnie 25 dla safety


    async def _run_filter_csv(self, args: dict) -> list[dict]:
        csv_text = self._last_csv if self._last_csv else args.get("csv_text", "")
        result = filter_csv(csv_text, args["filters"])
        return result


    async def solve(self, exercise_text: str, extra_context: dict = {}):
        print("[ExerciseAgent] Starting...\n")

        messages: list[Message] = [
            Message(role="system", content=SYSTEM_PROMPT),
            Message(role="user", content=exercise_text),
        ]
        if extra_context:
            messages.append(Message(role="user", content=f"Additional context: {extra_context}"))

        tool_functions = {
            "hub_get": lambda args: hub_get(args["endpoint"], args.get("params")),
            "hub_post": lambda args: hub_post(args["endpoint"], args["payload"]),
            "fetch_url": lambda args: fetch_url(args["url"], args.get("params")),
            "filter_csv": self._run_filter_csv,
            "ask_human": lambda args: ask_human(args["question"]),
        }

        while True:
            # CZYSZCZENIE HISTORII PRZED LLM CALL + DEBUG
            messages = self._truncate_history(messages)
            print(f"[DEBUG] {len(messages)} msg: {[m.role for m in messages]}")
            
            response: AgentResponse = await self.llm.generate(messages, tools=TOOLS)

            if not response.tool_calls:
                print(f"\n[DONE] {response.output_text}")
                break

            messages.append(Message(
                role="assistant",
                content=response.output_text,
                tool_calls=response.tool_calls,
            ))

            for tc in response.tool_calls:
                print(f"[TOOL] {tc.tool_name}({tc.arguments})")
                result = await tool_functions[tc.tool_name](tc.arguments)

                content = str(result)
                content = self._truncate_content(content)  # TRUNCATE TUTAJ

                # Store full CSV if hub_get
                if tc.tool_name == "hub_get" and "\n" in content and "," in content[:200]:
                    self._last_csv = result  # Pełny wynik bez truncate

                messages.append(Message(
                    role="tool",
                    content=content,
                    name=tc.tool_name,
                    tool_call_id=tc.tool_call_id,
                ))



