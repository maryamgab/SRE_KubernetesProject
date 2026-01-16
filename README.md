# Развертывание микросервисной системы

Проект демонстрирует развертывание микросервисной системы в Kubernetes с использованием `StatefulSet`, `Deployment`, `Service`, `Ingress`, `ConfigMap` и `Secret`.

---

## Описание

Это учебный проект, предназначенный для отработки практических навыков:

- работы с Kubernetes‑манифестами;
- развертывания stateful‑сервисов (MySQL);
- конфигурирования микросервисной архитектуры;
- контроля доступности и SLA;
- взаимодействия сервисов внутри кластера.

Проект подходит для лабораторных работ и демонстрации DevOps‑подходов.

---

## Архитектура

Система состоит из следующих компонентов:

### MySQL
- StatefulSet
- Хранение данных в PersistentVolume
- Доступ через Service
- Использование Kubernetes Secret
- Подключен MySQL exporter

### Oncall Service
- Основное приложение
- Deployment + Service
- Ingress для внешнего доступа
- ConfigMap для конфигурации
- Лог‑адаптер

### SLA Service
- Python‑сервис для проверки SLA
- Собственный Dockerfile
- Deployment в Kubernetes

### Prober
- Диагностический Python‑сервис
- Проверка доступности и health‑check
- Deployment в Kubernetes

---


## Быстрый старт

### Требования

- Kubernetes (minikube / kind / k8s cluster)
- kubectl
- Docker

### Развертывание

#### MySQL
```bash
kubectl apply -f manifests/mysql/
```

#### Oncall‑сервис
```bash
kubectl apply -f manifests/oncall/
```

#### SLA‑сервис
```bash
docker build -t sla-service ./sla
kubectl apply -f sla/deployment-sla.yaml
```

#### Prober
```bash
docker build -t prober-service ./prober
kubectl apply -f prober/deployment-prober.yaml
```

---

## Конфигурация

- Секреты БД хранятся в Kubernetes Secret
- Параметры сервисов вынесены в ConfigMap
- Возможна изоляция через namespace

---

## Мониторинг и контроль

- MySQL exporter — сбор метрик
- SLA Service — контроль доступности
- Prober — диагностика и health‑check
