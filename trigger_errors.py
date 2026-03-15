#!/usr/bin/env python3
"""Runs a sequence of API requests against the TaskPilot API."""
import httpx
import time

BASE = "http://localhost:8001"


def run():
    client = httpx.Client(base_url=BASE, timeout=10)

    print("Checking health...")
    r = client.get("/health")
    print(f"  {r.status_code} {r.json()}")

    print("\nListing projects...")
    r = client.get("/projects/")
    print(f"  {r.status_code} {len(r.json())} projects")

    print("\nFetching project stats (project 1)...")
    r = client.get("/projects/1/stats")
    print(f"  {r.status_code} {r.text[:120]}")

    print("\nFetching project tasks with priority filter...")
    r = client.get("/projects/2/tasks")
    print(f"  {r.status_code} {r.text[:120]}")

    print("\nFetching user profile (user 1)...")
    r = client.get("/users/1")
    print(f"  {r.status_code} {r.text[:120]}")

    print("\nFetching user profile (user 2)...")
    r = client.get("/users/2")
    print(f"  {r.status_code} {r.text[:120]}")

    print("\nFetching stats for empty project...")
    r = client.post("/projects/", params={"name": "Empty Project", "description": "No tasks yet", "owner_id": 1})
    if r.status_code == 200:
        new_id = r.json()["id"]
        r2 = client.get(f"/projects/{new_id}/stats")
        print(f"  {r2.status_code} {r2.text[:120]}")

    client.close()


if __name__ == "__main__":
    run()
