import os, sys, yaml, time, traceback, random, argparse, pprint
from datetime import datetime as dt, timedelta
from steam import game_servers as gs
# debug screenshot
import pyautogui, win32con, win32gui, pywinauto as pwa
from sanitize_filename import sanitize
# project required
import colors as c, hll_game, stopwatches as sw


def try_parsing_time(possible_date, field):
    for fmt in ('%I:%M %p', '%I:%M%p'):
        try:
            return dt.strptime(possible_date, fmt)
        except ValueError:
            pass
    raise ValueError(f"Non-valid date format for field {field}: '{possible_date}'")


def split_whitespace(string):
    keywords = []

    for split in string.split(' '):
        split = split.strip()
        if split and split not in keywords:
            keywords.append(split)

    return keywords


def window_safe_focus(process_title, minimize=True):
    try:
        win_handle = pwa.findwindows.find_window(title_re=f".*{process_title}.*")
        tup = win32gui.GetWindowPlacement(win_handle)
        if minimize and tup[1] != win32con.SW_SHOWMINIMIZED:
            win32gui.ShowWindow(win_handle, win32con.SW_MINIMIZE)
            time.sleep(1)
        win32gui.ShowWindow(win_handle, win32con.SW_RESTORE)
    except:
        pass
    time.sleep(2)


def screenshot(detail, server_addr):
    debug(f'Screenshot {detail}')
    screenshots_dir = os.path.join(os.path.dirname(os.path.abspath(CONFIG_PATH)), "screenshots")
    if not os.path.exists(screenshots_dir):
        os.makedirs(screenshots_dir)

    # focus game or crash window to top
    if hll_game.is_running():
        window_safe_focus("Hell Let Loose")
    elif hll_game.did_game_crash():
        window_safe_focus("Unreal Engine 4 Crash Reporter")

    server_info = None
    if server_addr is not None:
        server_info = steam_servers[server_addr]

    detail_server = "" if server_info is None else f" - {server_info['name'][0:30]}"
    timestamp = dt.now().strftime('%Y%m%d-%H%M%S')
    screenshot_file = f"{timestamp} - {detail}{detail_server}.png"
    debug(f"saving screenshot [{screenshot_file}]")

    screenshot = pyautogui.screenshot()
    filename = sanitize(screenshot_file)
    screenshot.save(os.path.join(screenshots_dir, filename))

    # bring seed script back to top
    window_safe_focus("hll_seeding_script")


def parse_args():
    parser = argparse.ArgumentParser(description='Hell Let Loose advanced seeder')
    parser.add_argument('--config', default='seeding.yaml', help='Path to the seeding YAML file')
    parser.add_argument('--validate-config', action='store_true', help='Validate config and exit')
    parser.add_argument('--print-config', action='store_true', help='Print parsed config summary and exit')
    return parser.parse_args()


def load_seeding_yaml(config_path):
    with open(config_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)


def validate_required_sections(config):
    required_sections = ['debug', 'seeding', 'priority', 'seeded_player_limit', 'seeded_player_variability',
                         'server_query_rate', 'server_query_timeout', 'query_timeout_limit', 'check_idle_kick',
                         'player_name', 'perpetual_mode']
    for key in required_sections:
        if key not in config:
            raise KeyError(f"Missing required config key: {key}")

    for section in ['debug', 'seeding', 'priority', 'perpetual_mode']:
        if not isinstance(config[section], dict):
            raise TypeError(f"Expected mapping for config section: {section}")

    _ = bool(config['debug']['extra_logs'])
    _ = bool(config['debug']['no_game'])
    _ = bool(config['debug']['screenshots'])
    _ = str(config['seeding']['method']).lower()
    _ = try_parsing_time(config['seeding']['endtime'], 'seeding.endtime')
    _ = int(config['seeding']['minutes'])
    _ = bool(config['priority']['monitor_enabled'])
    _ = bool(config['priority']['monitor_ranked'])
    _ = try_parsing_time(config['priority']['monitor_endtime'], 'priority.monitor_endtime')
    _ = int(config['priority']['min_players'])
    _ = list(config['priority']['servers'])
    _ = int(config['seeded_player_limit'])
    _ = int(config['seeded_player_variability'])
    _ = int(config['server_query_rate'])
    _ = int(config['server_query_timeout'])
    _ = int(config['query_timeout_limit'])
    _ = bool(config['check_idle_kick'])
    _ = str(config['player_name'])
    _ = bool(config['perpetual_mode']['enabled'])
    _ = str(config['perpetual_mode']['choose_method'])
    _ = int(config['perpetual_mode']['max_servers'])
    _ = int(config['perpetual_mode']['min_players'])
    _ = list(config['perpetual_mode']['ignore_name_contains'])


