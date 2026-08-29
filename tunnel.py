"""
Avtomatlashtirilgan va Uzluksiz Tunnel Skripti (Cloudflare & Ngrok qo'llab-quvvatlaydi).
1. 5173 portni (Vite WebApp) internetga ulaydi
2. .env fayliga yangi WEBAPP_URL ni o'zi yozib qo'yadi
3. Uzilib qolmaydi, o'ta tez va xavfsiz ishlaydi
"""
import subprocess
import re
import sys
import os
import time

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def update_env(new_url):
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    if "WEBAPP_URL=" in content:
        content = re.sub(r"WEBAPP_URL=.*", f"WEBAPP_URL={new_url}", content)
    else:
        content += f"\nWEBAPP_URL={new_url}\n"
    
    with open(env_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"\n[OK] .env yangilandi: WEBAPP_URL={new_url}")

def run_cloudflare_tunnel():
    print("=" * 65)
    print("[*] Cloudflare Tunnel ishga tushirilmoqda (localhost:5173)...")
    print("=" * 65)

    bin_name = "cloudflared.cmd" if os.name == "nt" else "cloudflared"
    cmd = [bin_name, "tunnel", "--url", "http://localhost:5173"]
    
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        encoding='utf-8',
        errors='replace',
        shell=True,
    )

    url_found = False
    try:
        for line in iter(proc.stdout.readline, ''):
            print(line, end='')
            if not url_found:
                match = re.search(r'https://[a-zA-Z0-9\.\-_]+\.trycloudflare\.com', line)
                if match:
                    url = match.group(0)
                    url_found = True
                    update_env(url)
                    print("\n" + "=" * 65)
                    print(f"🎉 [SUCCESS] CLOUDFLARE HTTPS TUNNEL TAYYOR!")
                    print(f"🔗 URL: {url}")
                    print("=" * 65 + "\n")
        proc.wait()
    except KeyboardInterrupt:
        print("\nTunnel to'xtatildi.")
        proc.terminate()
        return False

    return True

def main():
    while True:
        should_continue = run_cloudflare_tunnel()
        if not should_continue:
            break
        print("\n[!] Tunnel uzildi. 3 soniyadan so'ng avtomatik qayta ulanadi...")
        time.sleep(3)

if __name__ == "__main__":
    main()
