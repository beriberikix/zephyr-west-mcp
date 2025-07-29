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

# --- MCP Tool for `west boards`, `west shields`, `west list`, and `west topdir` ---
@mcp.tool()
def get_west_info(
    subcommand: str,
    name_re: Optional[str] = None,
    format_string: Optional[str] = None,
    board: Optional[str] = None,
    arch_root: Optional[List[str]] = None,
    board_root: Optional[List[str]] = None,
    soc_root: Optional[List[str]] = None,
    board_dir: Optional[str] = None,
    projects: Optional[List[str]] = None,
    all: bool = False,
    inactive: bool = False,
    manifest_path_from_yaml: bool = False,
) -> Dict[str, Any]:
    """
    A unified tool to get information about the west workspace.

    Args:
        subcommand (str): The subcommand to run ('boards', 'shields', 'list', 'topdir').
        name_re (str, optional): A regular expression to filter board or shield names.
        format_string (str, optional): Format string to use to list each board, shield, or project.
        board (str, optional): Lookup a specific board, fails if not found.
        arch_root (List[str], optional): Add an architecture root.
        board_root (List[str], optional): Add a board root.
        soc_root (List[str], optional): Add a SoC root.
        board_dir (str, optional): Only look for boards at the specific location.
        projects (List[str], optional): Projects to operate on (for 'list' subcommand).
        all (bool, optional): Include inactive projects (for 'list' subcommand).
        inactive (bool, optional): List only inactive projects (for 'list' subcommand).
        manifest_path_from_yaml (bool, optional): Print manifest path from YAML (for 'list' subcommand).

    Returns:
        dict: Command execution result.
    """
    valid_subcommands = ['boards', 'shields', 'list', 'topdir']
    if subcommand not in valid_subcommands:
        return {
            "success": False,
            "message": f"Invalid subcommand. Must be one of: {', '.join(valid_subcommands)}.",
            "stdout": "",
            "stderr": ""
        }

    command_args = [subcommand]

    if subcommand == 'boards':
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
    elif subcommand == 'shields':
        if name_re:
            command_args.extend(['-n', name_re])
        if format_string:
            command_args.extend(['-f', format_string])
        if board_root:
            for r in board_root:
                command_args.extend(['--board-root', r])
    elif subcommand == 'list':
        if all:
            command_args.append('-a')
        if inactive:
            command_args.append('-i')
        if manifest_path_from_yaml:
            command_args.append('--manifest-path-from-yaml')
        if format_string:
            command_args.extend(['-f', format_string])
        if projects:
            command_args.extend(projects)

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