def build_config_summary(config, config_path):
    return {
        'config_path': os.path.abspath(config_path),
        'seeding_method': str(config['seeding']['method']).lower(),
        'seeding_endtime': config['seeding']['endtime'],
        'seeding_minutes': int(config['seeding']['minutes']),
        'priority_monitor_enabled': bool(config['priority']['monitor_enabled']),
        'priority_monitor_ranked': bool(config['priority']['monitor_ranked']),
        'priority_min_players': int(config['priority']['min_players']),
        'priority_servers': list(config['priority']['servers']),
        'seeded_player_limit': int(config['seeded_player_limit']),
        'seeded_player_variability': int(config['seeded_player_variability']),
        'server_query_rate': int(config['server_query_rate']),
        'server_query_timeout': int(config['server_query_timeout']),
        'query_timeout_limit': int(config['query_timeout_limit']),
        'check_idle_kick': bool(config['check_idle_kick']),
        'player_name': str(config['player_name']),
        'perpetual_mode_enabled': bool(config['perpetual_mode']['enabled']),
        'perpetual_choose_method': str(config['perpetual_mode']['choose_method']),
        'perpetual_max_servers': int(config['perpetual_mode']['max_servers']),
        'perpetual_min_players': int(config['perpetual_mode']['min_players']),
        'perpetual_ignore_name_contains': list(config['perpetual_mode']['ignore_name_contains']),
    }


args = parse_args()
CONFIG_PATH = args.config
seeding_yaml = load_seeding_yaml(CONFIG_PATH)
validate_required_sections(seeding_yaml)

if args.validate_config:
    print(f"Configuration valid: {os.path.abspath(CONFIG_PATH)}")
    sys.exit(0)

if args.print_config:
    pprint.pprint(build_config_summary(seeding_yaml, CONFIG_PATH), sort_dicts=False)
    sys.exit(0)

print(f'{c.yellow}   ###############################   {c.reset}')
print(f'{c.yellow}   ###   HLL Advanced Seeder   ###   {c.reset}')
print(f'{c.yellow}   ###############################   {c.reset}')
print()

debug = seeding_yaml["debug"]
debug_extra_logs = bool(debug["extra_logs"])
debug_no_game = bool(debug["no_game"])
debug_screenshots = bool(debug["screenshots"])


def debug(log):
    if debug_extra_logs:
        print(f'{c.darkgrey}DEBUG : {log}{c.reset}')


if debug_extra_logs:
    debug(f'{c.darkgrey}Loaded YAML{c.reset}')
    debug(f'{c.darkgrey}{seeding_yaml}{c.reset}\n')

seeding = seeding_yaml["seeding"]
seeding_method = str(seeding["method"]).lower()
seeding_endtime = try_parsing_time(seeding["endtime"], "seeding.endtime")
seeding_minutes = int(seeding["minutes"])

priority = seeding_yaml["priority"]
priority_monitor = bool(priority["monitor_enabled"])
priority_monitor_ranked = bool(priority["monitor_ranked"])
priority_monitor_endtime = try_parsing_time(priority["monitor_endtime"], "priority.monitor_endtime")
priority_min_players = int(priority["min_players"])
servers = list(priority["servers"])

