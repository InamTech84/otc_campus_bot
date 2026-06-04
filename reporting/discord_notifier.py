import requests
import yaml

def send_discord_message(message: str):
    try:
        with open("config/discord.yaml") as f:
            config = yaml.safe_load(f)
        
        webhook_url = config.get("webhook_url", "")
        
        if not webhook_url or "YOUR_DISCORD" in webhook_url:
            print("Discord webhook URL not set or invalid.")
            return
        
        payload = {"content": message}
        response = requests.post(webhook_url, json=payload, timeout=10)
        
        if response.status_code == 204:
            print("Message sent to Discord successfully.")
        else:
            print(f"Failed to send message. Status: {response.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")
