import sys
import requests
from flask import Flask, jsonify, request, render_template_string, render_template, redirect, url_for
from threading import Thread, Timer  # Импортируем Thread и Timer
from collections import deque

app = Flask(__name__)

# хранение инстансов
instances = deque([
    {"ip": "127.0.0.1", "port": 5001, "active": True},
    {"ip": "127.0.0.1", "port": 5002, "active": True},
    {"ip": "127.0.0.1", "port": 5003, "active": True},
])

# Параметры для Round Robin
round_robin_index = 0

# Проверка состояния инстансов 
def check_health():
    global instances
    for instance in list(instances):  # Создаем копию для изменения во время итерации
        try:
            response = requests.get(f"http://{instance['ip']}:{instance['port']}/health", timeout=2)
            if response.status_code != 200:
                instance['active'] = False
        except requests.RequestException:
            instance['active'] = False

    # Переодически вызываем эту функцию каждые 5 секунд
    Timer(5, check_health).start()


# маршрут для проверки состояния всех инстансов
@app.route("/health")
def health_check():
    check_health()
    active_instances = [inst for inst in instances if inst['active']]  # получаем все активные инстансы
    return jsonify({"active_instances": active_instances, "total_instances": len(instances)})


# Перенаправляем запрос на доступный инстанс
@app.route("/process")
def process():
    
    global round_robin_index

    active_instances = [inst for inst in instances if inst['active']] # получаем все активные инстансы

    if not active_instances:
        return "Нет доступных активных инстансов", 503
    
    instance = active_instances[round_robin_index % len(active_instances)]
    round_robin_index += 1

    # Перенаправляем запрос на выбранный инстанс
    try:
        response = requests.get(f"http://{instance['ip']}:{instance['port']}/", timeout=2)
        return response.text
    except requests.RequestException:
        return "Инстанс недоступен", 502


@app.route("/")
def index():
    return render_template("index.html", instances=instances)


@app.route("/add_instance", methods=["POST"])
def add_instance():
    ip = request.form['ip']
    port = int(request.form['port'])
    instances.append({"ip": ip, "port": port, "active": ''})
    return redirect(url_for('index'))


@app.route("/remove_instance", methods=["POST"])
def remove_instance():
    index = int(request.form['index'])
    if 0 <= index < len(instances):
        del instances[index]
        return redirect(url_for('index'))
    return "Неверный индекс", 400


# Перехватываем все запросы и перенаправляем на активные инстансы с использованием Round Robin"
@app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
def proxy(path):
    global round_robin_index
    active_instances = [inst for inst in instances if inst['active']]
    if not active_instances:
        return "Нет доступных активных инстансов", 503
    
    instance = active_instances[round_robin_index % len(active_instances)]
    round_robin_index += 1

    print(f"Перенаправление на: {instance['ip']}:{instance['port']} для пути: {path}")

    response = requests.request(
        method=request.method,
        url=f'http://{instance["ip"]}:{instance["port"]}/{path}',
        data=request.data,
        headers=request.headers,
        cookies=request.cookies
    )
    return (response.text, response.status_code, response.headers.items())


if __name__ == "__main__":
    # Стартуем поток проверки состояния инстансов
    Thread(target=check_health, daemon=True).start()
    app.run(port=int(sys.argv[1]), debug=True)
