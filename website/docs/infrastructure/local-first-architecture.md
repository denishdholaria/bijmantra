---
id: local-first-architecture
sidebar_position: 1
---

# Local-First PWA Architecture

A critical non-functional requirement of BijMantra is field resilience. The platform is designed for agronomists, breeders, and field workers who operate in zones with highly intermittent or zero connectivity.

> **The Authentication Boundary:** It is important to clarify that BijMantra is not a "100% offline" standalone app. **An internet connection is strictly required to authenticate (log in) and perform the initial data synchronization.** Only after this initial handshake can the user take the device into an offline environment to perform core fieldwork.

## The Local-First Sync Paradigm

BijMantra abandons the traditional REST API approach for core field data in favor of a **Local-First, Reactive Architecture**.

### 1. The Local Source of Truth
When an action is performed (e.g., recording a phenotype, registering a new cross), the application writes exclusively to the *local* device database.
The UI reacts immediately to this local change. There is no waiting for a network request to resolve.

### 2. Polyglot Persistence
- **IndexedDB**: The underlying storage medium in the browser.
- **RxDB**: The reactive NoSQL database built on top of IndexedDB. It handles the complex logic of query subscriptions and multi-tab synchronization.

### 3. Background Synchronization
When the device detects a stable connection, the background sync engine engages. It uses a replication protocol to merge local changes with the central sovereign database and pull down any remote updates.

## Challenges for Open Source Contributors
We are actively seeking experts in distributed systems to solve:
- **Conflict Resolution**: How do we handle two offline researchers editing the same plot data simultaneously?
- **Delta Sync**: How do we minimize payload size when synchronizing a massive genetic dataset over a weak 3G connection?
