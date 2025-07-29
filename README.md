# West MCP Server

This repository contains a Model Context Protocol (MCP) server for `west`, the meta-tool used by the Zephyr RTOS. This server allows you to interact with `west` commands programmatically via a RESTful API, making it easier to automate Zephyr development workflows, integrate with other tools, or build custom interfaces.

The server is built using Python and the official `modelcontextprotocol/python-sdk`.

## Features

* **Programmatic `west` interaction:** Execute common `west` commands like `build`, `flash`, `debug`, `boards`, `shields`, and more via HTTP POST requests.

* **Standardized API:** Leverages the Model Context Protocol (MCP) for a consistent and discoverable API.

* **Command Introspection:** A dedicated tool to list all available `west` commands (built-in and extension) on your system.

* **Generic Command Execution:** A fallback tool to run any `west` command, even if it doesn't have a specific MCP tool defined, providing maximum flexibility.

* **Error Handling:** Provides informative error messages for `west` command failures or missing commands.

## Getting Started

### Prerequisites

* Python 3.8+

* `west` command-line tool installed and configured for your Zephyr environment. Ensure it's in your system's PATH.

### Installation

1. **Clone this repository** (or copy the `west_mcp_server.py` file).

2. **Navigate to the project directory** in your terminal.

3. **Install the `mcp` Python SDK:**

   Using `uv` (recommended):

   ```bash
   uv init .
   uv add "mcp[cli]"
   ```

   Or using `pip`:

   ```bash
   pip install "mcp[cli]"
   ```

### Running the Server

To start the MCP server, run the Python script:

```bash
python west_mcp_server.py
```

The server will typically start on `http://127.0.0.1:8000/`. Check your terminal output for the exact address and port.

## API Endpoints (Tools)

The server exposes various `west` commands as MCP tools. You can interact with these tools by sending JSON POST requests to the server.

### General Usage

All tools accept a JSON payload in the request body and return a JSON response with `success` (boolean), `message` (string), `stdout` (string), and `stderr` (string).

### Available Tools

Here's a list of the exposed `west` commands and their corresponding MCP tool names:

#### Core Commands

| Tool Name | Description | Arguments |
|---|---|---|
| `build_zephyr_project` | Builds a Zephyr application. | `source_dir` (str), `board` (str), `build_dir` (Optional\[str\]), `force` (Optional\[bool\]), `cmake` (Optional\[bool\]), `cmake_only` (Optional\[bool\]), `domain` (Optional\[str\]), `target` (Optional\[str\]), `test_item` (Optional\[str\]), `build_opt` (Optional\[List\[str\]\]), `just_print` (Optional\[bool\]), `snippet` (Optional\[List\[str\]\]), `shield` (Optional\[List\[str\]\]), `extra_conf` (Optional\[List\[str\]\]), `extra_dtc_overlay` (Optional\[List\[str\]\]), `pristine` (Optional\[str\]), `sysbuild` (Optional\[bool\]), `no_sysbuild` (Optional\[bool\]), `cmake_opt` (Optional\[List\[str\]\]) |
| `flash_zephyr_project` | Flashes a Zephyr project to the target board. | `build_dir` (Optional\[str\]), `runner` (Optional\[str\]), `skip_rebuild` (Optional\[bool\]), `domain` (Optional\[str\]), `board_dir` (Optional\[str\]), `gdb` (Optional\[str\]), `openocd` (Optional\[str\]), `openocd_search` (Optional\[str\]) |
| `debug_zephyr_project` | Connects, flashes, and starts a debugging session. | `build_dir` (Optional\[str\]), `runner` (Optional\[str\]), `skip_rebuild` (Optional\[bool\]), `domain` (Optional\[str\]), `board_dir` (Optional\[str\]), `gdb` (Optional\[str\]), `openocd` (Optional\[str\]), `openocd_search` (Optional\[str\]) |
| `start_debug_server` | Launches a debug server for the connected board. | `build_dir` (Optional\[str\]), `runner` (Optional\[str\]), `skip_rebuild` (Optional\[bool\]), `domain` (Optional\[str\]), `board_dir` (Optional\[str\]), `gdb` (Optional\[str\]), `openocd` (Optional\[str\]), `openocd_search` (Optional\[str\]) |
| `attach_debugger` | Attaches a debugger without reflashing. | `build_dir` (Optional\[str\]), `runner` (Optional\[str\]), `skip_rebuild` (Optional\[bool\]), `domain` (Optional\[str\]), `board_dir` (Optional\[str\]), `gdb` (Optional\[str\]), `openocd` (Optional\[str\]), `openocd_search` (Optional\[str\]) |
| `start_rtt_viewer` | Starts an RTT viewer. | `build_dir` (Optional\[str\]), `runner` (Optional\[str\]), `skip_rebuild` (Optional\[bool\]), `domain` (Optional\[str\]), `board_dir` (Optional\[str\]), `gdb` (Optional\[str\]), `openocd` (Optional\[str\]), `openocd_search` (Optional\[str\]) |

