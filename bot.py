from web3 import Web3
from web3.exceptions import TransactionNotFound
from eth_account import Account
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from aiohttp import ClientResponseError, ClientSession, ClientTimeout, BasicAuth
from aiohttp_socks import ProxyConnector
from fake_useragent import FakeUserAgent
from http.cookies import SimpleCookie
from datetime import datetime, timezone
from colorama import Fore, Style, init
import asyncio, binascii, random, json, re, os, pytz
from dotenv import load_dotenv

init(autoreset=True)
load_dotenv()

class Colors:
    RESET = Style.RESET_ALL
    BOLD = Style.BRIGHT
    GREEN = Fore.GREEN
    YELLOW = Fore.YELLOW
    RED = Fore.RED
    CYAN = Fore.CYAN
    MAGENTA = Fore.MAGENTA
    WHITE = Fore.WHITE
    BLUE = Fore.BLUE
    BRIGHT_GREEN = Fore.LIGHTGREEN_EX
    BRIGHT_MAGENTA = Fore.LIGHTMAGENTA_EX
    BRIGHT_WHITE = Fore.LIGHTWHITE_EX
    BRIGHT_BLACK = Fore.LIGHTBLACK_EX

class Logger:
    @staticmethod
    def log(label, symbol, msg, color):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"{Colors.BRIGHT_BLACK}[{timestamp}]{Colors.RESET} {color}[{symbol}] {msg}{Colors.RESET}")

    @staticmethod
    def info(msg): Logger.log("INFO", "✓", msg, Colors.GREEN)
    @staticmethod
    def warn(msg): Logger.log("WARN", "!", msg, Colors.YELLOW)
    @staticmethod
    def error(msg): Logger.log("ERR", "✗", msg, Colors.RED)
    @staticmethod
    def success(msg): Logger.log("OK", "+", msg, Colors.GREEN)
    @staticmethod
    def loading(msg): Logger.log("LOAD", "⟳", msg, Colors.CYAN)
    @staticmethod
    def step(msg): Logger.log("STEP", "➤", msg, Colors.WHITE)
    @staticmethod
    def action(msg): Logger.log("ACTION", "↪️", msg, Colors.CYAN)
    @staticmethod
    def actionSuccess(msg): Logger.log("ACTION", "✅", msg, Colors.GREEN)

logger = Logger()

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

async def display_welcome_screen():
    clear_console()
    now = datetime.now()
    print(f"{Colors.BRIGHT_GREEN}{Colors.BOLD}")
    print("  ╔══════════════════════════════════════╗")
    print("  ║           KITE AI  B O T            ║")
    print("  ║                                      ║")
    print(f"  ║     {Colors.YELLOW}{now.strftime('%H:%M:%S %d.%m.%Y')}{Colors.BRIGHT_GREEN}           ║")
    print("  ║                                      ║")
    print("  ║     Kiteai TESTNET AUTOMATION         ║")
    print(f"  ║   {Colors.BRIGHT_WHITE}ZonaAirdrop{Colors.BRIGHT_GREEN}  |  t.me/ZonaAirdr0p   ║")
    print("  ╚══════════════════════════════════════╝")
    print(f"{Colors.RESET}")
    await asyncio.sleep(1)

    