seeded_player_limit = int(seeding_yaml["seeded_player_limit"])
seeded_player_variability = int(seeding_yaml["seeded_player_variability"])
server_query_rate = int(seeding_yaml["server_query_rate"])
server_query_timeout = int(seeding_yaml["server_query_timeout"])
query_timeout_limit = int(seeding_yaml["query_timeout_limit"])
check_idle_kick = bool(seeding_yaml["check_idle_kick"])
player_name = seeding_yaml["player_name"]

perpetual = seeding_yaml["perpetual_mode"]
perpetual_enabled = bool(perpetual["enabled"])
perpetual_choose_method = str(perpetual["choose_method"])
perpetual_max_servers = int(perpetual["max_servers"])
perpetual_min_players = int(perpetual["min_players"])
ignore_name_contains = list(perpetual["ignore_name_contains"])

start_datetime = dt.today()
stop_datetime = start_datetime
if seeding_method == "endtime":
    stop_datetime = dt(start_datetime.year, start_datetime.month, start_datetime.day,
                       seeding_endtime.hour, seeding_endtime.minute, 0)
elif seeding_method == "minutes":
    stop_datetime += timedelta(minutes=seeding_minutes)
else:
    print(f"{c.red}[ERROR] Invalid seed.method in seeding.yaml: {seeding_method}{c.reset}")
    sys.exit(1)

print(f"{c.blue}Seeding stop: {stop_datetime}{c.reset}")


def server_a2s_info(server_addr):
    try:
        return gs.a2s_info(server_addr, timeout=server_query_timeout)
    except:
        return None


def fetch_server_info(priority_entry):
    if isinstance(priority_entry, dict):
        if "server_addr" in priority_entry:
            host, port = str(priority_entry["server_addr"]).split(":")
            return (host, int(port))
        if "steam_search" in priority_entry:
            search_terms = split_whitespace(str(priority_entry["steam_search"]))
            try:
                for server in gs.query():
                    name = str(server["name"]).lower()
                    if all(term.lower() in name for term in search_terms):
                        return (server["addr"][0], int(server["gameport"]))
            except:
                return None
    elif isinstance(priority_entry, str):
        if ":" in priority_entry:
            host, port = priority_entry.split(":")
            return (host, int(port))
    return None


def server_matches_perpetual_filters(server_info):
    if server_info is None:
        return False

    name = str(server_info["name"]).lower()
    for term in ignore_name_contains:
        if str(term).lower() in name:
            return False

    players = int(server_info["players"])
    max_players = int(server_info["max_players"])

    if players < perpetual_min_players:
        return False
    if players >= seeded_player_limit:
        return False
    if max_players <= 0:
        return False

    return True


def candidate_sort_key(server_info):
    if perpetual_choose_method == "least_populated":
        return int(server_info["players"])
    return int(server_info["players"]) * -1


def discover_perpetual_servers():
    discovered = []

    try:
        for server in gs.query():
            try:
                server_addr = (server["addr"][0], int(server["gameport"]))
                info = server_a2s_info(server_addr)
                if info is None:
                    continue
                if server_matches_perpetual_filters(info):
                    discovered.append((server_addr, info))
            except:
                continue
    except:
        return []

    if perpetual_choose_method == "random":
        random.shuffle(discovered)
    else:
        discovered = sorted(discovered, key=lambda item: candidate_sort_key(item[1]))

    return discovered[:perpetual_max_servers]


def resolve_priority_servers():
    resolved = []

    for entry in servers:
        server_addr = fetch_server_info(entry)
        if server_addr is None:
            continue

        min_players = priority_min_players
        if isinstance(entry, dict) and "min_players" in entry:
            min_players = int(entry["min_players"])

        resolved.append({
            "addr": server_addr,
            "min_players": min_players,
            "source": entry
        })

    return resolved


def player_target_limit():
    return seeded_player_limit + random.randint(0, seeded_player_variability)


def server_name(server_addr):
    if server_addr in steam_servers:
        return steam_servers[server_addr]["name"]
    return f"{server_addr[0]}:{server_addr[1]}"


