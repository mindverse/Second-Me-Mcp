import os
import json
import asyncio
from openai import OpenAI
from dotenv import load_dotenv
from typing import List
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class OpenAIClient:
    def __init__(self):
        self.session: List[ClientSession] = []
        self.exit_stack = AsyncExitStack()

    async def connect_from_config(self, config_path: str):
        if not os.path.exists(config_path):
            print(f"⚠️ Config file '{config_path}' not found. Skipping server connection.")
            return

        with open(config_path, "r") as f:
            try:
                config = json.load(f)
            except json.JSONDecodeError:
                print(f"⚠️ Config file '{config_path}' is not valid JSON. Skipping server connection.")
                return

        servers = config.get("mcpServers", {})
        if not servers:
            print("ℹ️ No MCP servers configured. Continuing without tool servers.")
            return

        for name, params in servers.items():
            command = params.get("command")
            args = params.get("args", [])
            env = params.get("env", {})

            if not command:
                raise ValueError(f"No command found for server '{name}'")

            print(f"🔌 Connecting to server: {name} (cmd: {command} {args})")

            server_params = StdioServerParameters(
                command=command,
                args=args,
                env=env
            )

            stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
            session = await self.exit_stack.enter_async_context(ClientSession(*stdio_transport))
            await session.initialize()
            self.session.append(session)

        for i, session in enumerate(self.session):
            response = await session.list_tools()
            tools = response.tools
            print(f"✅ Server {i + 1} tools:", [tool.name for tool in tools])

    async def process_query(self, query: str):
        messages = [{"role": "user", "content": query}]
        all_tools = []

        for session in self.session:
            response = await session.list_tools()
            all_tools.extend(response.tools)

        if not all_tools:
            response = client.responses.create(
                model="gpt-4o-mini",
                input=messages,
            )

            reply = response.output_text
            messages.append([{"role": "assistant", "content": reply}])
            return reply

        available_functions = [{
            "type": "function",
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.inputSchema

        } for tool in all_tools]

        response = client.responses.create(
            model="gpt-4o-mini",
            input=messages,
            tools=available_functions,
            tool_choice="auto"
        )
        reply = response.output_text

        tool_call = response.output[0]
        if response.output[0].type == "function_call":
            tool_name = tool_call.name
            tool_args = json.loads(tool_call.arguments)
            tool_response = ""
            tool_n = None
            for session in self.session:
                tool_result = await session.call_tool(tool_name, tool_args)
                if "Unknown tool" not in tool_result.content[0].text:
                    tool_response = tool_result.content[0].text
                    tool_n = tool_name

            print(tool_n)
            print("🛠️ Tool response:", tool_response)
            messages.append(tool_call)
            messages.append({
                "type": "function_call_output",
                "call_id": tool_call.call_id,
                "output": str(tool_response)
            })

            # Second round with tool result
            response = client.responses.create(
                model="gpt-4o-mini",
                input=messages,
                tools=available_functions,
            )
            reply = response.output_text
        messages.append([{"role": "assistant", "content": reply}])

        return reply

    async def chat_loop(self):
        print("\n🤖 MCP Client Started!")
        print("Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("\n💬 Query: ").strip()
                if query.lower() == 'quit':
                    break

                response = await self.process_query(query)
                print("\n🧠 Response:", response)

            except Exception as e:
                print(f"\n❌ Error: {str(e)}")

    async def cleanup(self):
        await self.exit_stack.aclose()


async def main():
    client = OpenAIClient()
    try:
        await client.connect_from_config("config.json")
        await client.chat_loop()
    finally:
        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