#### Information & Utility Commands

| Tool Name | Description | Arguments |
|---|---|---|
| `get_completion_script` | Outputs shell completion scripts. | `shell` (str, e.g., 'bash', 'fish', 'powershell', 'zsh') |
| `list_boards` | Displays information about Zephyr boards. | `name_re` (Optional\[str\]), `format_string` (Optional\[str\]), `board` (Optional\[str\]), `arch_root` (Optional\[List\[str\]\]), `board_root` (Optional\[List\[str\]\]), `soc_root` (Optional\[List\[str\]\]), `board_dir` (Optional\[str\]) |
| `list_shields` | Displays information about supported shields. | `name_re` (Optional\[str\]), `format_string` (Optional\[str\]), `board_root` (Optional\[List\[str\]\]) |
| `export_zephyr_installation` | Registers the current Zephyr installation as a CMake config package. | None |
| `manage_blobs` | Works with binary blobs (`list`, `fetch`, `clean`). | `subcommand` (str), `module` (Optional\[List\[str\]\]), `format_string` (Optional\[str\]), `auto_accept` (Optional\[bool\]) |
| `manage_binary_descriptors` | Works with Binary Descriptors (`dump`, `search`, `custom_search`, `list`, `get_offset`). | `subcommand` (str), `args` (Optional\[List\[str\]\]) |
| `run_robot_tests` | Runs RobotFramework test suites. | `build_dir` (Optional\[str\]), `runner` (Optional\[str\]), `skip_rebuild` (Optional\[bool\]), `domain` (Optional\[str\]), `board_dir` (Optional\[str\]), `gdb` (Optional\[str\]), `openocd` (Optional\[str\]), `openocd_search` (Optional\[str\]) |
| `simulate_board` | Simulates the board. | `build_dir` (Optional\[str\]), `runner` (Optional\[str\]), `skip_rebuild` (Optional\[bool\]), `domain` (Optional\[str\]), `board_dir` (Optional\[str\]), `gdb` (Optional\[str\]), `openocd` (Optional\[str\]), `openocd_search` (Optional\[str\]) |
| `manage_packages` | Lists and installs packages (`pip` manager supported). | `manager` (str, e.g., 'pip'), `module` (Optional\[List\[str\]\]), `args` (Optional\[List\[str\]\]) |
| `manage_patches` | Applies, cleans, lists, or fetches patches. | `subcommand` (str), `patch_base` (Optional\[str\]), `patch_yml` (Optional\[str\]), `west_workspace` (Optional\[str\]), `src_module` (Optional\[str\]), `dst_module` (Optional\[List\[str\]\]), `args` (Optional\[List\[str\]\]) |
| `index_gtags` | Indexes source code files using GNU Global's `gtags` tool. | `projects` (Optional\[List\[str\]\]) |

#### Introspection & Fallback

| Tool Name | Description | Arguments |
|---|---|---|
| `list_west_commands` | Lists all available `west` commands (built-in and extension) on the current system. | None |
| `run_arbitrary_west_command` | Executes any `west` command by its name with a list of arguments. This is a generic fallback for commands not explicitly defined as tools. | `command_name` (str), `args` (Optional\[List\[str\]\]) |

## Contributing

Feel free to extend this server with more `west` commands or additional functionalities. Pull requests are welcome!
