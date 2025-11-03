import requests
import uuid
import time
import random
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def create_session():
    """
    Creates a requests session with retry logic.
    """
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["POST"]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def send_ngl_message(session, username, message):
    """
    Sends an anonymous message to a specified NGL user.

    :param session: The requests session to use.
    :param username: The target NGL username (e.g., 'your_username').
    :param message: The anonymous message to send.
    :return: Tuple of (success: bool, status_message: str)
    """
    url = "https://ngl.link/api/submit"
    
    # Generate a unique device ID for each request
    device_id = str(uuid.uuid4())

    payload = {
        "username": username,
        "question": message,
        "deviceId": device_id,
        "gameSlug": "",
        "referrer": ""
    }

    headers = {
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://ngl.link",
        "Referer": f"https://ngl.link/{username}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest"
    }

    try:
        response = session.post(url, data=payload, headers=headers, timeout=15)
        
        if response.status_code == 200:
            return True, "Success"
        elif response.status_code == 429:
            return False, "Rate limited (429)"
        else:
            return False, f"Status code: {response.status_code}"

    except requests.exceptions.Timeout:
        return False, "Request timeout"
    except requests.exceptions.ConnectionError:
        return False, "Connection error"
    except requests.exceptions.RequestException as e:
        return False, f"Request error: {str(e)}"


def send_multiple_messages(username, message, count, min_delay=1, max_delay=2):
    """
    Sends multiple messages with random delays and smart rate limit handling.
    
    :param username: The target NGL username.
    :param message: The message to send.
    :param count: Number of messages to send.
    :param min_delay: Minimum delay between messages in seconds.
    :param max_delay: Maximum delay between messages in seconds.
    """
    print(f"\n--- Sending {count} messages to @{username} ---\n")
    
    session = create_session()
    success_count = 0
    fail_count = 0
    consecutive_rate_limits = 0
    base_wait_time = 30  # Base wait time when rate limited
    
    i = 1
    while i <= count:
        print(f"[{i}/{count}] Sending...", end=" ", flush=True)
        
        success, message_status = send_ngl_message(session, username, message)
        
        if success:
            success_count += 1
            consecutive_rate_limits = 0  # Reset counter on success
            print(f"✓ Success")
            i += 1
            
            # Normal delay between successful messages
            if i <= count:
                delay = random.uniform(min_delay, max_delay)
                time.sleep(delay)
        
        elif "429" in message_status:
            fail_count += 1
            consecutive_rate_limits += 1
            
            # Exponential backoff: wait longer each time we hit rate limit
            wait_time = base_wait_time * (1.5 ** (consecutive_rate_limits - 1))
            wait_time = min(wait_time, 300)  # Cap at 5 minutes
            
            print(f"✗ Rate Limited!")
            print(f"  → Hit rate limit {consecutive_rate_limits} time(s)")
            print(f"  → Waiting {wait_time:.0f} seconds before retry...")
            print(f"  → This message will be retried (not counted as sent yet)")
            
            # Ask user if they want to continue after multiple rate limits
            if consecutive_rate_limits >= 3:
                print(f"\n⚠ You've been rate limited {consecutive_rate_limits} times in a row.")
                print(f"  NGL likely has a hard limit around 25-30 messages.")
                print(f"  Options:")
                print(f"    1. Wait {wait_time:.0f} seconds and continue")
                print(f"    2. Stop now")
                choice = input(f"  Enter choice (1 or 2): ").strip()
                
                if choice == "2":
                    print("\nStopping as requested.")
                    break
            
            # Countdown timer
            for remaining in range(int(wait_time), 0, -1):
                print(f"\r  → Waiting: {remaining} seconds remaining...   ", end="", flush=True)
                time.sleep(1)
            print("\r  → Wait complete. Retrying...                    ")
            
            # Don't increment i - we'll retry this message
            
        else:
            fail_count += 1
            consecutive_rate_limits = 0
            print(f"✗ Failed: {message_status}")
            i += 1
            
            # Short delay before next attempt
            time.sleep(2)
    
    print(f"\n{'='*40}")
    print(f"Summary for @{username}")
    print(f"{'='*40}")
    print(f"✓ Successful: {success_count}/{count}")
    print(f"✗ Failed: {fail_count}/{count}")
    if success_count > 0:
        print(f"Success rate: {(success_count/(success_count + fail_count))*100:.1f}%")
    print(f"{'='*40}\n")


if __name__ == "__main__":
    print("\n")
    print(" /\\_/\\  /\\_/\\  /\\_/\\  /\\_/\\  /\\_/\\  /\\_/\\  /\\_/\\  /\\_/\\ ")
    print("( o.o )( o.o )( o.o )( o.o )( o.o )( o.o )( o.o )( o.o )")
    print(" > ^ <  > ^ <  > ^ <  > ^ <  > ^ <  > ^ <  > ^ <  > ^ < ")
    print(" /\\_/\\     ____  _                                /\\_/\\ ")
    print("( o.o )   |  _ \\| |__ __  ___ __   ___  _ __     ( o.o )")
    print(" > ^ <    | |_) | '_ \\\\ \\/ / '_ \\ / _ \\| '_ \\     > ^ < ")
    print(" /\\_/\\    |  __/| | | |>  <| | | | (_) | | | |    /\\_/\\ ")
    print("( o.o )   |_|   |_| |_/_/\\_\\_| |_|\\___/|_| |_|   ( o.o )")
    print(" > ^ <                                            > ^ < ")
    print(" /\\_/\\  /\\_/\\  /\\_/\\  /\\_/\\  /\\_/\\  /\\_/\\  /\\_/\\  /\\_/\\ ")
    print("( o.o )( o.o )( o.o )( o.o )( o.o )( o.o )( o.o )( o.o )")
    print(" > ^ <  > ^ <  > ^ <  > ^ <  > ^ <  > ^ <  > ^ <  > ^ < ")
    print("\n")
    print("="*50)
    print("       NGL Anonymous Message Sender")
    print("="*50)
    
    target_username = input("\nEnter the target NGL username: ").strip()
    if not target_username:
        print("Error: Username cannot be empty.")
        exit(1)

    message_to_send = input("Enter your anonymous message: ").strip()
    if not message_to_send:
        print("Error: Message cannot be empty.")
        exit(1)
    
    try:
        message_count = int(input("How many times to send the message?: ").strip())
        if message_count < 1:
            print("Error: Count must be at least 1.")
            exit(1)
    except ValueError:
        print("Error: Please enter a valid number.")
        exit(1)
    
    # Ask for delay settings
    print("\n--- Delay Settings ---")
    print("Recommended: 1-2 seconds (faster but may hit rate limit sooner)")
    try:
        min_delay = float(input("Minimum delay in seconds (default: 1): ").strip() or "1")
        max_delay = float(input("Maximum delay in seconds (default: 2): ").strip() or "2")
        
        if min_delay < 0.5 or max_delay < min_delay:
            print("Invalid delays. Using defaults: 1-2 seconds")
            min_delay, max_delay = 1, 2
    except ValueError:
        print("Invalid input. Using default delays: 1-2 seconds")
        min_delay, max_delay = 1, 2
    
    print(f"\nConfiguration:")
    print(f"  Target: @{target_username}")
    print(f"  Message: \"{message_to_send}\"")
    print(f"  Count: {message_count}")
    print(f"  Delay: {min_delay}-{max_delay} seconds")
    print(f"\nNote: If rate limited (429), the script will automatically wait and retry.")
    
    confirm = input("\nProceed? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        exit(0)
    
    send_multiple_messages(target_username, message_to_send, message_count, min_delay, max_delay)