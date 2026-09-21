Securing personal NetworkGrid

A self-contained, reproducible virtual network environment designed to simulate a hardened corporate perimeter.

🎯 Scenario

Wishing Well Holdings has deployed their new external operations portal. The environment has been designed with defensive hardening controls across all tiers.

Your objective as an external security evaluator is to assess the network perimeter, discover any internal attack surface, and retrieve the **3 Proof-of-Breach (PoB) tokens** hidden across the infrastructure:

* **Token 1:** Perimeter Access
* **Token 2:** Internal Host Compromise
* **Token 3:** Core Data Extraction

🚀 Setup & Launch

Prerequisites
* [Docker](https://docs.docker.com/get-docker/)
* [Docker Compose](https://docs.docker.com/compose/)

Quick Start
1. Clone the repository:
   ```bash
   git clone https://github.com/8shelly8/Networkgrid.git
   cd Networkgrid

  2. Boot the virtual network:
docker compose up -d --build

  3. Access the perimeter:
  Open your browser to http://localhost:8080.

  Teardown

  When finished, stop the environment and remove virtual networks:

docker compose down -v

⚠️ Documentation

For security reviewers, hiring managers, and evaluators:
* **Architecture & Defenses:** A breakdown of the network topology, defensive controls, and verification commands is in [Writeup.md](file:///home/shelly/Networkgrid/Writeup.md).
* **Attack Walkthrough:** The step-by-step solution to capture all three flags is documented in [Walkthrough.md](file:///home/shelly/Networkgrid/Walkthrough.md) (Contains Spoilers).
