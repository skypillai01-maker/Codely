import argparse
import sys
import os
import json
from clients.python_sdk.codely import CodelyClient

def main():
    parser = argparse.ArgumentParser(description="Codely AI CLI Tool")
    parser.add_argument("--url", default="http://localhost:8889", help="Codely Server URL")
    parser.add_argument("--context", default="cli_context", help="The context_id to use")
    parser.add_argument("--session-id", help="Session token (or set CODELY_SESSION_ID env var)")
    parser.add_argument("--mode", default="normal", choices=["normal", "thinking", "deep"], help="Response mode")

    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    chat_parser = subparsers.add_parser("chat", help="Send a chat prompt")
    chat_parser.add_argument("prompt", help="The user prompt")
    chat_parser.add_argument("--file", "-f", action="append", help="Attach a file (can be used multiple times)")
    chat_parser.add_argument("--url", "-u", action="append", help="Attach URL content (can be used multiple times)")
    chat_parser.add_argument("--save-memory", "-s", action="store_true", help="Save attachments to memory")

    memory_parser = subparsers.add_parser("memory", help="Memory management")
    memory_parser.add_argument("--add", help="Add text to memory")
    memory_parser.add_argument("--clear", action="store_true", help="Clear context memory")

    ingest_parser = subparsers.add_parser("ingest", help="Ingest a file")
    ingest_parser.add_argument("file", help="Path to the file to ingest")

    module_parser = subparsers.add_parser("modules", help="Module management")
    module_parser.add_argument("--list", action="store_true", help="List all available modules")
    module_parser.add_argument("--execute", help="Execute a module by name")
    module_parser.add_argument("--params", help="JSON parameters for module execution")

    task_parser = subparsers.add_parser("task", help="Task management")
    task_parser.add_argument("--status", help="Get the status of a task by ID")

    thread_parser = subparsers.add_parser("thread", help="Thread management")
    thread_parser.add_argument("--list", action="store_true", help="List all threads")
    thread_parser.add_argument("--stats", help="Get stats for a thread")
    thread_parser.add_argument("--delete", help="Delete a thread")
    thread_parser.add_argument("--merge", nargs="+", help="Merge threads into first one")

    model_parser = subparsers.add_parser("model", help="Model management")
    model_parser.add_argument("--switch", nargs=2, metavar=("TYPE", "NAME"), help="Switch model (type name)")

    auth_parser = subparsers.add_parser("auth", help="Authentication")
    auth_parser.add_argument("--login", help="Login with email")
    auth_parser.add_argument("--me", action="store_true", help="Show current user info")
    auth_parser.add_argument("--logout", action="store_true", help="Logout")

    tools_parser = subparsers.add_parser("tools", help="Phase 3 tools")
    tools_parser.add_argument("--list", action="store_true", help="List all available tools")

    write_parser = subparsers.add_parser("write", help="Write to a file")
    write_parser.add_argument("file_path", help="Path to the file to write")
    write_parser.add_argument("--content", "-c", required=True, help="Content to write")
    write_parser.add_argument("--mode", default="write", choices=["write", "append"], help="Write mode")

    exec_parser = subparsers.add_parser("exec", help="Execute a command")
    exec_parser.add_argument("command", help="Command to execute")
    exec_parser.add_argument("--timeout", type=int, default=30, help="Timeout in seconds")
    exec_parser.add_argument("--workdir", help="Working directory")

    testgen_parser = subparsers.add_parser("testgen", help="Generate tests")
    testgen_parser.add_argument("--file", "-f", required=True, help="Source file to generate tests for")
    testgen_parser.add_argument("--framework", default="pytest", choices=["pytest", "unittest", "jest"], help="Test framework")
    testgen_parser.add_argument("--style", default="comprehensive", choices=["comprehensive", "basic", "edge_cases", "integration"], help="Test style")

    args = parser.parse_args()

    session_id = args.session_id or os.getenv("CODELY_SESSION_ID")
    client = CodelyClient(args.url, session_id=session_id)

    try:
        if args.command == "auth":
            if args.login:
                result = client.login(args.login)
                print(result.get("message", "Check console for magic link"))
            elif args.me:
                result = client.get_user_info()
                print(json.dumps(result, indent=2))
            elif args.logout:
                result = client.logout()
                print(result.get("message", "Logged out"))
            else:
                auth_parser.print_help()
            return

        if args.command == "chat":
            files = args.file if args.file else []
            urls = args.url if args.url else []

            if files or urls:
                result = client.chat_with_files(
                    context_id=args.context,
                    prompt=args.prompt,
                    files=files,
                    urls=urls,
                    save_to_memory=args.save_memory,
                    mode=args.mode
                )
                print(f"AI: {result['response']}")

                if result.get('attachments'):
                    if result['attachments']['files']:
                        print(f"\nFiles processed: {', '.join(result['attachments']['files'])}")
                    if result['attachments']['urls']:
                        print(f"\nURLs processed: {', '.join(result['attachments']['urls'])}")
                    if result.get('saved_to_memory'):
                        print("\n[Saved to memory]")
            else:
                result = client.chat(args.context, args.prompt, mode=args.mode)
                print(f"AI: {result['response']}")

        elif args.command == "memory":
            if args.add:
                result = client.add_memory(args.context, args.add)
                print(result["message"])
            elif args.clear:
                result = client.clear_memory(args.context)
                print(result["message"])

        elif args.command == "ingest":
            if os.path.exists(args.file):
                result = client.ingest_file(args.context, args.file)
                print(result["message"])
            else:
                print(f"Error: File not found: {args.file}")

        elif args.command == "modules":
            if args.list:
                modules = client.list_modules()
                print("Available Modules:")
                for m in modules:
                    print(f"- {m['name']}: {m['description']}")
            elif args.execute:
                params = json.loads(args.params) if args.params else {}
                result = client.execute_module(args.execute, params)
                print(json.dumps(result, indent=2))

        elif args.command == "task":
            if args.status:
                result = client.get_task_status(args.status)
                print(json.dumps(result, indent=2))

        elif args.command == "thread":
            if args.list:
                result = client.list_threads()
                print(f"Threads ({result['count']}):")
                for thread in result['threads']:
                    print(f"  - {thread['id']}: {thread['entries']} entries")
            elif args.stats:
                result = client.get_thread_stats(args.stats)
                print(json.dumps(result, indent=2))
            elif args.delete:
                result = client.delete_thread(args.delete)
                print(result["message"])
            elif args.merge:
                if len(args.merge) < 2:
                    print("Error: --merge requires at least 2 thread IDs")
                else:
                    target = args.merge[0]
                    sources = args.merge[1:]
                    result = client.merge_memory(target, sources)
                    print(f"Merged {result['entries_merged']} entries into {target}")

        elif args.command == "model":
            if args.switch:
                result = client.switch_model(args.switch[0], args.switch[1])
                print(result.get("message", "Model switched"))

        elif args.command == "tools":
            if args.list:
                result = client.list_tools()
                print("Available Tools:")
                for t in result.get("tools", []):
                    perm = " [requires permission]" if t.get("requires_permission") else ""
                    print(f"- {t['name']}: {t['description']}{perm}")

        elif args.command == "write":
            try:
                with open(args.file_path, "r") as f:
                    existing = f.read()
                if args.mode == "append":
                    print(f"Appending to {args.file_path}")
                else:
                    print(f"Overwriting {args.file_path}")
            except FileNotFoundError:
                print(f"Creating new file: {args.file_path}")

            result = client.write_file(args.file_path, args.content, args.mode)
            print(json.dumps(result, indent=2))

        elif args.command == "exec":
            result = client.exec_command(args.command, args.timeout, args.workdir)
            print(json.dumps(result, indent=2))

        elif args.command == "testgen":
            if not os.path.exists(args.file):
                print(f"Error: File not found: {args.file}")
                return

            with open(args.file, "r", encoding="utf-8") as f:
                code = f.read()

            result = client.generate_tests(
                code=code,
                file_path=args.file,
                framework=args.framework,
                test_style=args.style
            )

            print(f"Framework: {result.get('framework')}")
            print(f"Test file: {result.get('test_file_name')}")
            print(f"Test path: {result.get('test_file_path')}")
            print(f"\nPrompt for LLM:")
            print(result.get("test_prompt"))
            print(f"\nInstructions:")
            print(result.get("instructions"))

        else:
            parser.print_help()

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
