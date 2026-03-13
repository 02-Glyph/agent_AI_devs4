# exercises/run.py
import asyncio
import sys
from agent.agents.exercise_agent import ExerciseAgent


def read_exercise_from_terminal() -> str:
    """Czyta zadanie z terminala aż do pojedynczej kropki."""
    print("=== Wklej opis zadania (zakończ pojedynczą kropką na nowej linii) ===")
    lines = []
    while True:
        try:
            line = input()
            if line.strip() == ".":
                break
            lines.append(line)
        except EOFError:
            break
    return "\n".join(lines)


async def main():
    exercise_text = read_exercise_from_terminal()
    if not exercise_text.strip():
        print("Brak zadania, kończę.")
        return

    print("\n=== Uruchamiam agenta ===")
    await ExerciseAgent().solve(exercise_text)


if __name__ == "__main__":
    asyncio.run(main())