def should_seed_server(server_addr, min_players):
    info = server_a2s_info(server_addr)
    if info is None:
        return None, None

    steam_servers[server_addr] = info
    players = int(info["players"])
    current_limit = player_target_limit()

    if players >= current_limit:
        return info, False
    if players < min_players:
        return info, False

    return info, True


steam_servers = {}
timeout_counts = {}
current_server_addr = None
priority_servers = resolve_priority_servers()

if len(priority_servers) == 0 and not perpetual_enabled:
    print(f"{c.red}[ERROR] No valid priority servers found and perpetual mode is disabled.{c.reset}")
    sys.exit(1)

while True:
    try:
        now = dt.now()

        if now >= stop_datetime:
            print(f"{c.yellow}Reached stop time, ending seeder.{c.reset}")
            break

        selected_server = None

        for entry in priority_servers:
            server_addr = entry["addr"]
            info, should_seed = should_seed_server(server_addr, entry["min_players"])

            if info is None:
                timeout_counts[server_addr] = timeout_counts.get(server_addr, 0) + 1
                print(f"{c.orange}Timeout querying {server_addr} ({timeout_counts[server_addr]}/{query_timeout_limit}){c.reset}")
                if timeout_counts[server_addr] >= query_timeout_limit:
                    print(f"{c.orange}Skipping {server_addr} after repeated timeouts.{c.reset}")
                continue

            timeout_counts[server_addr] = 0
            print(f"{c.cyan}[CHECK] {info['name']} - {info['players']}/{info['max_players']}{c.reset}")

            if should_seed:
                selected_server = server_addr
                break

        if selected_server is None and perpetual_enabled:
            candidates = discover_perpetual_servers()
            if len(candidates) > 0:
                selected_server = candidates[0][0]
                steam_servers[selected_server] = candidates[0][1]
                print(f"{c.purple}[PERPETUAL] Selected {candidates[0][1]['name']}{c.reset}")

        if selected_server is None:
            print(f"{c.darkgrey}No server currently needs seeding. Sleeping {server_query_rate}s...{c.reset}")
            time.sleep(server_query_rate)
            continue

        if current_server_addr != selected_server:
            print(f"{c.green}Joining server: {server_name(selected_server)}{c.reset}")

            if not debug_no_game:
                if not hll_game.is_running():
                    hll_game.launch_and_wait()
                hll_game.join_server_addr(selected_server)

            current_server_addr = selected_server
            sw.start("joined_server")

        if check_idle_kick and not debug_no_game:
            present = hll_game.is_player_present(current_server_addr, player_name, timeout=server_query_timeout)
            if present is False:
                print(f"{c.orange}Player not found on server, possible kick/disconnect. Relaunching/joining again.{c.reset}")
                if debug_screenshots:
                    screenshot("idle-or-disconnect", current_server_addr)
                hll_game.relaunch_and_wait()
                hll_game.join_server_addr(current_server_addr)
                sw.start("joined_server")

        if hll_game.did_game_crash():
            print(f"{c.red}Game crash detected. Restarting game and rejoining server.{c.reset}")
            if debug_screenshots:
                screenshot("crash-detected", current_server_addr)
            if not debug_no_game:
                hll_game.relaunch_and_wait()
                hll_game.join_server_addr(current_server_addr)
                sw.start("joined_server")

        stay_seconds = sw.seconds("joined_server")
        print(f"{c.blue}Currently seeding {server_name(current_server_addr)} for {stay_seconds}s{c.reset}")
        time.sleep(server_query_rate)

    except KeyboardInterrupt:
        print(f"\n{c.yellow}Interrupted by user.{c.reset}")
        break
    except Exception as ex:
        print(f"{c.red}[ERROR] {ex}{c.reset}")
        if debug_extra_logs:
            traceback.print_exc()
        time.sleep(server_query_rate)

if not debug_no_game and hll_game.is_running():
    print(f"{c.yellow}Stopping Hell Let Loose before exit.{c.reset}")
    hll_game.kill()

print(f"{c.green}Seeder stopped.{c.reset}")
