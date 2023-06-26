import pywifi
import math
from colorama import Fore, Style
import subprocess
import requests
import time
import threading
import sys
import os

def calculate_distance(signal_strength, frequency):
    exp = (27.55 - (20 * math.log10(frequency)) + abs(signal_strength)) / 20.0
    distance = pow(10.0, exp)
    return distance

def save_to_file(file_name, content):
    with open(file_name, "a") as file:
        file.write(content + "\n")

def ping_device(ip_address):
    result = subprocess.run(['ping', '-n', '1', ip_address], capture_output=True)
    return result.returncode == 0

def get_device_vendor(mac_address):
    url = "https://api.macvendors.com/" + mac_address
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text.strip()
    except requests.exceptions.RequestException:
        pass
    return "Nieznany"

def get_security_type(profile):
    akm_suites = profile.akm
    cipher_suites = profile.cipher

    if pywifi.const.AKM_TYPE_WPA2 in akm_suites:
        return "WPA2"
    elif pywifi.const.AKM_TYPE_WPA in akm_suites:
        return "WPA"
    elif pywifi.const.CIPHER_TYPE_WEP == cipher_suites:
        return "WEP"
    elif pywifi.const.AKM_TYPE_NONE in akm_suites:
        return "Brak zabezpieczeń"
    else:
        return "Nieznane"

def is_password_protected(profile):
    return profile.akm != pywifi.const.AKM_TYPE_NONE

def scan_networks():
    wifi = pywifi.PyWiFi()
    iface = wifi.interfaces()[0]

    if iface.status() in [pywifi.const.IFACE_DISCONNECTED, pywifi.const.IFACE_INACTIVE]:
        iface.disconnect()

    iface.scan()
    time.sleep(2)  # Czas na skanowanie sieci

    networks = iface.scan_results()

    if networks:
        log_content = "Znaleziono dostępne sieci Wi-Fi:"
        print(log_content)
        save_to_file("wifi_log.txt", log_content)
        for network in networks:
            ssid = network.ssid
            signal_strength = network.signal
            frequency = network.freq / 1000  # Przeliczamy na GHz
            distance = calculate_distance(signal_strength, frequency)
            log_content = "Nazwa: " + Fore.BLUE + "{}, Sygnał: ".format(ssid) + Fore.GREEN + "{} dBm".format(signal_strength) + Style.RESET_ALL + ", Częstotliwość: {} GHz, Odległość: ".format(frequency) + Fore.MAGENTA + Style.BRIGHT + "{:.2f} metrów".format(distance) + Style.RESET_ALL
            print(log_content)
            save_to_file("wifi_log.txt", log_content)

            # Pingowanie urządzenia
            ip_address = network.bssid
            start_time = time.time()
            ping_result = ping_device(ip_address)
            end_time = time.time()
            elapsed_time = end_time - start_time
            if ping_result:
                print("Ping do urządzenia {} udany.".format(ip_address))
                save_to_file("wifi_log.txt", "Ping do urządzenia {} udany.".format(ip_address))
            else:
                print("Ping do urządzenia {} nieudany.".format(ip_address))
                save_to_file("wifi_log.txt", "Ping do urządzenia {} nieudany.".format(ip_address))

            # Rozpoznawanie urządzenia na podstawie adresu MAC
            device_vendor = get_device_vendor(network.bssid)
            print("Producent urządzenia: {}".format(device_vendor))
            save_to_file("wifi_log.txt", "Producent urządzenia: {}".format(device_vendor))

            # Dodanie profilu sieciowego do interfejsu
            profile = iface.add_network_profile(network)

            # Wykrywanie rodzaju zabezpieczeń
            security_type = get_security_type(profile)
            print("Rodzaj zabezpieczenia: {}".format(security_type))
            save_to_file("wifi_log.txt", "Rodzaj zabezpieczenia: {}".format(security_type))

            # Sprawdzanie czy sieć jest zabezpieczona hasłem
            is_protected = is_password_protected(profile)
            print("Czy sieć jest zabezpieczona hasłem: {}".format(is_protected))
            save_to_file("wifi_log.txt", "Czy sieć jest zabezpieczona hasłem: {}".format(is_protected))

            # Wyświetlanie czasu przeskanowania urządzenia
            elapsed_time = round(elapsed_time, 2)
            elapsed_time_str = Fore.RED + "{:.2f} s".format(elapsed_time) + Style.RESET_ALL
            print("Czas przeskanowania urządzenia: {}".format(elapsed_time_str))
            save_to_file("wifi_log.txt", "Czas przeskanowania urządzenia: {}".format(elapsed_time_str))

            print()

    else:
        log_content = "Nie znaleziono żadnych dostępnych sieci Wi-Fi."
        print(log_content)
        save_to_file("wifi_log.txt", log_content)

def scan_networks_continuous():
    while True:
        scan_networks()
        print("Naciśnij 'q' aby zatrzymać program.")
        user_input = input()
        if user_input.lower() == 'q':
            break
        os.system('cls' if os.name == 'nt' else 'clear')

def show_progress():
    while True:
        sys.stdout.write(Fore.YELLOW + "." + Style.RESET_ALL)
        sys.stdout.flush()
        time.sleep(0.5)

# Uruchamianie skanowania sieci w oddzielnym wątku
scan_thread = threading.Thread(target=scan_networks_continuous)
scan_thread.start()

# Uruchamianie funkcji pokazującej postęp w oddzielnym wątku
progress_thread = threading.Thread(target=show_progress)
progress_thread.start()

# Oczekiwanie na zatrzymanie programu
print("Naciśnij 'q' aby zatrzymać program.")
while True:
    user_input = input()
    if user_input.lower() == 'q':
        break

# Zatrzymywanie wątków
scan_thread.join()
progress_thread.join()
