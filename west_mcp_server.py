import subprocess
import logging
import re
from typing import Optional, List, Dict, Any

from mcp.server.fastmcp import FastMCP

# Configure basic logging for the server
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize the MCP server with a name
mcp = FastMCP("WestMCP")

# --- Helper Function for Running West Commands ---
def run_west_command(command_args: List[str]) -> Dict[str, Any]:
    """
    Executes a west command and captures its output.

    Args:
        command_args (list): A list of strings representing the west command
                             and its arguments (e.g., ['build', '-b', 'nrf52840dk_nrf52840', 'path/to/project']).

    Returns:
        dict: A dictionary containing 'success' (boolean), 'message' (string),
              'stdout' (string), and 'stderr' (string).
    """
    full_command = ['west'] + command_args
    logger.info(f"Executing command: {' '.join(full_command)}")

    try:
        result = subprocess.run(
            full_command,
            capture_output=True,
            text=True,
            check=True,
            encoding='utf-8'
        )
        logger.info(f"Command successful: {' '.join(full_command)}")
        return {
            "success": True,
            "message": "Command executed successfully.",
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except subprocess.CalledProcessError as e:
        # Check for specific error messages indicating an unknown subcommand
        if "unknown command" in e.stderr.lower() or "invalid choice" in e.stderr.lower():
            error_message = f"West subcommand '{command_args[0]}' not found or invalid."
        else:
            error_message = f"Command failed with exit code {e.returncode}."

        logger.error(f"{error_message}: {' '.join(full_command)}")
        logger.error(f"Stdout: {e.stdout}")
        logger.error(f"Stderr: {e.stderr}")
        return {
            "success": False,
            "message": error_message,
            "stdout": e.stdout,
            "stderr": e.stderr
        }
    except FileNotFoundError:
        logger.error("'west' command not found. Ensure west is installed and in your system's PATH.")
        return {
            "success": False,
            "message": "'west' command not found. Please ensure west is installed and in your system's PATH.",
            "stdout": "",
            "stderr": "FileNotFoundError: 'west' command not found."
        }
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return {
            "success": False,
            "message": f"An unexpected error occurred: {str(e)}",
            "stdout": "",
            "stderr": str(e)
        }

# --- Helper for common runner options ---
def _add_runner_options(base_command: List[str],
                        build_dir: Optional[str],
                        runner: Optional[str],
                        skip_rebuild: Optional[bool],
                        domain: Optional[str],
                        board_dir: Optional[str],
                        gdb: Optional[str],
                        openocd: Optional[str],
                        openocd_search: Optional[str]) -> List[str]:
    """Helper to append common runner-related options to a command."""
    cmd = list(base_command) # Create a mutable copy
    if build_dir:
        cmd.extend(['-d', build_dir])
    if runner:
        cmd.extend(['-r', runner])
    if skip_rebuild:
        cmd.append('--skip-rebuild')
    if domain:
        cmd.extend(['--domain', domain])
    if board_dir:
        cmd.extend(['--board-dir', board_dir])
    if gdb:
        cmd.extend(['--gdb', gdb])
    if openocd:
        cmd.extend(['--openocd', openocd])
    if openocd_search:
        cmd.extend(['--openocd-search', openocd_search])
    return cmd

# --- MCP Tool for `west completion` ---
@mcp.tool()
def get_completion_script(shell: str) -> Dict[str, Any]:
    """
    Outputs shell completion scripts for west.

    Args:
        shell (str): The shell for which the completion script is intended
                     (e.g., 'bash', 'fish', 'powershell', 'zsh').

    Returns:
        dict: Command execution result.
    """
    if shell not in ['bash', 'fish', 'powershell', 'zsh']:
        return {
            "success": False,
            "message": "Invalid shell specified. Must be one of: bash, fish, powershell, zsh.",
            "stdout": "",
            "stderr": ""
        }
    command_args = ['completion', shell]
    return run_west_command(command_args)

# --- MCP Tool for `west boards` ---
@mcp.tool()
def list_boards(
    name_re: Optional[str] = None,
    format_string: Optional[str] = None,
    board: Optional[str] = None,
    arch_root: Optional[List[str]] = None,
    board_root: Optional[List[str]] = None,
    soc_root: Optional[List[str]] = None,
    board_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Displays information about Zephyr boards.

    Args:
        name_re (str, optional): A regular expression to filter board names.
        format_string (str, optional): Format string to use to list each board.
        board (str, optional): Lookup a specific board, fails if not found.
        arch_root (List[str], optional): Add an architecture root.
        board_root (List[str], optional): Add a board root.
        soc_root (List[str], optional): Add a SoC root.
        board_dir (str, optional): Only look for boards at the specific location.

    Returns:
        dict: Command execution result.
    """
    command_args = ['boards']
    if name_re:
        command_args.extend(['-n', name_re])
    if format_string:
        command_args.extend(['-f', format_string])
    if board:
        command_args.extend(['--board', board])
    if arch_root:
        for r in arch_root:
            command_args.extend(['--arch-root', r])
    if board_root:
        for r in board_root:
            command_args.extend(['--board-root', r])
    if soc_root:
        for r in soc_root:
            command_args.extend(['--soc-root', r])
    if board_dir:
        command_args.extend(['--board-dir', board_dir])
    return run_west_command(command_args)

# --- MCP Tool for `west shields` ---
@mcp.tool()
def list_shields(
    name_re: Optional[str] = None,
    format_string: Optional[str] = None,
    board_root: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Displays information about supported shields.

    Args:
        name_re (str, optional): A regular expression to filter shield names.
        format_string (str, optional): Format string to use to list each shield.
        board_root (List[str], optional): Add a board root.

    Returns:
        dict: Command execution result.
    """
    command_args = ['shields']
    if name_re:
        command_args.extend(['-n', name_re])
    if format_string:
        command_args.extend(['-f', format_string])
    if board_root:
        for r in board_root:
            command_args.extend(['--board-root', r])
    return run_west_command(command_args)

# --- MCP Tool for Building Zephyr Projects (`west build`) ---
@mcp.tool()
def build_zephyr_project(
    source_dir: str,
    board: str,
    build_dir: Optional[str] = None,
    force: Optional[bool] = False,
    cmake: Optional[bool] = False,
    cmake_only: Optional[bool] = False,
    domain: Optional[str] = None,
    target: Optional[str] = None,
    test_item: Optional[str] = None,
    build_opt: Optional[List[str]] = None,
    just_print: Optional[bool] = False,
    snippet: Optional[List[str]] = None,
    shield: Optional[List[str]] = None,
    extra_conf: Optional[List[str]] = None,
    extra_dtc_overlay: Optional[List[str]] = None,
    pristine: Optional[str] = None, # auto, always, never
    sysbuild: Optional[bool] = False, # --sysbuild or --no-sysbuild
    no_sysbuild: Optional[bool] = False,
    cmake_opt: Optional[List[str]] = None # extra options after --
) -> Dict[str, Any]:
    """
    Builds a Zephyr application using the 'west build' command.

    Args:
        source_dir (str): Application source directory.
        board (str): Board to build for with optional board revision (e.g., 'nrf52840dk_nrf52840').
        build_dir (str, optional): Build directory to create or use.
        force (bool, optional): Ignore any errors and try to proceed.
        cmake (bool, optional): Force a cmake run.
        cmake_only (bool, optional): Just run cmake; don't build (implies -c).
        domain (str, optional): Execute build tool only for given domain.
        target (str, optional): Run build system target (e.g., 'usage').
        test_item (str, optional): Build based on test data in testcase.yaml or sample.yaml.
        build_opt (List[str], optional): Options to pass to the build tool (make or ninja).
        just_print (bool, optional): Just print build commands; don't run them.
        snippet (List[str], optional): Add the argument to SNIPPET.
        shield (List[str], optional): Add the argument to SHIELD.
        extra_conf (List[str], optional): Add the argument to EXTRA_CONF_FILE.
        extra_dtc_overlay (List[str], optional): Add the argument to EXTRA_DTC_OVERLAY_FILE.
        pristine (str, optional): Pristine build folder setting ('auto', 'always', 'never').
        sysbuild (bool, optional): Create multi domain build system.
        no_sysbuild (bool, optional): Do not create multi domain build system (default).
        cmake_opt (List[str], optional): Extra options to pass to cmake (after '--').

    Returns:
        dict: Command execution result.
    """
    command_args = ['build']

    if board:
        command_args.extend(['-b', board])
    if build_dir:
        command_args.extend(['-d', build_dir])
    if force:
        command_args.append('-f')
    if cmake:
        command_args.append('-c')
    if cmake_only:
        command_args.append('--cmake-only')
    if domain:
        command_args.extend(['--domain', domain])
    if target:
        command_args.extend(['-t', target])
    if test_item:
        command_args.extend(['-T', test_item])
    if build_opt:
        for opt in build_opt:
            command_args.extend(['-o', opt])
    if just_print:
        command_args.append('-n')
    if snippet:
        for s in snippet:
            command_args.extend(['-S', s])
    if shield:
        for s in shield:
            command_args.extend(['--shield', s])
    if extra_conf:
        for f in extra_conf:
            command_args.extend(['--extra-conf', f])
    if extra_dtc_overlay:
        for f in extra_dtc_overlay:
            command_args.extend(['--extra-dtc-overlay', f])
    if pristine:
        command_args.extend(['-p', pristine])
    if sysbuild:
        command_args.append('--sysbuild')
    if no_sysbuild:
        command_args.append('--no-sysbuild')

    command_args.append(source_dir)

    if cmake_opt:
        command_args.append('--')
        command_args.extend(cmake_opt)

    return run_west_command(command_args)

# --- MCP Tool for Flashing Zephyr Projects (`west flash`) ---
@mcp.tool()
def flash_zephyr_project(
    build_dir: Optional[str] = None,
    runner: Optional[str] = None,
    skip_rebuild: Optional[bool] = False,
    domain: Optional[str] = None,
    board_dir: Optional[str] = None,
    gdb: Optional[str] = None,
    openocd: Optional[str] = None,
    openocd_search: Optional[str] = None
) -> Dict[str, Any]:
    """
    Flashes a Zephyr project to the target board using the 'west flash' command.

    Args:
        build_dir (str, optional): Application build directory.
        runner (str, optional): Override default runner from --build-dir.
        skip_rebuild (bool, optional): Do not refresh cmake dependencies first.
        domain (str, optional): Execute runner only for given domain.
        board_dir (str, optional): Board directory.
        gdb (str, optional): Path to GDB.
        openocd (str, optional): Path to OpenOCD.
        openocd_search (str, optional): Path to add to OpenOCD search path.

    Returns:
        dict: Command execution result.
    """
    command_args = _add_runner_options(
        ['flash'], build_dir, runner, skip_rebuild, domain,
        board_dir, gdb, openocd, openocd_search
    )
    return run_west_command(command_args)

# --- MCP Tool for `west debug` ---
@mcp.tool()
def debug_zephyr_project(
    build_dir: Optional[str] = None,
    runner: Optional[str] = None,
    skip_rebuild: Optional[bool] = False,
    domain: Optional[str] = None,
    board_dir: Optional[str] = None,
    gdb: Optional[str] = None,
    openocd: Optional[str] = None,
    openocd_search: Optional[str] = None
) -> Dict[str, Any]:
    """
    Connects to the board, flashes the program, and starts a debugging session
    using the 'west debug' command.

    Args:
        build_dir (str, optional): Application build directory.
        runner (str, optional): Override default runner from --build-dir.
        skip_rebuild (bool, optional): Do not refresh cmake dependencies first.
        domain (str, optional): Execute runner only for given domain.
        board_dir (str, optional): Board directory.
        gdb (str, optional): Path to GDB.
        openocd (str, optional): Path to OpenOCD.
        openocd_search (str, optional): Path to add to OpenOCD search path.

    Returns:
        dict: Command execution result.
    """
    command_args = _add_runner_options(
        ['debug'], build_dir, runner, skip_rebuild, domain,
        board_dir, gdb, openocd, openocd_search
    )
    return run_west_command(command_args)

# --- MCP Tool for `west debugserver` ---
@mcp.tool()
def start_debug_server(
    build_dir: Optional[str] = None,
    runner: Optional[str] = None,
    skip_rebuild: Optional[bool] = False,
    domain: Optional[str] = None,
    board_dir: Optional[str] = None,
    gdb: Optional[str] = None,
    openocd: Optional[str] = None,
    openocd_search: Optional[str] = None
) -> Dict[str, Any]:
    """
    Connects to the board and launches a debug server which accepts incoming
    connections for debugging the connected board using 'west debugserver'.

    Args:
        build_dir (str, optional): Application build directory.
        runner (str, optional): Override default runner from --build-dir.
        skip_rebuild (bool, optional): Do not refresh cmake dependencies first.
        domain (str, optional): Execute runner only for given domain.
        board_dir (str, optional): Board directory.
        gdb (str, optional): Path to GDB.
        openocd (str, optional): Path to OpenOCD.
        openocd_search (str, optional): Path to add to OpenOCD search path.

    Returns:
        dict: Command execution result.
    """
    command_args = _add_runner_options(
        ['debugserver'], build_dir, runner, skip_rebuild, domain,
        board_dir, gdb, openocd, openocd_search
    )
    return run_west_command(command_args)

# --- MCP Tool for `west attach` ---
@mcp.tool()
def attach_debugger(
    build_dir: Optional[str] = None,
    runner: Optional[str] = None,
    skip_rebuild: Optional[bool] = False,
    domain: Optional[str] = None,
    board_dir: Optional[str] = None,
    gdb: Optional[str] = None,
    openocd: Optional[str] = None,
    openocd_search: Optional[str] = None
) -> Dict[str, Any]:
    """
    Attaches a debugger to the board without reflashing the program
    using the 'west attach' command.

    Args:
        build_dir (str, optional): Application build directory.
        runner (str, optional): Override default runner from --build-dir.
        skip_rebuild (bool, optional): Do not refresh cmake dependencies first.
        domain (str, optional): Execute runner only for given domain.
        board_dir (str, optional): Board directory.
        gdb (str, optional): Path to GDB.
        openocd (str, optional): Path to OpenOCD.
        openocd_search (str, optional): Path to add to OpenOCD search path.

    Returns:
        dict: Command execution result.
    """
    command_args = _add_runner_options(
        ['attach'], build_dir, runner, skip_rebuild, domain,
        board_dir, gdb, openocd, openocd_search
    )
    return run_west_command(command_args)

# --- MCP Tool for `west rtt` ---
@mcp.tool()
def start_rtt_viewer(
    build_dir: Optional[str] = None,
    runner: Optional[str] = None,
    skip_rebuild: Optional[bool] = False,
    domain: Optional[str] = None,
    board_dir: Optional[str] = None,
    gdb: Optional[str] = None,
    openocd: Optional[str] = None,
    openocd_search: Optional[str] = None
) -> Dict[str, Any]:
    """
    Starts an RTT viewer for the connected board using the 'west rtt' command.

    Args:
        build_dir (str, optional): Application build directory.
        runner (str, optional): Override default runner from --build-dir.
        skip_rebuild (bool, optional): Do not refresh cmake dependencies first.
        domain (str, optional): Execute runner only for given domain.
        board_dir (str, optional): Board directory.
        gdb (str, optional): Path to GDB.
        openocd (str, optional): Path to OpenOCD.
        openocd_search (str, optional): Path to add to OpenOCD search path.

    Returns:
        dict: Command execution result.
    """
    command_args = _add_runner_options(
        ['rtt'], build_dir, runner, skip_rebuild, domain,
        board_dir, gdb, openocd, openocd_search
    )
    return run_west_command(command_args)

# --- MCP Tool for `west zephyr-export` ---
@mcp.tool()
def export_zephyr_installation() -> Dict[str, Any]:
    """
    Registers the current Zephyr installation as a CMake config package
    in the CMake user package registry using 'west zephyr-export'.

    Returns:
        dict: Command execution result.
    """
    command_args = ['zephyr-export']
    return run_west_command(command_args)

# --- MCP Tool for `west blobs` ---
@mcp.tool()
def manage_blobs(
    subcommand: str,
    module: Optional[List[str]] = None,
    format_string: Optional[str] = None,
    auto_accept: Optional[bool] = False
) -> Dict[str, Any]:
    """
    Works with binary blobs using 'west blobs'.

    Args:
        subcommand (str): The 'blobs' subcommand to execute (e.g., 'list', 'fetch', 'clean').
        module (List[str], optional): Zephyr modules to operate on; all modules if not given.
        format_string (str, optional): Format string to use to list each blob (for 'list' subcommand).
        auto_accept (bool, optional): Auto accept license if fetching needs click-through (for 'fetch' subcommand).

    Returns:
        dict: Command execution result.
    """
    if subcommand not in ['list', 'fetch', 'clean']:
        return {
            "success": False,
            "message": "Invalid 'blobs' subcommand. Must be one of: list, fetch, clean.",
            "stdout": "",
            "stderr": ""
        }

    command_args = ['blobs', subcommand]
    if module:
        for m in module:
            command_args.extend(['--module', m]) # Note: west blobs uses --module for filtering
    if subcommand == 'list' and format_string:
        command_args.extend(['-f', format_string])
    if subcommand == 'fetch' and auto_accept:
        command_args.append('-a')

    return run_west_command(command_args)

# --- MCP Tool for `west bindesc` ---
@mcp.tool()
def manage_binary_descriptors(
    subcommand: str,
    args: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Works with Binary Descriptors using 'west bindesc'.

    Args:
        subcommand (str): The 'bindesc' subcommand to run (e.g., 'dump', 'search', 'custom_search', 'list', 'get_offset').
        args (List[str], optional): Additional arguments specific to the subcommand.

    Returns:
        dict: Command execution result.
    """
    valid_subcommands = ['dump', 'search', 'custom_search', 'list', 'get_offset']
    if subcommand not in valid_subcommands:
        return {
            "success": False,
            "message": f"Invalid 'bindesc' subcommand. Must be one of: {', '.join(valid_subcommands)}.",
            "stdout": "",
            "stderr": ""
        }

    command_args = ['bindesc', subcommand]
    if args:
        command_args.extend(args)
    return run_west_command(command_args)

# --- MCP Tool for `west robot` ---
@mcp.tool()
def run_robot_tests(
    build_dir: Optional[str] = None,
    runner: Optional[str] = None,
    skip_rebuild: Optional[bool] = False,
    domain: Optional[str] = None,
    board_dir: Optional[str] = None,
    gdb: Optional[str] = None,
    openocd: Optional[str] = None,
    openocd_search: Optional[str] = None
) -> Dict[str, Any]:
    """
    Runs RobotFramework test suites with a chosen runner using 'west robot'.

    Args:
        build_dir (str, optional): Application build directory.
        runner (str, optional): Override default runner from --build-dir.
        skip_rebuild (bool, optional): Do not refresh cmake dependencies first.
        domain (str, optional): Execute runner only for given domain.
        board_dir (str, optional): Board directory.
        gdb (str, optional): Path to GDB.
        openocd (str, optional): Path to OpenOCD.
        openocd_search (str, optional): Path to add to OpenOCD search path.

    Returns:
        dict: Command execution result.
    """
    command_args = _add_runner_options(
        ['robot'], build_dir, runner, skip_rebuild, domain,
        board_dir, gdb, openocd, openocd_search
    )
    return run_west_command(command_args)

# --- MCP Tool for `west simulate` ---
@mcp.tool()
def simulate_board(
    build_dir: Optional[str] = None,
    runner: Optional[str] = None,
    skip_rebuild: Optional[bool] = False,
    domain: Optional[str] = None,
    board_dir: Optional[str] = None,
    gdb: Optional[str] = None,
    openocd: Optional[str] = None,
    openocd_search: Optional[str] = None
) -> Dict[str, Any]:
    """
    Simulates the board on a chosen runner using generated artifacts
    with 'west simulate'.

    Args:
        build_dir (str, optional): Application build directory.
        runner (str, optional): Override default runner from --build-dir.
        skip_rebuild (bool, optional): Do not refresh cmake dependencies first.
        domain (str, optional): Execute runner only for given domain.
        board_dir (str, optional): Board directory.
        gdb (str, optional): Path to GDB.
        openocd (str, optional): Path to OpenOCD.
        openocd_search (str, optional): Path to add to OpenOCD search path.

    Returns:
        dict: Command execution result.
    """
    command_args = _add_runner_options(
        ['simulate'], build_dir, runner, skip_rebuild, domain,
        board_dir, gdb, openocd, openocd_search
    )
    return run_west_command(command_args)

# --- MCP Tool for `west packages` ---
@mcp.tool()
def manage_packages(
    manager: str,
    module: Optional[List[str]] = None,
    args: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Lists and installs packages for Zephyr and modules using 'west packages'.

    Args:
        manager (str): The package manager to use (e.g., 'pip').
        module (List[str], optional): Zephyr module(s) to run the 'packages' command for.
                                      Use 'zephyr' for Zephyr itself.
        args (List[str], optional): Additional arguments specific to the package manager subcommand.

    Returns:
        dict: Command execution result.
    """
    if manager not in ['pip']: # Extend this list if other managers are supported by west packages
        return {
            "success": False,
            "message": f"Invalid package manager. Only '{manager}' is currently supported for 'west packages'.",
            "stdout": "",
            "stderr": ""
        }

    command_args = ['packages', manager]
    if module:
        for m in module:
            command_args.extend(['-m', m])
    if args:
        command_args.extend(args)
    return run_west_command(command_args)

# --- MCP Tool for `west patch` ---
@mcp.tool()
def manage_patches(
    subcommand: str,
    patch_base: Optional[str] = None,
    patch_yml: Optional[str] = None,
    west_workspace: Optional[str] = None,
    src_module: Optional[str] = None,
    dst_module: Optional[List[str]] = None,
    args: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Applies, cleans, lists, or fetches patches to the west workspace using 'west patch'.

    Args:
        subcommand (str): The 'patch' subcommand to execute (e.g., 'apply', 'clean', 'gh-fetch', 'list').
        patch_base (str, optional): Directory containing patch files.
        patch_yml (str, optional): Path to patches.yml file.
        west_workspace (str, optional): West workspace directory.
        src_module (str, optional): Zephyr module containing the patch definition.
        dst_module (List[str], optional): Zephyr module(s) to run the 'patch' command for.
        args (List[str], optional): Additional arguments specific to the subcommand.

    Returns:
        dict: Command execution result.
    """
    valid_subcommands = ['apply', 'clean', 'gh-fetch', 'list']
    if subcommand not in valid_subcommands:
        return {
            "success": False,
            "message": f"Invalid 'patch' subcommand. Must be one of: {', '.join(valid_subcommands)}.",
            "stdout": "",
            "stderr": ""
        }

    command_args = ['patch', subcommand]
    if patch_base:
        command_args.extend(['-b', patch_base])
    if patch_yml:
        command_args.extend(['-l', patch_yml])
    if west_workspace:
        command_args.extend(['-w', west_workspace])
    if src_module:
        command_args.extend(['-sm', src_module])
    if dst_module:
        for m in dst_module:
            command_args.extend(['-dm', m])
    if args:
        command_args.extend(args)

    return run_west_command(command_args)

# --- MCP Tool for `west gtags` ---
@mcp.tool()
def index_gtags(
    projects: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Indexes source code files in the west workspace using GNU Global's 'gtags' tool.

    Args:
        projects (List[str], optional): Name of west project to index, or its path.
                                        May be given more than once. Use "manifest"
                                        to refer to the manifest repository.

    Returns:
        dict: Command execution result.
    """
    command_args = ['gtags']
    if projects:
        command_args.extend(projects)
    return run_west_command(command_args)

# --- NEW MCP Tool for listing all available west commands ---
@mcp.tool()
def list_west_commands() -> Dict[str, Any]:
    """
    Lists all available west commands (built-in and extension) by parsing 'west --help' output.

    Returns:
        dict: A dictionary containing 'success' (boolean), 'message' (string),
              and 'commands' (dict with 'built_in' and 'extension' lists of command names).
    """
    help_result = run_west_command(['--help'])

    if not help_result['success']:
        return {
            "success": False,
            "message": "Failed to retrieve west help output.",
            "commands": {"built_in": [], "extension": []},
            "stdout": help_result.get('stdout', ''),
            "stderr": help_result.get('stderr', '')
        }

    output_lines = help_result['stdout'].splitlines()
    built_in_commands = []
    extension_commands = []
    current_section = None

    for line in output_lines:
        line = line.strip()
        if line == "Built-in commands:":
            current_section = "built_in"
            continue
        elif line == "Extension Commands:":
            current_section = "extension"
            continue
        elif not line and current_section: # Empty line often indicates end of section
            current_section = None
            continue

        if current_section:
            # Commands are typically listed as 'command_name: one-line description'
            match = re.match(r'^(\S+)(?:\s+.*)?$', line)
            if match:
                command_name = match.group(1).strip()
                if current_section == "built_in":
                    built_in_commands.append(command_name)
                elif current_section == "extension":
                    extension_commands.append(command_name)

    return {
        "success": True,
        "message": "Successfully listed west commands.",
        "commands": {
            "built_in": built_in_commands,
            "extension": extension_commands
        },
        "stdout": help_result.get('stdout', ''),
        "stderr": help_result.get('stderr', '')
    }

# --- NEW MCP Tool for running arbitrary west commands (fallback) ---
@mcp.tool()
def run_arbitrary_west_command(command_name: str, args: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Executes any west command by its name with a list of arguments.
    This tool serves as a generic fallback for commands that do not have
    a dedicated MCP tool definition.

    Args:
        command_name (str): The name of the west command to execute (e.g., 'init', 'update').
        args (List[str], optional): A list of strings representing the arguments for the command.

    Returns:
        dict: Command execution result.
    """
    full_args = [command_name]
    if args:
        full_args.extend(args)
    return run_west_command(full_args)


# --- Main Execution Block ---
if __name__ == '__main__':
    logger.info("Starting West MCP Server...")
    mcp.run()
