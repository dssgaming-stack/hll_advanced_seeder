import os, sys, yaml, time, traceback, random, argparse, pprint
from datetime import datetime as dt, timedelta
from steam import game_servers as gs
import pyautogui, win32con, win32gui, pywinauto as pwa
from sanitize_filename import sanitize
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
