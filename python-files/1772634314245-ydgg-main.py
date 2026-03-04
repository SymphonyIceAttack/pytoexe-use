import os
import openai
from dotenv import load_dotenv
from rich import print
from rich.console import Console

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

console = Console()

MODEL = "gpt-4o-mini"

def read_project_files(root="."):
    project_data = ""
    for root_dir, dirs, files in os.walk(root):
        for file in files:
            if file.endswith((".py", ".js", ".html", ".css", ".json", ".md")):
                path = os.path.join(root_dir, file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                        project_data += f"\n\n### FILE: {path}\n{content}\n"
                except:
                    pass
    return project_data


def ai_request(user_prompt):
    project_context = read_project_files()

    system_prompt = """
You are an advanced AI IDE Agent like Cursor.
You can:
- Generate code
- Modify code
- Create new files
- Refactor entire project
When modifying files, respond in this format:

CREATE_FILE: filename
<code>

OR

MODIFY_FILE: filename
<new full code>
"""

    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Project:\n{project_context}\n\nTask:\n{user_prompt}"}
        ],
        temperature=0.2
    )

    return response["choices"][0]["message"]["content"]


def apply_changes(ai_output):
    lines = ai_output.splitlines()

    if ai_output.startswith("CREATE_FILE:"):
        filename = lines[0].replace("CREATE_FILE:", "").strip()
        code = "\n".join(lines[1:])
        with open(filename, "w", encoding="utf-8") as f:
            f.write(code)
        print(f"[green]Created file {filename}[/green]")

    elif ai_output.startswith("MODIFY_FILE:"):
        filename = lines[0].replace("MODIFY_FILE:", "").strip()
        code = "\n".join(lines[1:])
        with open(filename, "w", encoding="utf-8") as f:
            f.write(code)
        print(f"[yellow]Modified file {filename}[/yellow]")

    else:
        print(ai_output)


def main():
    print("[bold cyan]AI IDE Agent Started (like Cursor)[/bold cyan]\n")

    while True:
        user_input = input(">>> ")

        if user_input.lower() in ["exit", "quit"]:
            break

        console.print("[blue]Thinking...[/blue]")
        ai_output = ai_request(user_input)

        console.print("\n[bold]AI Response:[/bold]")
        console.print(ai_output)

        apply_changes(ai_output)


if __name__ == "__main__":
    main()