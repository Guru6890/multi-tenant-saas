# Multi-Tenant Modular SaaS Platform

A Django-based multi-tenant SaaS platform designed to support multiple business types through a modular architecture.

> **Status:** Active development (Portfolio Project)

---

## Overview

This project aims to build a single SaaS platform that can support different types of businesses without creating separate applications for each one.

It uses a **workspace-based multi-tenant architecture** with **row-level data isolation**. Each business operates inside its own workspace, and all business data is automatically scoped to that workspace.

The platform is being designed around reusable modules that can be combined to support multiple business types.

---

## Key Features

- Workspace-based multi-tenancy
- Row-level tenant data isolation
- Middleware-based workspace context
- Tenant-aware base model with soft delete
- Custom QuerySets and Managers
- Service layer for business logic
- Selector layer for data retrieval
- Role and permission-based authorization
- Modular architecture (Inventory, CRM, and more)

---

## Architecture

```text
Request
  │
  ▼
Middleware (sets current workspace)
  │
  ▼
Workspace Context
  │
  ├── Selectors (data retrieval)
  └── Services (business logic)
        │
        ▼
  Tenant-aware Models → Database
```

---

## Multi-Tenancy Model

* **User**
  * Workspace Membership
    * **Workspace**
      * Business Data *(automatically scoped)*

---

## Tech Stack

- Python
- Django + Django ORM
- PostgreSQL *(recommended)*
- HTML / CSS *(basic UI for now)*

---

## Project Roadmap

### 🟢 Completed
- Core multi-tenancy foundation
- Workspace context and middleware
- Tenant-aware base model
- Soft-delete infrastructure
- Authorization foundation
- Inventory domain models
- Inventory selectors and service layer
- Inventory business rules & validation

### 🟡 In Progress
- CRM module
- Automated tests
- UI improvements

### 🔵 Planned
- Billing module
- POS module
- Expanded test coverage
- Production deployment
