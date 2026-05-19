# RB Assistant

RB Assistant provides offline semantic search over the DeepSeek documentation repository using a pure-Python TF-IDF implementation. It exposes HTTP endpoints and an interactive CLI.

Endpoints:

- `/search?q=...` — keyword search
- `/semantic?q=...` — semantic TF-IDF similarity search

Install and run (example):

```bash
sudo dpkg -i rb-assistant_1.0.0_amd64.deb
sudo systemctl enable --now assistant.service
curl 'http://127.0.0.1:9001/semantic?q=code+generation'
```