class KiteAi:
    def __init__(self) -> None:
        self.KITE_AI = {
            "name": "KITE AI",
            "rpc_url": "https://rpc-testnet.gokite.ai/",
            "explorer": "https://testnet.kitescan.ai/tx/",
            "tokens": [
                { "type": "native", "ticker": "KITE", "address": "0x0BBB7293c08dE4e62137a557BC40bc12FA1897d6" },
                { "type": "erc20", "ticker": "Bridged ETH", "address": "0x7AEFdb35EEaAD1A15E869a6Ce0409F26BFd31239" }
            ],
            "chain_id": 2368
        }
        self.BASE_SEPOLIA = {
            "name": "BASE SEPOLIA",
            "rpc_url": "https://base-sepolia-rpc.publicnode.com/",
            "explorer": "https://sepolia.basescan.org/tx/",
            "tokens": [
                { "type": "native", "ticker": "ETH", "address": "0x226D7950D4d304e749b0015Ccd3e2c7a4979bB7C" },
                { "type": "erc20", "ticker": "Bridged KITE", "address": "0xFB9a6AF5C014c32414b4a6e208a89904c6dAe266" }
            ],
            "chain_id": 84532
        }
        self.NATIVE_CONTRACT_ABI = json.loads('''[
            {"type":"function","name":"send","stateMutability":"payable","inputs":[{"name":"_destChainId","type":"uint256"},{"name":"_recipient","type":"address"},{"name":"_amount","type":"uint256"}],"outputs":[]}
        ]''')
        self.ERC20_CONTRACT_ABI = json.loads('''[
            {"type":"function","name":"send","stateMutability":"nonpayable","inputs":[{"name":"_destChainId","type":"uint256"},{"name":"_recipient","type":"address"},{"name":"_amount","type":"uint256"}],"outputs":[]},
            {"type":"function","name":"balanceOf","stateMutability":"view","inputs":[{"name":"address","type":"address"}],"outputs":[{"name":"","type":"uint256"}]},
            {"type":"function","name":"allowance","stateMutability":"view","inputs":[{"name":"owner","type":"address"},{"name":"spender","type":"address"}],"outputs":[{"name":"","type":"uint256"}]},
            {"type":"function","name":"approve","stateMutability":"nonpayable","inputs":[{"name":"spender","type":"address"},{"name":"amount","type":"uint256"}],"outputs":[{"name":"","type":"bool"}]},
            {"type":"function","name":"decimals","stateMutability":"view","inputs":[],"outputs":[{"name":"","type":"uint8"}]}
        ]''')
        self.TESTNET_API = "https://testnet.gokite.ai"
        self.BRIDGE_API = "https://bridge-backend.prod.gokite.ai"
        self.NEO_API = "https://neo.prod.gokite.ai/v2"
        self.OZONE_API = "https://ozone-point-system.prod.gokite.ai"
        self.SITE_KEY = "6Lc_VwgrAAAAALtx_UtYQnW-cFg8EPDgJ8QVqkaz"
        self.KITE_AI_SUBNET = "0xb132001567650917d6bd695d1fab55db7986e9a5"
        self.CAPTCHA_KEY = None
        self.TESTNET_HEADERS = {}
        self.BRIDGE_HEADERS = {}
        self.proxies = []
        self.proxy_index = 0
        self.account_proxies = {}
        self.auth_tokens = {}
        self.header_cookies = {}
        self.access_tokens = {}
        self.auto_faucet = False
        self.auto_quiz = False
        self.auto_stake = False
        self.auto_unstake = False
        self.auto_chat = False
        self.auto_bridge = False
        self.chat_count = 0
        self.bridge_count = 0
        self.min_bridge_amount = 0
        self.max_bridge_amount = 0
        self.agent_lists = []

    def clear_terminal(self):
        clear_console()

    async def welcome(self): # Made async
        await display_welcome_screen()

    def format_seconds(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

    def load_2captcha_key(self):
        try:
            with open("2captcha_key.txt", 'r') as file:
                captcha_key = file.read().strip()
            return captcha_key
        except Exception as e:
            return None

    def load_ai_agents(self):
        filename = "agents.json"
        try:
            if not os.path.exists(filename):
                logger.error(f"File {filename} Not Found.")
                return []

            with open(filename, 'r') as file:
                data = json.load(file)
                if isinstance(data, list):
                    return data
                return []
        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON from {filename}.")
            return []

    async def load_proxies(self, use_proxy_choice: int):
        filename = "proxy.txt"
        try:
            # Pilihan 1 sekarang adalah Proxyscrape Free Proxy (sebelumnya pilihan 2)
            if use_proxy_choice == 1: # if use_proxy_choice == 1 (Proxyscrape Free Proxy)
                async with ClientSession(timeout=ClientTimeout(total=30)) as session:
                    async with session.get("https://raw.githubusercontent.com/monosans/proxy-list/refs/heads/main/proxies/all.txt") as response:
                        response.raise_for_status()
                        content = await response.text()
                        with open(filename, 'w') as f:
                            f.write(content)
                        self.proxies = [line.strip() for line in content.splitlines() if line.strip()]
            # Pilihan 2 sekarang adalah Tanpa Proxy (sebelumnya pilihan 3)
            # else: if use_proxy_choice == 2 (Run Without Proxy) - No proxy loading needed

            if not self.proxies and use_proxy_choice == 1: # Check only if proxy was intended to be loaded
                logger.error("No Proxies Found.")
                return

            if use_proxy_choice == 1:
                logger.info(f"Proxies Total : {len(self.proxies)}")

        except Exception as e:
            logger.error(f"Failed To Load Proxies: {e}")
            self.proxies = []

    def check_proxy_schemes(self, proxies):
        schemes = ["http://", "https://", "socks4://", "socks5://"]
        if any(proxies.startswith(scheme) for scheme in schemes):
            return proxies
        return f"http://{proxies}"

    def get_next_proxy_for_account(self, account):
        if account not in self.account_proxies:
            if not self.proxies:
                return None
            proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
            self.account_proxies[account] = proxy
            self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return self.account_proxies[account]

    def rotate_proxy_for_account(self, account):
        if not self.proxies:
            return None
        proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
        self.account_proxies[account] = proxy
        self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return proxy

    def build_proxy_config(self, proxy=None):
        if not proxy:
            return None, None, None

        if proxy.startswith("socks"):
            connector = ProxyConnector.from_url(proxy)
            return connector, None, None

        elif proxy.startswith("http"):
            match = re.match(r"http://(.*?):(.*?)@(.*)", proxy)
            if match:
                username, password, host_port = match.groups()
                clean_url = f"http://{host_port}"
                auth = BasicAuth(username, password)
                return None, clean_url, auth
            else:
                return None, proxy, None

        raise Exception("Unsupported Proxy Type.")

    def generate_address(self, account: str):
        try:
            account = Account.from_key(account)
            address = account.address
            return address
        except Exception as e:
            logger.error(f"Error generating address: {e}")
            return None

    def mask_account(self, account):
        try:
            mask_account = account[:6] + '*' * 6 + account[-6:]
            return mask_account
        except Exception as e:
            logger.error(f"Error masking account: {e}")
            return None

    def generate_auth_token(self, address):
        try:
            key_hex = "6a1c35292b7c5b769ff47d89a17e7bc4f0adfe1b462981d28e0e9f7ff20b8f8a"

            key = bytes.fromhex(key_hex)
            iv = os.urandom(12)

            encryptor = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend()).encryptor()

            ciphertext = encryptor.update(address.encode()) + encryptor.finalize()
            auth_tag = encryptor.tag

            result = iv + ciphertext + auth_tag
            result_hex = binascii.hexlify(result).decode()

            return result_hex
        except Exception as e:
            logger.error(f"Error generating auth token: {e}")
            return None

    def generate_quiz_title(self):
        today = datetime.today().strftime('%Y-%m-%d')
        return f"daily_quiz_{today}"

    def setup_ai_agent(self, agents: list):
        agent = random.choice(agents)

        agent_name = agent["agentName"]
        service_id = agent["serviceId"]
        question = random.choice(agent["questionLists"])

        return agent_name, service_id, question

    def generate_inference_payload(self, service_id: str, question: str):
        try:
            payload = {
                "service_id": service_id,
                "subnet": "kite_ai_labs",
                "stream": True,
                "body": {
                    "stream": True,
                    "message": question
                }
            }

            return payload
        except Exception as e:
            raise Exception(f"Generate Inference Payload Failed: {str(e)}")

    def generate_receipt_payload(self, address: str, service_id: str, question: str, answer: str):
        try:
            payload = {
                "address": address,
                "service_id": service_id,
                "input": [
                    { "type":"text/plain", "value":question }
                ],
                "output": [
                    { "type":"text/plain", "value":answer }
                ]
            }

            return payload
        except Exception as e:
            raise Exception(f"Generate Req Payload Failed: {str(e)}")

    def generate_bridge_payload(self, address: str, src_chain_id: int, dest_chain_id: int, src_token: str, dest_token: str, amount: int, tx_hash: str):
        try:
            now_utc = datetime.now(timezone.utc)
            timestamp = now_utc.isoformat(timespec='milliseconds').replace('+00:00', 'Z')

            payload = {
                "source_chain_id": src_chain_id,
                "target_chain_id": dest_chain_id,
                "source_token_address": src_token,
                "target_token_address": dest_token,
                "amount": str(amount),
                "source_address": address,
                "target_address": address,
                "tx_hash": tx_hash,
                "initiated_at": timestamp
            }

            return payload
        except Exception as e:
            raise Exception(f"Generate Req Payload Failed: {str(e)}")

    def generate_bridge_option(self):
        src_chain, dest_chain = random.choice([
            (self.KITE_AI, self.BASE_SEPOLIA),
            (self.BASE_SEPOLIA, self.KITE_AI)
        ])

        src_token = random.choice(src_chain["tokens"])

        opposite_type = "erc20" if src_token["type"] == "native" else "native"
        dest_token = next(token for token in dest_chain["tokens"] if token["type"] == opposite_type)

        return {
            "option": f"{src_chain['name']} to {dest_chain['name']}",
            "rpc_url": src_chain["rpc_url"],
            "explorer": src_chain["explorer"],
            "src_chain_id": src_chain["chain_id"],
            "dest_chain_id": dest_chain["chain_id"],
            "src_token": src_token,
            "dest_token": dest_token
        }

    async def get_web3_with_check(self, address: str, rpc_url: str, use_proxy: bool, retries=3, timeout=60):
        request_kwargs = {"timeout": timeout}

        proxy = self.get_next_proxy_for_account(address) if use_proxy else None

        if use_proxy and proxy:
            request_kwargs["proxies"] = {"http": proxy, "https": proxy}

        for attempt in range(retries):
            try:
                web3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs=request_kwargs))
                web3.eth.get_block_number()
                return web3
            except Exception as e:
                if attempt < retries - 1:
                    await asyncio.sleep(3)
                    continue
                raise Exception(f"Failed to Connect to RPC: {str(e)}")

    async def get_token_balance(self, address: str, rpc_url: str, contract_address: str, token_type: str, use_proxy: bool):
        try:
            web3 = await self.get_web3_with_check(address, rpc_url, use_proxy)

            if token_type == "native":
                balance = web3.eth.get_balance(address)
                decimals = 18
            else:
                token_contract = web3.eth.contract(
                    address=web3.to_checksum_address(contract_address),
                    abi=self.ERC20_CONTRACT_ABI
                )
                balance = token_contract.functions.balanceOf(address).call()
                decimals = token_contract.functions.decimals().call()

            token_balance = balance / (10 ** decimals)
            return token_balance

        except Exception as e:
            logger.error(f"Get token balance failed: {str(e)}")
            return None

    async def send_raw_transaction_with_retries(self, account, web3, tx, retries=5):
        for attempt in range(retries):
            try:
                signed_tx = web3.eth.account.sign_transaction(tx, account)
                raw_tx = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
                tx_hash = web3.to_hex(raw_tx)
                return tx_hash
            except TransactionNotFound:
                pass
            except Exception as e:
                pass
            await asyncio.sleep(2 ** attempt)
        raise Exception("Transaction Hash Not Found After Maximum Retries")

    async def wait_for_receipt_with_retries(self, web3, tx_hash, retries=5):
        for attempt in range(retries):
            try:
                receipt = await asyncio.to_thread(web3.eth.wait_for_transaction_receipt, tx_hash, timeout=300)
                return receipt
            except TransactionNotFound:
                pass
            except Exception as e:
                pass
            await asyncio.sleep(2 ** attempt)
        raise Exception("Transaction Receipt Not Found After Maximum Retries")

    async def perform_bridge(self, account: str, address: str, rpc_url: str, dest_chain_id: int, src_address: str, amount: float, token_type: str, use_proxy: bool):
        try:
            web3 = await self.get_web3_with_check(address, rpc_url, use_proxy)

            contract_address = web3.to_checksum_address(src_address)
            abi = self.NATIVE_CONTRACT_ABI if token_type == "native" else self.ERC20_CONTRACT_ABI
            token_contract = web3.eth.contract(address=contract_address, abi=abi)

            amount_to_wei = web3.to_wei(amount, "ether")
            bridge_data = token_contract.functions.send(dest_chain_id, address, amount_to_wei)

            gas_params = {"from": address}
            if token_type == "native":
                gas_params["value"] = amount_to_wei

            estimated_gas = bridge_data.estimate_gas(gas_params)

            max_priority_fee = web3.to_wei(0.001, "gwei")
            max_fee = max_priority_fee

            tx_data = {
                "from": address,
                "gas": int(estimated_gas * 1.2),
                "maxFeePerGas": int(max_fee),
                "maxPriorityFeePerGas": int(max_priority_fee),
                "nonce": web3.eth.get_transaction_count(address, "pending"),
                "chainId": web3.eth.chain_id,
            }

            if token_type == "native":
                tx_data["value"] = amount_to_wei

            bridge_tx = bridge_data.build_transaction(tx_data)

            tx_hash = await self.send_raw_transaction_with_retries(account, web3, bridge_tx)
            receipt = await self.wait_for_receipt_with_retries(web3, tx_hash)

            block_number = receipt.blockNumber

            return tx_hash, block_number, amount_to_wei

        except Exception as e:
            logger.error(f"Perform bridge failed: {str(e)}")
            return None, None, None

    async def print_timer(self, type: str):
        for remaining in range(random.randint(5, 10), 0, -1):
            current_time = datetime.now().strftime("%H:%M:%S")
            print(
                f"{Colors.CYAN + Colors.BOLD}[{current_time}]{Colors.RESET}"
                f"{Colors.WHITE + Colors.BOLD} | {Colors.RESET}"
                f"{Colors.BLUE + Colors.BOLD}Wait For{Colors.RESET}"
                f"{Colors.WHITE + Colors.BOLD} {remaining} {Colors.RESET}"
                f"{Colors.BLUE + Colors.BOLD}Seconds For Next {type}...{Colors.RESET}",
                end="\r",
                flush=True
            )
            await asyncio.sleep(1)
        print(" " * 80, end="\r") # Clear the line after countdown

    def print_chat_question(self):
        while True:
            try:
                chat_count = int(input(f"{Colors.YELLOW + Colors.BOLD}AI Agent Chat Count? -> {Colors.RESET}").strip())
                if chat_count > 0:
                    self.chat_count = chat_count
                    break
                else:
                    print(f"{Colors.RED + Colors.BOLD}Please enter positive number.{Colors.RESET}")
            except ValueError:
                print(f"{Colors.RED + Colors.BOLD}Invalid input. Enter a number.{Colors.RESET}")

    def print_bridge_question(self):
        while True:
            try:
                bridge_count = int(input(f"{Colors.YELLOW + Colors.BOLD}Bridge Transaction Count? -> {Colors.RESET}").strip())
                if bridge_count > 0:
                    self.bridge_count = bridge_count
                    break
                else:
                    print(f"{Colors.RED + Colors.BOLD}Please enter positive number.{Colors.RESET}")
            except ValueError:
                print(f"{Colors.RED + Colors.BOLD}Invalid input. Enter a number.{Colors.RESET}")

        while True:
            try:
                min_bridge_amount = float(input(f"{Colors.YELLOW + Colors.BOLD}Min Bridge Amount? -> {Colors.RESET}").strip())
                if min_bridge_amount > 0:
                    self.min_bridge_amount = min_bridge_amount
                    break
                else:
                    print(f"{Colors.RED + Colors.BOLD}Amount must be greater than 0.{Colors.RESET}")
            except ValueError:
                print(f"{Colors.RED + Colors.BOLD}Invalid input. Enter a number.{Colors.RESET}")

        while True:
            try:
                max_bridge_amount = float(input(f"{Colors.YELLOW + Colors.BOLD}Max Bridge Amount? -> {Colors.RESET}").strip())
                if max_bridge_amount >= min_bridge_amount:
                    self.max_bridge_amount = max_bridge_amount
                    break
                else:
                    print(f"{Colors.RED + Colors.BOLD}Amount must be >= Min Bridge Amount.{Colors.RESET}")
            except ValueError:
                print(f"{Colors.RED + Colors.BOLD}Invalid input. Enter a number.{Colors.RESET}")

    def print_question(self):
        while True:
            try:
                print(f"{Colors.GREEN + Colors.BOLD}Select Option:{Colors.RESET}")
                print(f"{Colors.WHITE + Colors.BOLD}1. Claim Faucet{Colors.RESET}")
                print(f"{Colors.WHITE + Colors.BOLD}2. Daily Quiz{Colors.RESET}")
                print(f"{Colors.WHITE + Colors.BOLD}3. Stake Token{Colors.RESET}")
                print(f"{Colors.WHITE + Colors.BOLD}4. Unstake Token{Colors.RESET}")
                print(f"{Colors.WHITE + Colors.BOLD}5. AI Agent Chat{Colors.RESET}")
                print(f"{Colors.WHITE + Colors.BOLD}6. Random Bridge{Colors.RESET}")
                print(f"{Colors.WHITE + Colors.BOLD}7. Run All Features{Colors.RESET}")
                option = int(input(f"{Colors.BLUE + Colors.BOLD}Choose [1/2/3/4/5/6/7] -> {Colors.RESET}").strip())

                if option in [1, 2, 3, 4, 5, 6, 7]:
                    option_type = (
                        "Claim Faucet" if option == 1 else
                        "Daily Quiz" if option == 2 else
                        "Stake Token" if option == 3 else
                        "Unstake Token" if option == 4 else
                        "AI Agent Chat" if option == 5 else
                        "Random Bridge" if option == 6 else
                        "Run All Features"
                    )
                    print(f"{Colors.GREEN + Colors.BOLD}{option_type} Selected.{Colors.RESET}")
                    break
                else:
                    print(f"{Colors.RED + Colors.BOLD}Please enter either 1, 2, 3, 4, 5, 6, or 7.{Colors.RESET}")
            except ValueError:
                print(f"{Colors.RED + Colors.BOLD}Invalid input. Enter a number (1, 2, 3, 4, 5, 6, or 7).{Colors.RESET}")

        if option == 5:
            self.print_chat_question()

        elif option == 6:
            self.print_bridge_question()

        elif option == 7:
            while True:
                auto_faucet = input(f"{Colors.YELLOW + Colors.BOLD}Auto Claim Kite Token Faucet? [y/n] -> {Colors.RESET}").strip()
                if auto_faucet in ["y", "n"]:
                    self.auto_faucet = auto_faucet == "y"
                    break
                else:
                    print(f"{Colors.RED + Colors.BOLD}Please enter 'y' or 'n'.{Colors.RESET}")

            while True:
                auto_quiz = input(f"{Colors.YELLOW + Colors.BOLD}Auto Complete Daily Quiz? [y/n] -> {Colors.RESET}").strip()
                if auto_quiz in ["y", "n"]:
                    self.auto_quiz = auto_quiz == "y"
                    break
                else:
                    print(f"{Colors.RED + Colors.BOLD}Please enter 'y' or 'n'.{Colors.RESET}")

            while True:
                auto_stake = input(f"{Colors.YELLOW + Colors.BOLD}Auto Stake Kite Token Faucet? [y/n] -> {Colors.RESET}").strip()
                if auto_stake in ["y", "n"]:
                    self.auto_stake = auto_stake == "y"
                    break
                else:
                    print(f"{Colors.RED + Colors.BOLD}Please enter 'y' or 'n'.{Colors.RESET}")

            while True:
                auto_unstake = input(f"{Colors.YELLOW + Colors.BOLD}Auto Unstake Kite Token Faucet? [y/n] -> {Colors.RESET}").strip()
                if auto_unstake in ["y", "n"]:
                    self.auto_unstake = auto_unstake == "y"
                    break
                else:
                    print(f"{Colors.RED + Colors.BOLD}Please enter 'y' or 'n'.{Colors.RESET}")

            while True:
                auto_chat = input(f"{Colors.YELLOW + Colors.BOLD}Auto Chat With AI Agent? [y/n] -> {Colors.RESET}").strip()
                if auto_chat in ["y", "n"]:
                    self.auto_chat = auto_chat == "y"

                    if self.auto_chat:
                        self.print_chat_question()
                    break
                else:
                    print(f"{Colors.RED + Colors.BOLD}Please enter 'y' or 'n'.{Colors.RESET}")

            while True:
                auto_bridge = input(f"{Colors.YELLOW + Colors.BOLD}Auto Perform Random Bridge? [y/n] -> {Colors.RESET}").strip()
                if auto_bridge in ["y", "n"]:
                    self.auto_bridge = auto_bridge == "y"

                    if self.auto_bridge:
                        self.print_bridge_question()
                    break
                else:
                    print(f"{Colors.RED + Colors.BOLD}Please enter 'y' or 'n'.{Colors.RESET}")

        while True:
            try:
                print(f"{Colors.WHITE + Colors.BOLD}1. Run With Proxyscrape Free Proxy{Colors.RESET}")
                print(f"{Colors.WHITE + Colors.BOLD}2. Run Without Proxy{Colors.RESET}")
                choose = int(input(f"{Colors.BLUE + Colors.BOLD}Choose [1/2] -> {Colors.RESET}").strip())

                if choose in [1, 2]:
                    proxy_type = (
                        "With Proxyscrape Free" if choose == 1 else
                        "Without"
                    )
                    print(f"{Colors.GREEN + Colors.BOLD}Run {proxy_type} Proxy Selected.{Colors.RESET}")
                    break
                else:
                    print(f"{Colors.RED + Colors.BOLD}Please enter either 1 or 2.{Colors.RESET}")
            except ValueError:
                print(f"{Colors.RED + Colors.BOLD}Invalid input. Enter a number (1 or 2).{Colors.RESET}")

        rotate = False
        if choose == 1: # Only ask about rotation if a proxy is chosen
            while True:
                rotate = input(f"{Colors.BLUE + Colors.BOLD}Rotate Invalid Proxy? [y/n] -> {Colors.RESET}").strip()

                if rotate in ["y", "n"]:
                    rotate = rotate == "y"
                    break
                else:
                    print(f"{Colors.RED + Colors.BOLD}Invalid input. Enter 'y' or 'n'.{Colors.RESET}")

        return option, choose, rotate

    async def solve_recaptcha(self, retries=5):
        for attempt in range(retries):
            try:
                async with ClientSession(timeout=ClientTimeout(total=60)) as session:

                    if self.CAPTCHA_KEY is None:
                        logger.warn("2Captcha Key Is None")
                        return None

                    url = f"http://2captcha.com/in.php?key={self.CAPTCHA_KEY}&method=userrecaptcha&googlekey={self.SITE_KEY}&pageurl={self.TESTNET_API}&json=1"
                    async with session.get(url=url) as response:
                        response.raise_for_status()
                        result = await response.json()

                        if result.get("status") != 1:
                            err_text = result.get("error_text", "Unknown Error")
                            logger.warn(f"2Captcha API Error: {err_text}")
                            await asyncio.sleep(5)
                            continue

                        request_id = result.get("request")
                        logger.info(f"Recaptcha Request ID: {request_id}")

                        for _ in range(30):
                            res_url = f"http://2captcha.com/res.php?key={self.CAPTCHA_KEY}&action=get&id={request_id}&json=1"
                            async with session.get(url=res_url) as res_response:
                                res_response.raise_for_status()
                                res_result = await res_response.json()

                                if res_result.get("status") == 1:
                                    recaptcha_token = res_result.get("request")
                                    return recaptcha_token
                                elif res_result.get("request") == "CAPCHA_NOT_READY":
                                    logger.info("Recaptcha Not Ready, waiting...")
                                    await asyncio.sleep(5)
                                    continue
                                else:
                                    logger.error(f"Failed to retrieve recaptcha result: {res_result.get('request')}")
                                    break

            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                logger.error(f"Recaptcha Unsolved - {str(e)}")
                return None
        return None

    async def check_connection(self, proxy_url=None):
        connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
        try:
            async with ClientSession(connector=connector, timeout=ClientTimeout(total=5)) as session:
                async with session.get(url="https://api.ipify.org?format=json", proxy=proxy, proxy_auth=proxy_auth, ssl=False) as response:
                    response.raise_for_status()
                    return True
        except (Exception, ClientResponseError) as e:
            logger.error(f"Connection Not OK - {str(e)}")

        return False

    async def user_signin(self, address: str, use_proxy: bool, retries=5):
        url = f"{self.NEO_API}/signin"
        data = json.dumps({"eoa":address})
        headers = {
            **self.TESTNET_HEADERS[address],
            "Authorization": self.auth_tokens[address],
            "Content-Length": str(len(data)),
            "Content-Type": "application/json"
        }
        await asyncio.sleep(3)
        for attempt in range(retries):
            proxy_url = self.get_next_proxy_for_account(address) if use_proxy else None
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=headers, data=data, proxy=proxy, proxy_auth=proxy_auth, ssl=False) as response:
                        response.raise_for_status()
                        result = await response.json()

                        raw_cookies = response.headers.getall('Set-Cookie', [])
                        if raw_cookies:
                            cookie = SimpleCookie()
                            cookie.load("\n".join(raw_cookies))
                            cookie_string = "; ".join([f"{key}={morsel.value}" for key, morsel in cookie.items()])
                            self.header_cookies[address] = cookie_string

                            return result
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                logger.error(f"Login Failed - {str(e)}")

        return None

    async def user_data(self, address: str, use_proxy: bool, retries=5):
        url = f"{self.OZONE_API}/me"
        headers = {
            **self.TESTNET_HEADERS[address],
            "Authorization": f"Bearer {self.access_tokens[address]}"
        }
        await asyncio.sleep(3)
        for attempt in range(retries):
            proxy_url = self.get_next_proxy_for_account(address) if use_proxy else None
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.get(url=url, headers=headers, proxy=proxy, proxy_auth=proxy_auth, ssl=False) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                logger.error(f"Fetch User Data Failed - {str(e)}")

        return None

    async def claim_faucet(self, address: str, recaptcha_token: str, use_proxy: bool, retries=5):
        url = f"{self.OZONE_API}/blockchain/faucet-transfer"
        headers = {
            **self.TESTNET_HEADERS[address],
            "Authorization": f"Bearer {self.access_tokens[address]}",
            "Content-Length":"2",
            "Content-Type": "application/json",
            "x-recaptcha-token": recaptcha_token
        }
        await asyncio.sleep(3)
        for attempt in range(retries):
            proxy_url = self.get_next_proxy_for_account(address) if use_proxy else None
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=headers, json={}, proxy=proxy, proxy_auth=proxy_auth, ssl=False) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                logger.error(f"Faucet Not Claimed - {str(e)}")

        return None

    async def create_quiz(self, address: str, use_proxy: bool, retries=5):
        url = f"{self.NEO_API}/quiz/create"
        data = json.dumps({"title":self.generate_quiz_title(), "num":1, "eoa":address})
        headers = {
            **self.TESTNET_HEADERS[address],
            "Authorization": f"Bearer {self.access_tokens[address]}",
            "Cookie": self.header_cookies[address],
            "Content-Length": str(len(data)),
            "Content-Type": "application/json"
        }
        await asyncio.sleep(3)
        for attempt in range(retries):
            proxy_url = self.get_next_proxy_for_account(address) if use_proxy else None
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=headers, data=data, proxy=proxy, proxy_auth=proxy_auth, ssl=False) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                logger.error(f"Daily Quiz GET Id Failed - {str(e)}")

        return None

    async def get_quiz(self, address: str, quiz_id: int, use_proxy: bool, retries=5):
        url = f"{self.NEO_API}/quiz/get?id={quiz_id}&eoa={address}"
        headers = {
            **self.TESTNET_HEADERS[address],
            "Authorization": f"Bearer {self.access_tokens[address]}",
            "Cookie": self.header_cookies[address]
        }
        await asyncio.sleep(3)
        for attempt in range(retries):
            proxy_url = self.get_next_proxy_for_account(address) if use_proxy else None
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.get(url=url, headers=headers, proxy=proxy, proxy_auth=proxy_auth, ssl=False) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                logger.error(f"GET Question & Answer Failed - {str(e)}")

        return None

    async def submit_quiz(self, address: str, quiz_id: int, question_id: int, quiz_answer: str, use_proxy: bool, retries=5):
        url = f"{self.NEO_API}/quiz/submit"
        data = json.dumps({"quiz_id":quiz_id, "question_id":question_id, "answer":quiz_answer, "finish":True, "eoa":address})
        headers = {
            **self.TESTNET_HEADERS[address],
            "Authorization": f"Bearer {self.access_tokens[address]}",
            "Cookie": self.header_cookies[address],
            "Content-Length": str(len(data)),
            "Content-Type": "application/json"
        }
        await asyncio.sleep(3)
        for attempt in range(retries):
            proxy_url = self.get_next_proxy_for_account(address) if use_proxy else None
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=headers, data=data, proxy=proxy, proxy_auth=proxy_auth, ssl=False) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                logger.error(f"Submit Answer Failed - {str(e)}")

        return None

    async def token_balance(self, address: str, use_proxy: bool, retries=5):
        url = f"{self.OZONE_API}/me/balance"
        headers = {
            **self.TESTNET_HEADERS[address],
            "Authorization": f"Bearer {self.access_tokens[address]}"
        }
        await asyncio.sleep(3)
        for attempt in range(retries):
            proxy_url = self.get_next_proxy_for_account(address) if use_proxy else None
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.get(url=url, headers=headers, proxy=proxy, proxy_auth=proxy_auth, ssl=False) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                logger.error(f"GET Balance Failed - {str(e)}")

        return None

    async def stake_token(self, address: str, use_proxy: bool, retries=5):
        url = f"{self.OZONE_API}/subnet/delegate"
        data = json.dumps({"subnet_address":self.KITE_AI_SUBNET, "amount":1})
        headers = {
            **self.TESTNET_HEADERS[address],
            "Authorization": f"Bearer {self.access_tokens[address]}",
            "Content-Length": str(len(data)),
            "Content-Type": "application/json"
        }
        await asyncio.sleep(3)
        for attempt in range(retries):
            proxy_url = self.get_next_proxy_for_account(address) if use_proxy else None
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=headers, data=data, proxy=proxy, proxy_auth=proxy_auth, ssl=False) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                logger.error(f"Stake Failed - {str(e)}")

        return None

    async def claim_stake_rewards(self, address: str, use_proxy: bool, retries=5):
        url = f"{self.OZONE_API}/subnet/claim-rewards"
        data = json.dumps({"subnet_address":self.KITE_AI_SUBNET})
        headers = {
            **self.TESTNET_HEADERS[address],
            "Authorization": f"Bearer {self.access_tokens[address]}",
            "Content-Length": str(len(data)),
            "Content-Type": "application/json"
        }
        await asyncio.sleep(3)
        for attempt in range(retries):
            proxy_url = self.get_next_proxy_for_account(address) if use_proxy else None
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=headers, data=data, proxy=proxy, proxy_auth=proxy_auth, ssl=False) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                logger.error(f"Unstake Failed - {str(e)}")

        return None

    async def agent_inference(self, address: str, service_id: str, question: str, use_proxy: bool, retries=5):
        url = f"{self.OZONE_API}/agent/inference"
        data = json.dumps(self.generate_inference_payload(service_id, question))
        headers = {
            **self.TESTNET_HEADERS[address],
            "Authorization": f"Bearer {self.access_tokens[address]}",
            "Content-Length": str(len(data)),
            "Content-Type": "application/json"
        }
        await asyncio.sleep(3)
        for attempt in range(retries):
            proxy_url = self.get_next_proxy_for_account(address) if use_proxy else None
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=headers, data=data, proxy=proxy, proxy_auth=proxy_auth, ssl=False) as response:
                        response.raise_for_status()
                        result = ""

                        async for line in response.content:
                            line = line.decode("utf-8").strip()
                            if line.startswith("data:"):
                                try:
                                    json_data = json.loads(line[len("data:"):].strip())
                                    delta = json_data.get("choices", [{}])[0].get("delta", {})
                                    content = delta.get("content")
                                    if content:
                                        result += content
                                except json.JSONDecodeError:
                                    continue

                        return result
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                logger.error(f"Agents Didn't Respond - {str(e)}")

        return None

    async def submit_receipt(self, address: str, sa_address: str, service_id: str, question: str, answer: str, use_proxy: bool, retries=5):
        url = f"{self.NEO_API}/submit_receipt"
        data = json.dumps(self.generate_receipt_payload(sa_address, service_id, question, answer))
        headers = {
            **self.TESTNET_HEADERS[address],
            "Authorization": f"Bearer {self.access_tokens[address]}",
            "Cookie": self.header_cookies[address],
            "Content-Length": str(len(data)),
            "Content-Type": "application/json"
        }
        await asyncio.sleep(3)
        for attempt in range(retries):
            proxy_url = self.get_next_proxy_for_account(address) if use_proxy else None
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=headers, data=data, proxy=proxy, proxy_auth=proxy_auth, ssl=False) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                logger.error(f"Submit Receipt Failed - {str(e)}")

        return None

    async def submit_bridge_transfer(self, address: str, src_chain_id: int, dest_chain_id: int, src_address: str, dest_address: str, amount_to_wei: int, tx_hash: str, use_proxy: bool, retries=5):
        url = f"{self.BRIDGE_API}/bridge-transfer"
        data = json.dumps(self.generate_bridge_payload(address, src_chain_id, dest_chain_id, src_address, dest_address, amount_to_wei, tx_hash))
        headers = {
            **self.BRIDGE_HEADERS[address],
            "Content-Length": str(len(data)),
            "Content-Type": "application/json"
        }
        await asyncio.sleep(3)
        for attempt in range(retries):
            proxy_url = self.get_next_proxy_for_account(address) if use_proxy else None
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=60)) as session:
                    async with session.post(url=url, headers=headers, data=data, proxy=proxy, proxy_auth=proxy_auth, ssl=False) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                logger.error(f"Submit Bridge Transfer Failed - {str(e)}")

        return None

    async def process_perform_bridge(self, account: str, address: str, rpc_url: str, src_chain_id: int, dest_chain_id: int, src_address: str, dest_address: str, amount: float, token_type: str, explorer: str, use_proxy: bool):
        tx_hash, block_number, amount_to_wei = await self.perform_bridge(account, address, rpc_url, dest_chain_id, src_address, amount, token_type, use_proxy)
        if tx_hash and block_number and amount_to_wei:
            logger.info("Bridge Transaction Success")
            print(f"{Colors.CYAN}↪️ Tx hash {tx_hash} ✅ Explore {explorer}{tx_hash}{Colors.RESET}") # Modified output

            submit = await self.submit_bridge_transfer(address, src_chain_id, dest_chain_id, src_address, dest_address, amount_to_wei, tx_hash, use_proxy)
            if submit:
                logger.info("Bridge Transfer Submitted Successfully")

        else:
            logger.error("Perform On-Chain Bridge Failed")

    async def process_option_1(self, address: str, user: dict, use_proxy: bool):
        is_claimable = user.get("data", {}).get("faucet_claimable", False)
        if is_claimable:
            logger.step("Faucet Claim:")

            logger.loading("Solving Recaptcha...")
            recaptcha_token = await self.solve_recaptcha()
            if recaptcha_token:
                logger.info("Recaptcha Solved Successfully")

                claim = await self.claim_faucet(address, recaptcha_token, use_proxy)
                if claim:
                    logger.success("Faucet Claimed Successfully")

        else:
            logger.warn("Faucet: Not Time to Claim")

    async def process_option_2(self, address: str, use_proxy: bool):
        logger.step("Daily Quiz:")
        create = await self.create_quiz(address, use_proxy)
        if create:
            quiz_id = create.get("data", {}).get("quiz_id")
            status = create.get("data", {}).get("status")

            if status == 0:
                quiz = await self.get_quiz(address, quiz_id, use_proxy)
                if quiz:
                    quiz_questions = quiz.get("data", {}).get("question", [])

                    if quiz_questions:
                        for quiz_question in quiz_questions:
                            if quiz_question:
                                question_id = quiz_question.get("question_id")
                                quiz_content = quiz_question.get("content")
                                quiz_answer = quiz_question.get("answer")

                                logger.info(f"Question: {quiz_content}")
                                logger.info(f"Answer  : {quiz_answer}")

                                submit_quiz = await self.submit_quiz(address, quiz_id, question_id, quiz_answer, use_proxy)
                                if submit_quiz:
                                    result = submit_quiz.get("data", {}).get("result")

                                    if result == "RIGHT":
                                        logger.success("Quiz Answered Successfully")
                                    else:
                                        logger.warn("Quiz: Wrong Answer")

                    else:
                        logger.error("GET Quiz Answer Failed")

            else:
                logger.warn("Daily Quiz: Already Answered")

    async def process_option_3(self, address: str, use_proxy: bool):
        logger.step("Stake Token:")
        balance = await self.token_balance(address, use_proxy)
        if balance:
            kite_balance = balance.get("data", {}).get("balances", {}).get("kite", 0)

            if kite_balance >= 1:
                stake = await self.stake_token(address, use_proxy)
                if stake:
                    logger.success(f"Stake Success - Amount: 1 KITE")

            else:
                logger.warn("Stake: Insufficient Kite Token Balance")

    async def process_option_4(self, address: str, use_proxy: bool):
        logger.step("Unstake Token:")
        unstake = await self.claim_stake_rewards(address, use_proxy)
        if unstake:
            reward = unstake.get("data", {}).get("claim_amount", 0)
            logger.success(f"Unstake Success - Reward: {reward} KITE")

    async def process_option_5(self, address: str, sa_address: str, use_proxy: bool):
        logger.step("AI Agents Chat:")

        used_questions_per_agent = {}

        for i in range(self.chat_count):
            logger.info(f"Interactions {i+1} Of {self.chat_count}")

            agent = random.choice(self.agent_lists)
            agent_name = agent["agentName"]
            service_id = agent["service_id"] # Corrected key
            questions = agent["questionLists"]

            if agent_name not in used_questions_per_agent:
                used_questions_per_agent[agent_name] = set()

            used_questions = used_questions_per_agent[agent_name]
            available_questions = [q for q in questions if q not in used_questions]

            if not available_questions:
                logger.warn(f"No new questions available for agent {agent_name}. Skipping.")
                continue

            question = random.choice(available_questions)

            logger.info(f"    AI Agent: {agent_name}")
            logger.info(f"    Question: {question}")

            answer = await self.agent_inference(address, service_id, question, use_proxy)
            if not answer:
                logger.error("AI Agent did not provide an answer.")
                continue

            logger.info(f"    Answer  : {answer.strip()}")

            submit = await self.submit_receipt(address, sa_address, service_id, question, answer, use_proxy)
            if submit:
                logger.success("Receipt Submitted Successfully")

            used_questions.add(question)
            await self.print_timer("Interaction")

    async def process_option_6(self, account: str, address: str, use_proxy: bool):
        logger.step("Bridge Transaction:")

        for i in range(self.bridge_count):
            logger.info(f"Bridge {i+1} / {self.bridge_count}")

            bridge_data = self.generate_bridge_option()
            option = bridge_data["option"]
            rpc_url = bridge_data["rpc_url"]
            explorer = bridge_data["explorer"]
            src_chain_id = bridge_data["src_chain_id"]
            dest_chain_id = bridge_data["dest_chain_id"]
            token_type = bridge_data["src_token"]["type"]
            src_ticker = bridge_data["src_token"]["ticker"]
            src_address = bridge_data["src_token"]["address"]
            dest_address = bridge_data["dest_token"]["address"]

            amount = round(random.uniform(self.min_bridge_amount, self.max_bridge_amount), 6)

            balance = await self.get_token_balance(address, rpc_url, src_address, token_type, use_proxy)

            logger.info(f"    Pair    : {option}")
            logger.info(f"    Balance : {balance} {src_ticker}")
            logger.info(f"    Amount  : {amount} {src_ticker}")

            if not balance or balance <= amount:
                logger.warn(f"Insufficient {src_ticker} Token Balance. Skipping bridge.")
                continue

            await self.process_perform_bridge(account, address, rpc_url, src_chain_id, dest_chain_id, src_address, dest_address, amount, token_type, explorer, use_proxy)
            await self.print_timer("Tx")

    async def process_check_connection(self, address: str, use_proxy: bool, rotate_proxy: bool):
        while True:
            proxy = self.get_next_proxy_for_account(address) if use_proxy else None
            if use_proxy: # Only print proxy info if proxy is actually being used
                logger.info(f"Proxy     : {proxy}")

            is_valid = True # Assume valid if no proxy is used
            if use_proxy:
                is_valid = await self.check_connection(proxy)

            if not is_valid:
                if rotate_proxy:
                    proxy = self.rotate_proxy_for_account(address)
                    logger.warn("Rotating proxy due to invalid connection.")
                    continue
                else:
                    logger.error("Connection failed and proxy rotation is disabled. Skipping account.")
                    return False
            return True

    async def process_user_signin(self, address: str, use_proxy: bool, rotate_proxy: bool):
        is_connected = await self.process_check_connection(address, use_proxy, rotate_proxy)
        if is_connected:
            signin = await self.user_signin(address, use_proxy)
            if signin:
                self.access_tokens[address] = signin["data"]["access_token"]
                logger.success("Login Success")
                return True
            else:
                logger.error("User sign-in failed.")
                return False
        else:
            return False

    async def process_accounts(self, account: str, address: str, option: int, use_proxy: bool, rotate_proxy: bool):
        # Print masked address at the beginning of processing each account
        logger.info(f"Memproses akun: {self.mask_account(address)}")

        signed = await self.process_user_signin(address, use_proxy, rotate_proxy)
        if signed:
            user = await self.user_data(address, use_proxy)
            if not user:
                logger.error("Failed to fetch user data. Skipping account.")
                return

            username = user.get("data", {}).get("profile", {}).get("username", "Unknown")
            sa_address = user.get("data", {}).get("profile", {}).get("smart_account_address", "Undefined")
            balance = user.get("data", {}).get("profile", {}).get("total_xp_points", 0)

            logger.info(f"Username  : {username}")
            logger.info(f"SA Address: {self.mask_account(sa_address)}")
            logger.info(f"Balance   : {balance} XP")

            if option == 1:
                await self.process_option_1(address, user, use_proxy)

            elif option == 2:
                await self.process_option_2(address, use_proxy)

            elif option == 3:
                await self.process_option_3(address, use_proxy)

            elif option == 4:
                await self.process_option_4(address, use_proxy)

            elif option == 5:
                await self.process_option_5(address, sa_address, use_proxy)

            elif option == 6:
                await self.process_option_6(account, address, use_proxy)

            else: # Option 7: Run All Features
                if self.auto_faucet:
                    await self.process_option_1(address, user, use_proxy)
                    await asyncio.sleep(5)

                if self.auto_quiz:
                    await self.process_option_2(address, use_proxy)
                    await asyncio.sleep(5)

                if self.auto_stake:
                    await self.process_option_3(address, use_proxy)
                    await asyncio.sleep(5)

                if self.auto_unstake:
                    await self.process_option_4(address, use_proxy)
                    await asyncio.sleep(5)

                if self.auto_chat:
                    await self.process_option_5(address, sa_address, use_proxy)
                    await asyncio.sleep(5)

                if self.auto_bridge:
                    await self.process_option_6(account, address, use_proxy)

    async def main(self):
        # Define wib inside the main method or as a class attribute
        wib = pytz.timezone('Asia/Jakarta') 
        try:
            with open('accounts.txt', 'r') as file:
                accounts = [line.strip() for line in file if line.strip()]

            captcha_key = self.load_2captcha_key()
            if captcha_key:
                self.CAPTCHA_KEY = captcha_key

            agents = self.load_ai_agents()
            if not agents:
                logger.error("No Agents Loaded. Exiting.")
                return

            self.agent_lists = agents

            option, use_proxy_choice, rotate_proxy = self.print_question()

            while True:
                use_proxy = False
                if use_proxy_choice == 1: # Pilihan 1 sekarang adalah Proxyscrape Free Proxy
                    use_proxy = True

                self.clear_terminal()
                await self.welcome() # Changed to await
                logger.info(f"Total Akun: {len(accounts)}")

                if use_proxy_choice == 1: # Hanya load proxy jika pilihan 1 (Proxyscrape) dipilih
                    await self.load_proxies(use_proxy_choice)

                for account in accounts:
                    if account:
                        address = self.generate_address(account)

                        if not address:
                            logger.error("Kunci Privat Tidak Valid atau Versi Library Tidak Didukung.")
                            continue

                        auth_token = self.generate_auth_token(address)
                        if not auth_token:
                            logger.error("Pembuatan Token Otentikasi Gagal. Periksa Library Kriptografi Anda.")
                            continue

                        user_agent = FakeUserAgent().random

                        self.TESTNET_HEADERS[address] = {
                            "Accept-Language": "application/json, text/plain, */*",
                            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
                            "Origin": "https://testnet.gokite.ai",
                            "Referer": "https://testnet.gokite.ai/",
                            "Sec-Fetch-Dest": "empty",
                            "Sec-Fetch-Mode": "cors",
                            "Sec-Fetch-Site": "same-site",
                            "User-Agent": user_agent
                        }

                        self.BRIDGE_HEADERS[address] = {
                            "Accept-Language": "application/json, text/plain, */*",
                            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
                            "Origin": "https://bridge.prod.gokite.ai",
                            "Referer": "https://bridge.prod.gokite.ai/",
                            "Sec-Fetch-Dest": "empty",
                            "Sec-Fetch-Mode": "cors",
                            "Sec-Fetch-Site": "same-site",
                            "User-Agent": user_agent
                        }

                        self.auth_tokens[address] = auth_token

                        await self.process_accounts(account, address, option, use_proxy, rotate_proxy)
                        await asyncio.sleep(3) # Small delay between accounts

                seconds = 24 * 60 * 60
                start_time_str = datetime.now(wib).strftime('%H:%M:%S')

                print(f"{Colors.BRIGHT_BLACK}[{start_time_str}]{Colors.RESET} {Colors.GREEN}[✓] 23:59:59 All Task Completeed 🗿", end="\r", flush=True)
                await asyncio.sleep(1)

                seconds -= 1

                while seconds >= 0:
                    formatted_time = self.format_seconds(seconds)
                    print(
                        f"{Colors.BRIGHT_BLACK}[ {datetime.now().astimezone(wib).strftime('%H:%M:%S')} ]{Colors.RESET} "
                        f"{Colors.CYAN}[⟳] Task Completeed Next cycle in: {formatted_time}",
                        end="\r",
                        flush=True
                    )
                    await asyncio.sleep(1)
                    seconds -= 1

        except FileNotFoundError:
            logger.error(f"File 'accounts.txt' Not Found.")
            return
        except Exception as e:
            logger.error(f"Error: {e}")
            raise e

if __name__ == "__main__":
    try:
        bot = KiteAi()
        asyncio.run(bot.main())
    except KeyboardInterrupt:
        logger.error("[ EXIT ] Kite Ai Ozone - BOT")
