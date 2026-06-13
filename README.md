# 🌤️ AI Weather Intelligence & Telemetry Dashboard

A high-performance FastAPI backend interface integrated with an open-source Large Language Model (LLM) inference engine to deliver real-time, personalized weather analytics and lifestyle recommendations.

## 🛠️ Tech Stack & Architecture

- **Inference Engine:** Groq Cloud API (`llama-3.3-70b-versatile`) for ultra-low latency structured prompt intelligence.
- **Backend Framework:** FastAPI (Python) running an asynchronous Uvicorn server wrapper.
- **Telemetry Pipelines:** Dual-source integration fetching metrics from OpenWeather API (Current/Forecast matrices) and Open-Meteo Historical Archive API (5-day comparative trend).
- **Performance Layer:** Custom in-memory dictionary caching layer protecting rate-limited API endpoints with a 10-minute validity pool.

## 🚀 Setup & Execution Instructions

### 1. Clone the Repository
```bash
git clone [https://github.com/YOUR_ACTUAL_GITHUB_USERNAME/ai-weather-intelligence-dashboard.git](https://github.com/YOUR_ACTUAL_GITHUB_USERNAME/ai-weather-intelligence-dashboard.git)
cd "weather analyser"
