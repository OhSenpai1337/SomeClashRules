import socket
import ipaddress
import yaml
import subprocess
import os
from datetime import datetime

# Функция для чтения доменов из файла
def read_domains_from_file(filename):
    with open(filename, 'r') as file:
        domains = file.read().splitlines()
    return domains

# Получаем IP-адреса для каждого домена
def get_ip_from_domain(domain):
    try:
        ip = socket.gethostbyname(domain)
        return ip
    except socket.error as e:
        print(f"Не удалось получить IP для {domain}: {e}")
        return None

# Объединяем IP-адреса в подсети /32 и /24
def aggregate_ips(ips):
    ip_networks = [ipaddress.ip_network(ip + '/32', strict=False) for ip in ips]
    ip_networks = sorted(ip_networks, key=lambda x: x.network_address)

    aggregated_ips = []
    current_supernet = None

    for net in ip_networks:
        if current_supernet is None or current_supernet != net.supernet(new_prefix=24):
            current_supernet = net.supernet(new_prefix=24)
            matching_ips = [n for n in ip_networks if n.supernet(new_prefix=24) == current_supernet]
            if len(matching_ips) > 1:
                aggregated_ips.append(current_supernet)
                ip_networks = [n for n in ip_networks if n.supernet(new_prefix=24) != current_supernet]
            else:
                aggregated_ips.append(net)
        else:
            continue
    
    return aggregated_ips

# Генерация файла в формате YAML
def generate_yaml(aggregated_ips):
    payload = [f"'{ip}'" for ip in aggregated_ips]  # Добавляем одинарные кавычки к IP-адресам
    data = {'payload': payload}
    with open('Discord_RPC.yaml', 'w') as yaml_file:
        yaml.dump(data, yaml_file, default_flow_style=False, allow_unicode=True, default_style="'")
    print("Файл Discord_RPC.yaml создан")

# Публикация файла на GitHub
def publish_to_github():
    try:
        # Получаем текущую дату и время
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        commit_message = f'Auto-update Discord_RPC.yaml on {current_time}'

        # Добавляем файл к индексу Git
        subprocess.run(['git', 'add', 'Discord_RPC.yaml'], check=True)
        
        # Коммит с датой и временем
        subprocess.run(['git', 'commit', '-m', commit_message], check=True)
        
        # Пуш изменений на GitHub (проверьте название основной ветки)
        subprocess.run(['git', 'push', 'origin', 'master'], check=True)  # Используем 'master' вместо 'main'
        
        print(f"Файл успешно опубликован на GitHub с коммитом: {commit_message}")
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при публикации на GitHub: {e}")

if __name__ == '__main__':
    # Чтение доменов из файла
    domains = read_domains_from_file('domains.txt')
    ips = [get_ip_from_domain(domain) for domain in domains if get_ip_from_domain(domain)]
    
    if ips:
        aggregated_ips = aggregate_ips(ips)
        generate_yaml(aggregated_ips)
        
        # Публикация на GitHub
        publish_to_github()
    else:
        print("Не удалось получить IP-адреса.")
