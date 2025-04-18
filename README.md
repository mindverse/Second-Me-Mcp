# MCP Client

## Overview

This is a chat client built on OpenAI GPT model and MCP tool service, which supports automatic recognition of user intent and calling local tool functions. Support OpenAI function calling and dynamically extending tool functionality.

## Requirements

### Python Version
- Python 3.12

### Required Packages
1. `openai`
2. `mcp` (Multi-Component Platform client library)
3. `python-dotenv`

## Quick start
### Configuration

#### 1. Fill in the OpenAI API key in the`.env` file:
```
OPENAI_API_KEY=your_api_key_here
```
#### 2. Define MCP servers in `config.json`:
```
{
  "mcpServers": {
    "mindverse": {
      "command": "python",
      "args": ["{Local Path}/Second-Me/mcp/mcp_public.py"]
    }
  }
}
```
The default configuration is for the MCP service of SecondME. Before using the MCP service of SecondME, please ensure that you have downloaded the latest version of the code and completed registration. After completing the above steps, fill in the local computer path to the corresponding configuration item to start using.

### Usage
``` python
python mcp_openai_client.py
```
When the following image appears, it proves that the client is running normally.

![quick_start.png](quick_start.png)

Next, you can ask questions or request access to tools.

![query.png](query.png)