# --- MCP Tool for Runner-Based West Commands ---
@mcp.tool()
def run_west_runner(
    subcommand: str,
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
    A single tool to execute runner-based commands like `flash`, `debug`, `debugserver`, `attach`, `rtt`, `robot`, and `simulate`.

    Args:
        subcommand (str): The runner-based subcommand to execute.
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
    valid_subcommands = ['flash', 'debug', 'debugserver', 'attach', 'rtt', 'robot', 'simulate']
    if subcommand not in valid_subcommands:
        return {
            "success": False,
            "message": f"Invalid subcommand. Must be one of: {', '.join(valid_subcommands)}.",
            "stdout": "",
            "stderr": ""
        }

    command_args = _add_runner_options(
        [subcommand], build_dir, runner, skip_rebuild, domain,
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

# --- MCP Tool for `west init` ---
@mcp.tool()
def init_workspace(
    directory: Optional[str] = None,
    manifest_url: Optional[str] = None,
    manifest_rev: Optional[str] = None,
    manifest_file: Optional[str] = None,
    clone_opt: Optional[List[str]] = None,
    local: bool = False,
    rename_delay: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Creates a west workspace.

    Args:
        directory (str, optional): The directory to create the workspace in.
        manifest_url (str, optional): Manifest repository URL to clone.
        manifest_rev (str, optional): Manifest repository branch or tag name to check out.
        manifest_file (str, optional): Manifest file name to use.
        clone_opt (List[str], optional): Additional option to pass to 'git clone'.
        local (bool, optional): Use an existing local manifest repository.
        rename_delay (int, optional): Number of seconds to wait before renaming temporary directories.

    Returns:
        dict: Command execution result.
    """
    command_args = ['init']
    if manifest_url:
        command_args.extend(['-m', manifest_url])
    if manifest_rev:
        command_args.extend(['--mr', manifest_rev])
    if manifest_file:
        command_args.extend(['--mf', manifest_file])
    if clone_opt:
        for opt in clone_opt:
            command_args.extend(['-o', opt])
    if local:
        command_args.append('-l')
    if rename_delay:
        command_args.extend(['--rename-delay', str(rename_delay)])
    if directory:
        command_args.append(directory)
    return run_west_command(command_args)

# --- MCP Tool for `west update` ---
@mcp.tool()
def update_workspace(
    projects: Optional[List[str]] = None,
    stats: bool = False,
    name_cache: Optional[str] = None,
    path_cache: Optional[str] = None,
    fetch: Optional[str] = None,
    fetch_opt: Optional[List[str]] = None,
    narrow: bool = False,
    keep_descendants: bool = False,
    rebase: bool = False,
    group_filter: Optional[str] = None,
    submodule_init_config: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Updates active projects defined in the manifest file.

    Args:
        projects (List[str], optional): Projects to operate on.
        stats (bool, optional): Print performance statistics.
        name_cache (str, optional): Cache repositories by project name.
        path_cache (str, optional): Cache repositories by relative path.
        fetch (str, optional): How to fetch projects ('always' or 'smart').
        fetch_opt (List[str], optional): Additional options for 'git fetch'.
        narrow (bool, optional): Fetch just the project revision.
        keep_descendants (bool, optional): Keep descendant branches checked out.
        rebase (bool, optional): Rebase checked out branches.
        group_filter (str, optional): Filter projects by group.
        submodule_init_config (List[str], optional): Git config for submodule init.

    Returns:
        dict: Command execution result.
    """
    command_args = ['update']
    if stats:
        command_args.append('--stats')
    if name_cache:
        command_args.extend(['--name-cache', name_cache])
    if path_cache:
        command_args.extend(['--path-cache', path_cache])
    if fetch:
        command_args.extend(['-f', fetch])
    if fetch_opt:
        for opt in fetch_opt:
            command_args.extend(['-o', opt])
    if narrow:
        command_args.append('-n')
    if keep_descendants:
        command_args.append('-k')
    if rebase:
        command_args.append('-r')
    if group_filter:
        command_args.extend(['--group-filter', group_filter])
    if submodule_init_config:
        for config in submodule_init_config:
            command_args.extend(['--submodule-init-config', config])
    if projects:
        command_args.extend(projects)
    return run_west_command(command_args)



# --- MCP Tool for `west manifest` ---
@mcp.tool()
def manage_manifest(
    resolve: bool = False,
    freeze: bool = False,
    validate: bool = False,
    path: bool = False,
    untracked: bool = False,
    out: Optional[str] = None,
    active_only: bool = False,
) -> Dict[str, Any]:
    """
    Manages the west manifest.

    Args:
        resolve (bool, optional): Print the resolved manifest.
        freeze (bool, optional): Print the resolved manifest with SHAs.
        validate (bool, optional): Validate the current manifest.
        path (bool, optional): Print the top-level manifest file's path.
        untracked (bool, optional): Print untracked files and directories.
        out (str, optional): Output file for --resolve and --freeze.
        active_only (bool, optional): Only resolve active projects.

    Returns:
        dict: Command execution result.
    """
    command_args = ['manifest']
    if resolve:
        command_args.append('--resolve')
    if freeze:
        command_args.append('--freeze')
    if validate:
        command_args.append('--validate')
    if path:
        command_args.append('--path')
    if untracked:
        command_args.append('--untracked')
    if out:
        command_args.extend(['-o', out])
    if active_only:
        command_args.append('--active-only')
    return run_west_command(command_args)

# --- MCP Tool for `west compare` ---
@mcp.tool()
def compare_projects(
    projects: Optional[List[str]] = None,
    all: bool = False,
    exit_code: bool = False,
    ignore_branches: bool = False,
    no_ignore_branches: bool = False,
) -> Dict[str, Any]:
    """
    Compares project working tree state against the last 'west update'.

    Args:
        projects (List[str], optional): Projects to operate on.
        all (bool, optional): Include inactive projects.
        exit_code (bool, optional): Exit with status 1 if there are differences.
        ignore_branches (bool, optional): Ignore branches with clean working trees.
        no_ignore_branches (bool, optional): Don't ignore branches.

    Returns:
        dict: Command execution result.
    """
    command_args = ['compare']
    if all:
        command_args.append('-a')
    if exit_code:
        command_args.append('--exit-code')
    if ignore_branches:
        command_args.append('--ignore-branches')
    if no_ignore_branches:
        command_args.append('--no-ignore-branches')
    if projects:
        command_args.extend(projects)
    return run_west_command(command_args)

# --- MCP Tool for `west diff` ---
@mcp.tool()
def diff_projects(
    projects: Optional[List[str]] = None,
    all: bool = False,
    manifest: bool = False,
    git_diff_args: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Runs 'git diff' on specified projects.

    Args:
        projects (List[str], optional): Projects to operate on.
        all (bool, optional): Include inactive projects.
        manifest (bool, optional): Show changes relative to 'manifest-rev'.
        git_diff_args (List[str], optional): Arguments to pass to 'git diff'.

    Returns:
        dict: Command execution result.
    """
    command_args = ['diff']
    if all:
        command_args.append('-a')
    if manifest:
        command_args.append('-m')
    if projects:
        command_args.extend(projects)
    if git_diff_args:
        command_args.append('--')
        command_args.extend(git_diff_args)
    return run_west_command(command_args)

# --- MCP Tool for `west status` ---
@mcp.tool()
def status_projects(
    projects: Optional[List[str]] = None,
    all: bool = False,
    git_status_args: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Runs 'git status' on specified projects.

    Args:
        projects (List[str], optional): Projects to operate on.
        all (bool, optional): Include inactive projects.
        git_status_args (List[str], optional): Arguments to pass to 'git status'.

    Returns:
        dict: Command execution result.
    """
    command_args = ['status']
    if all:
        command_args.append('-a')
    if projects:
        command_args.extend(projects)
    if git_status_args:
        command_args.append('--')
        command_args.extend(git_status_args)
    return run_west_command(command_args)

# --- MCP Tool for `west forall` ---
@mcp.tool()
def forall_projects(
    command: str,
    projects: Optional[List[str]] = None,
    cwd: Optional[str] = None,
    all: bool = False,
    group: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Runs a command in each specified project.

    Args:
        command (str): The command to run.
        projects (List[str], optional): Projects to operate on.
        cwd (str, optional): Directory to run commands from.
        all (bool, optional): Include inactive projects.
        group (List[str], optional): Only run on projects in these groups.

    Returns:
        dict: Command execution result.
    """
    command_args = ['forall', '-c', command]
    if cwd:
        command_args.extend(['-C', cwd])
    if all:
        command_args.append('-a')
    if group:
        for g in group:
            command_args.extend(['-g', g])
    if projects:
        command_args.extend(projects)
    return run_west_command(command_args)

# --- MCP Tool for `west grep` ---
@mcp.tool()
def grep_projects(
    pattern: str,
    projects: Optional[List[str]] = None,
    tool: Optional[str] = None,
    tool_path: Optional[str] = None,
    grep_args: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Runs grep or a grep-like tool in specified projects.

    Args:
        pattern (str): The pattern to search for.
        projects (List[str], optional): Projects to operate on.
        tool (str, optional): The grep tool to use ('git-grep', 'ripgrep', 'grep').
        tool_path (str, optional): Path to the grep tool executable.
        grep_args (List[str], optional): Arguments to pass to the grep tool.

    Returns:
        dict: Command execution result.
    """
    command_args = ['grep']
    if tool:
        command_args.extend(['--tool', tool])
    if tool_path:
        command_args.extend(['--tool-path', tool_path])
    if projects:
        for p in projects:
            command_args.extend(['-p', p])
    command_args.append(pattern)
    if grep_args:
        command_args.append('--')
        command_args.extend(grep_args)
    return run_west_command(command_args)

# --- MCP Tool for `west config` ---
@mcp.tool()
def manage_config(
    name: Optional[str] = None,
    value: Optional[str] = None,
    list: bool = False,
    delete: bool = False,
    delete_all: bool = False,
    append: bool = False,
    scope: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Manages west configuration files.

    Args:
        name (str, optional): The name of the config option.
        value (str, optional): The value to set for the config option.
        list (bool, optional): List all options and their values.
        delete (bool, optional): Delete an option in one config file.
        delete_all (bool, optional): Delete an option everywhere it's set.
        append (bool, optional): Append to an existing value.
        scope (str, optional): The scope to use ('system', 'global', 'local').

    Returns:
        dict: Command execution result.
    """
    command_args = ['config']
    if list:
        command_args.append('-l')
    if delete:
        command_args.append('-d')
    if delete_all:
        command_args.append('-D')
    if append:
        command_args.append('-a')
    if scope:
        command_args.append(f'--{scope}')
    if name:
        command_args.append(name)
    if value:
        command_args.append(value)
    return run_west_command(command_args)



# --- MCP Tool for `west twister` ---
@mcp.tool()
def run_twister(
    extra_test_args: Optional[List[str]] = None,
    save_tests: Optional[str] = None,
    load_tests: Optional[str] = None,
    testsuite_root: Optional[List[str]] = None,
    only_failed: bool = False,
    list_tests: bool = False,
    test_tree: bool = False,
    integration: bool = False,
    emulation_only: bool = False,
    device_testing: bool = False,
    generate_hardware_map: Optional[str] = None,
    simulation: Optional[str] = None,
    device_serial: Optional[str] = None,
    device_serial_pty: Optional[str] = None,
    hardware_map: Optional[str] = None,
    device_flash_timeout: Optional[int] = None,
    device_flash_with_test: bool = False,
    flash_before: bool = False,
    build_only: bool = False,
    prep_artifacts_for_testing: bool = False,
    package_artifacts: Optional[str] = None,
    test_only: bool = False,
    timeout_multiplier: Optional[float] = None,
    test_pattern: Optional[str] = None,
    test: Optional[List[str]] = None,
    sub_test: Optional[str] = None,
    pytest_args: Optional[str] = None,
    ctest_args: Optional[str] = None,
    enable_valgrind: bool = False,
    enable_asan: bool = False,
    board_root: Optional[List[str]] = None,
    allow_installed_plugin: bool = False,
    arch: Optional[str] = None,
    subset: Optional[str] = None,
    shuffle_tests: bool = False,
    shuffle_tests_seed: Optional[int] = None,
    clobber_output: bool = False,
    cmake_only: bool = False,
    enable_coverage: bool = False,
    coverage: bool = False,
    gcov_tool: Optional[str] = None,
    coverage_basedir: Optional[str] = None,
    coverage_platform: Optional[str] = None,
    coverage_tool: Optional[str] = None,
    coverage_formats: Optional[str] = None,
    coverage_per_instance: bool = False,
    disable_coverage_aggregation: bool = False,
    test_config: Optional[str] = None,
    level: Optional[int] = None,
    device_serial_baud: Optional[int] = None,
    disable_suite_name_check: bool = False,
    exclude_tag: Optional[str] = None,
    enable_lsan: bool = False,
    enable_ubsan: bool = False,
    filter: Optional[str] = None,
    force_color: bool = False,
    force_toolchain: bool = False,
    create_rom_ram_report: bool = False,
    footprint_report: Optional[str] = None,
    enable_size_report: bool = False,
    footprint_from_buildlog: bool = False,
    last_metrics: bool = False,
    compare_report: Optional[str] = None,
    show_footprint: bool = False,
    footprint_threshold: Optional[float] = None,
    all_deltas: bool = False,
    size: Optional[str] = None,
    inline_logs: bool = False,
    ignore_platform_key: bool = False,
    jobs: Optional[int] = None,
    force_platform: bool = False,
    all: bool = False,
    list_tags: bool = False,
    log_file: Optional[str] = None,
    runtime_artifact_cleanup: Optional[str] = None,
    keep_artifacts: Optional[str] = None,
    ninja: bool = False,
    make: bool = False,
    no_clean: bool = False,
    aggressive_no_clean: bool = False,
    detailed_test_id: bool = False,
    no_detailed_test_id: bool = False,
    detailed_skipped_report: bool = False,
    outdir: Optional[str] = None,
    report_dir: Optional[str] = None,
    overflow_as_errors: bool = False,
    report_filtered: bool = False,
    exclude_platform: Optional[str] = None,
    persistent_hardware_map: bool = False,
    vendor: Optional[str] = None,
    platform: Optional[str] = None,
    platform_pattern: Optional[str] = None,
    platform_reports: bool = False,
    pre_script: Optional[str] = None,
    quarantine_list: Optional[str] = None,
    quarantine_verify: bool = False,
    quit_on_failure: bool = False,
    report_name: Optional[str] = None,
    report_summary: Optional[int] = None,
    report_suffix: Optional[str] = None,
    report_all_options: bool = False,
    retry_failed: Optional[int] = None,
    retry_interval: Optional[int] = None,
    retry_build_errors: bool = False,
    enable_slow: bool = False,
    enable_slow_only: bool = False,
    seed: Optional[int] = None,
    short_build_path: bool = False,
    tag: Optional[str] = None,
    timestamps: bool = False,
    no_update: bool = False,
    verbose: bool = False,
    log_level: Optional[str] = None,
    disable_warnings_as_errors: bool = False,
    west_flash: Optional[str] = None,
    west_runner: Optional[str] = None,
    fixture: Optional[str] = None,
    extra_args: Optional[str] = None,
    dry_run: bool = False,
    alt_config_root: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Runs twister, the Zephyr test runner.
    """
    command_args = ['twister']
    if save_tests:
        command_args.extend(['-E', save_tests])
    if load_tests:
        command_args.extend(['-F', load_tests])
    if testsuite_root:
        for root in testsuite_root:
            command_args.extend(['-T', root])
    if only_failed:
        command_args.append('-f')
    if list_tests:
        command_args.append('--list-tests')
    if test_tree:
        command_args.append('--test-tree')
    if integration:
        command_args.append('-G')
    if emulation_only:
        command_args.append('--emulation-only')
    if device_testing:
        command_args.append('--device-testing')
    if generate_hardware_map:
        command_args.extend(['--generate-hardware-map', generate_hardware_map])
    if simulation:
        command_args.extend(['--simulation', simulation])
    if device_serial:
        command_args.extend(['--device-serial', device_serial])
    if device_serial_pty:
        command_args.extend(['--device-serial-pty', device_serial_pty])
    if hardware_map:
        command_args.extend(['--hardware-map', hardware_map])
    if device_flash_timeout:
        command_args.extend(['--device-flash-timeout', str(device_flash_timeout)])
    if device_flash_with_test:
        command_args.append('--device-flash-with-test')
    if flash_before:
        command_args.append('--flash-before')
    if build_only:
        command_args.append('-b')
    if prep_artifacts_for_testing:
        command_args.append('--prep-artifacts-for-testing')
    if package_artifacts:
        command_args.extend(['--package-artifacts', package_artifacts])
    if test_only:
        command_args.append('--test-only')
    if timeout_multiplier:
        command_args.extend(['--timeout-multiplier', str(timeout_multiplier)])
    if test_pattern:
        command_args.extend(['--test-pattern', test_pattern])
    if test:
        for t in test:
            command_args.extend(['-s', t])
    if sub_test:
        command_args.extend(['--sub-test', sub_test])
    if pytest_args:
        command_args.extend(['--pytest-args', pytest_args])
    if ctest_args:
        command_args.extend(['--ctest-args', ctest_args])
    if enable_valgrind:
        command_args.append('--enable-valgrind')
    if enable_asan:
        command_args.append('--enable-asan')
    if board_root:
        for root in board_root:
            command_args.extend(['-A', root])
    if allow_installed_plugin:
        command_args.append('--allow-installed-plugin')
    if arch:
        command_args.extend(['-a', arch])
    if subset:
        command_args.extend(['-B', subset])
    if shuffle_tests:
        command_args.append('--shuffle-tests')
    if shuffle_tests_seed:
        command_args.extend(['--shuffle-tests-seed', str(shuffle_tests_seed)])
    if clobber_output:
        command_args.append('-c')
    if cmake_only:
        command_args.append('--cmake-only')
    if enable_coverage:
        command_args.append('--enable-coverage')
    if coverage:
        command_args.append('-C')
    if gcov_tool:
        command_args.extend(['--gcov-tool', gcov_tool])
    if coverage_basedir:
        command_args.extend(['--coverage-basedir', coverage_basedir])
    if coverage_platform:
        command_args.extend(['--coverage-platform', coverage_platform])
    if coverage_tool:
        command_args.extend(['--coverage-tool', coverage_tool])
    if coverage_formats:
        command_args.extend(['--coverage-formats', coverage_formats])
    if coverage_per_instance:
        command_args.append('--coverage-per-instance')
    if disable_coverage_aggregation:
        command_args.append('--disable-coverage-aggregation')
    if test_config:
        command_args.extend(['--test-config', test_config])
    if level:
        command_args.extend(['--level', str(level)])
    if device_serial_baud:
        command_args.extend(['--device-serial-baud', str(device_serial_baud)])
    if disable_suite_name_check:
        command_args.append('--disable-suite-name-check')
    if exclude_tag:
        command_args.extend(['-e', exclude_tag])
    if enable_lsan:
        command_args.append('--enable-lsan')
    if enable_ubsan:
        command_args.append('--enable-ubsan')
    if filter:
        command_args.extend(['--filter', filter])
    if force_color:
        command_args.append('--force-color')
    if force_toolchain:
        command_args.append('--force-toolchain')
    if create_rom_ram_report:
        command_args.append('--create-rom-ram-report')
    if footprint_report:
        command_args.extend(['--footprint-report', footprint_report])
    if enable_size_report:
        command_args.append('--enable-size-report')
    if footprint_from_buildlog:
        command_args.append('--footprint-from-buildlog')
    if last_metrics:
        command_args.append('-m')
    if compare_report:
        command_args.extend(['--compare-report', compare_report])
    if show_footprint:
        command_args.append('--show-footprint')
    if footprint_threshold:
        command_args.extend(['-H', str(footprint_threshold)])
    if all_deltas:
        command_args.append('-D')
    if size:
        command_args.extend(['-z', size])
    if inline_logs:
        command_args.append('-i')
    if ignore_platform_key:
        command_args.append('--ignore-platform-key')
    if jobs:
        command_args.extend(['-j', str(jobs)])
    if force_platform:
        command_args.append('-K')
    if all:
        command_args.append('-l')
    if list_tags:
        command_args.append('--list-tags')
    if log_file:
        command_args.extend(['--log-file', log_file])
    if runtime_artifact_cleanup:
        command_args.extend(['-M', runtime_artifact_cleanup])
    if keep_artifacts:
        command_args.extend(['--keep-artifacts', keep_artifacts])
    if ninja:
        command_args.append('-N')
    if make:
        command_args.append('-k')
    if no_clean:
        command_args.append('-n')
    if aggressive_no_clean:
        command_args.append('--aggressive-no-clean')
    if detailed_test_id:
        command_args.append('--detailed-test-id')
    if no_detailed_test_id:
        command_args.append('--no-detailed-test-id')
    if detailed_skipped_report:
        command_args.append('--detailed-skipped-report')
    if outdir:
        command_args.extend(['-O', outdir])
    if report_dir:
        command_args.extend(['-o', report_dir])
    if overflow_as_errors:
        command_args.append('--overflow-as-errors')
    if report_filtered:
        command_args.append('--report-filtered')
    if exclude_platform:
        command_args.extend(['-P', exclude_platform])
    if persistent_hardware_map:
        command_args.append('--persistent-hardware-map')
    if vendor:
        command_args.extend(['--vendor', vendor])
    if platform:
        command_args.extend(['-p', platform])
    if platform_pattern:
        command_args.extend(['--platform-pattern', platform_pattern])
    if platform_reports:
        command_args.append('--platform-reports')
    if pre_script:
        command_args.extend(['--pre-script', pre_script])
    if quarantine_list:
        command_args.extend(['--quarantine-list', quarantine_list])
    if quarantine_verify:
        command_args.append('--quarantine-verify')
    if quit_on_failure:
        command_args.append('--quit-on-failure')
    if report_name:
        command_args.extend(['--report-name', report_name])
    if report_summary:
        command_args.extend(['--report-summary', str(report_summary)])
    if report_suffix:
        command_args.extend(['--report-suffix', report_suffix])
    if report_all_options:
        command_args.append('--report-all-options')
    if retry_failed:
        command_args.extend(['--retry-failed', str(retry_failed)])
    if retry_interval:
        command_args.extend(['--retry-interval', str(retry_interval)])
    if retry_build_errors:
        command_args.append('--retry-build-errors')
    if enable_slow:
        command_args.append('-S')
    if enable_slow_only:
        command_args.append('--enable-slow-only')
    if seed:
        command_args.extend(['--seed', str(seed)])
    if short_build_path:
        command_args.append('--short-build-path')
    if tag:
        command_args.extend(['-t', tag])
    if timestamps:
        command_args.append('--timestamps')
    if no_update:
        command_args.append('-u')
    if verbose:
        command_args.append('-v')
    if log_level:
        command_args.extend(['-ll', log_level])
    if disable_warnings_as_errors:
        command_args.append('-W')
    if west_flash:
        command_args.extend(['--west-flash', west_flash])
    if west_runner:
        command_args.extend(['--west-runner', west_runner])
    if fixture:
        command_args.extend(['-X', fixture])
    if extra_args:
        command_args.extend(['-x', extra_args])
    if dry_run:
        command_args.append('-y')
    if alt_config_root:
        command_args.extend(['--alt-config-root', alt_config_root])
    if extra_test_args:
        command_args.append('--')
        command_args.extend(extra_test_args)
    return run_west_command(command_args)

# --- MCP Tool for `west sign` ---
@mcp.tool()
def sign_binary(
    build_dir: Optional[str] = None,
    quiet: bool = False,
    force: bool = False,
    tool: Optional[str] = None,
    tool_path: Optional[str] = None,
    tool_data: Optional[str] = None,
    if_tool_available: bool = False,
    bin: bool = False,
    no_bin: bool = False,
    sbin: Optional[str] = None,
    hex: bool = False,
    no_hex: bool = False,
    shex: Optional[str] = None,
    tool_opt: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Signs a Zephyr binary.
    """
    command_args = ['sign']
    if build_dir:
        command_args.extend(['-d', build_dir])
    if quiet:
        command_args.append('-q')
    if force:
        command_args.append('-f')
    if tool:
        command_args.extend(['-t', tool])
    if tool_path:
        command_args.extend(['-p', tool_path])
    if tool_data:
        command_args.extend(['-D', tool_data])
    if if_tool_available:
        command_args.append('--if-tool-available')
    if bin:
        command_args.append('--bin')
    if no_bin:
        command_args.append('--no-bin')
    if sbin:
        command_args.extend(['-B', sbin])
    if hex:
        command_args.append('--hex')
    if no_hex:
        command_args.append('--no-hex')
    if shex:
        command_args.extend(['-H', shex])
    if tool_opt:
        command_args.append('--')
        command_args.extend(tool_opt)
    return run_west_command(command_args)

# --- MCP Tool for `west spdx` ---
@mcp.tool()
def create_spdx_bom(
    init: bool = False,
    build_dir: Optional[str] = None,
    namespace_prefix: Optional[str] = None,
    spdx_dir: Optional[str] = None,
    spdx_version: Optional[str] = None,
    analyze_includes: bool = False,
    include_sdk: bool = False,
) -> Dict[str, Any]:
    """
    Creates an SPDX bill of materials.
    """
    command_args = ['spdx']
    if init:
        command_args.append('-i')
    if build_dir:
        command_args.extend(['-d', build_dir])
    if namespace_prefix:
        command_args.extend(['-n', namespace_prefix])
    if spdx_dir:
        command_args.extend(['-s', spdx_dir])
    if spdx_version:
        command_args.extend(['--spdx-version', spdx_version])
    if analyze_includes:
        command_args.append('--analyze-includes')
    if include_sdk:
        command_args.append('--include-sdk')
    return run_west_command(command_args)

# --- MCP Tool for `west sdk` ---
@mcp.tool()
def manage_sdk(
    subcommand: str,
    args: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Manages the Zephyr SDK.
    """
    command_args = ['sdk', subcommand]
    if args:
        command_args.extend(args)
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
