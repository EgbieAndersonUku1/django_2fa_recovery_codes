![Made with Python](https://img.shields.io/badge/Made%20with-Python-blue?logo=python)
![Security](https://img.shields.io/badge/Security-213--bit-brightgreen)
![Brute Force](https://img.shields.io/badge/Brute--force-Impractical-red)
![License](https://img.shields.io/badge/License-MIT-yellow)


## 🔐 Django 2FA Recovery Codes

The premises of this resuable application, is that it takes any Django application and extends that application so that it can now use the 2FA recovery codes as a backup login should you lose access.

`django-2fa-recovery-codes` is a Django app that provides a robust system for generating, storing, and managing **2FA recovery codes**. Unlike a full two-factor authentication apps, this package focuses solely on **recovery codes**, although this is a lightweight application it is a very powerful tool, offering fine-grained control and asynchronous management for better UX and performance.

### Table of Contents

* [Introduction](#introduction)
* [Features](#features)
* [How it Differs from Full Two-Factor-Auth Apps](#how-it-differs-from-full-two-factor-auth-apps)
* [2FA Recovery Code Generator](#2fa-recovery-code-generator)
* [Why It’s Secure](#why-its-secure)
  * [Entropy](#entropy)
  * [Total Combinations](#total-combinations)
* [Brute-Force Resistance](#brute-force-resistance)
* [Perspective](#perspective)
  * [Time to Crack at Different Speeds](#time-to-crack-at-different-speeds)
* [Developer Appendix 🛠️](#developer-appendix-)
* [Summary](#summary)
* [Use Cases](#use-cases)
* [Installation](#installation)
* [Quick Example](#quick-example)
* [Contributing](#contributing)
* [License](#license)


---

### Features

* Generate recovery codes in configurable batches.
* Track recovery codes individually:

  * Mark codes as used, inactive, or scheduled for deletion.
  * User the 2FA code to login which becomes invalid after a single use

* Batch management:

  * Track issued and removed codes per batch.
  * Statuses for active, invalidated, or deleted batches.

* Asynchronous cleanup using Django-Q:

  * Delete expired or invalid codes without locking the database.
  * Scheduler allows admins to set cleanup intervals (e.g., every 2 days) without touching code.
  * Optional options to email the report to the admin
  * Optional option to store user emails (Whenever the user send themselves a code) in the database
  * Optional scheduler to delete Recovery code Audit model (tracks the users, the number of code issued, time issued, etc)

 
* Secure storage:

  * Codes are hashed before saving; no plaintext storage.
* Extensible utilities for generating and verifying codes.

---

### How It Differs From A Full Two-Factor Authentication Apps?

`django-2fa-recovery-codes` is designed **solely for recovery codes**, offering fine-grained control, asynchronous management, and admin-friendly batch handling.

* User UI interface
   * Dedicated login interface page to enter your email and 2FA recovery code
   * Dashboard that allows the user to:
	      * Generate a batch of 2FA recovery codes (default=10 generated, configurable via settings flags) with expiry date or doesn't expiry
        * Regenerate code (Uses brute force rate limiter with a penalty that increases wait time if codes is regenerated within that time window)
        * Email, Delete or Download entire codes via the buttons
        * One-time verification code setup form
          * A one-time setup that allows the user to enter a 2FA code after generation (for the first time) to verify that the backend has configured it correctly without marking the code as used. The tests indicate whether the code has been set up correctly.

        * Invalidate or delete a code via interactive form
        * view batch histories
	
          #### Example a single recovery code batch View

          | Field                     | Value                                |
          | ------------------------- | ------------------------------------ |
          | Batch ID                  | 8C2655A1-8F14-4B56-AEC8-7DDA72F887A4 |
          | Expiry info               | Active                               |
          | User                      | Egbie                                |
          | Date issued               | 23 Sept. 2025, 16:21                 |
          | Date modified             | 23 Sept. 2025, 16:31                 |
          | Number of codes issued    | 10                                   |
          | Number of codes used      | 0                                    |
          | Number of deactivated     | 0                                    |
          | Number of removed         | 0                                    |
          | Has generated code batch  | True                                 |
          | Has viewed code batch     | True                                 |
          | Has downloaded code batch | False                                |
          | Has emailed code batch    | False                                |

      * Pagination to split the batch recovery codes history on different pages instead of one long page

* Focuses **exclusively on recovery codes**, rather than full 2FA flows.
* Built with **asynchronous usage** using Django-Q:
  * Automatically deletes expired or invalid codes when uses with scheduler.
  * On a successful delete scheduler generates an audit report of the number of deleted codes and sends it to admin via email. The sending of the email is optional.
  * Email sending can be configured to run **asynchronous or synchronous** depending on your environment:
    * `DEBUG = True` : uses synchronous sending (easy for development or testing).  
    * `DEBUG = False` : uses asynchronous sending (recommended for production; doesn’t block the application while sending in the background).

* **Admin-friendly view interface code management**, including the ability to scheduler deletion for expired or invalid codes e.g (every 2 days, etc) or even the audit history.
* **Individual code tracking** with granular control over each code.
* Optional configuration to  turn **logger** on or off to track the actions of users generating recovery codes, email sent, various aspect of the models, etc.
* Optional **storage of user email** in the model for auditing purposes.
* Utilises **caching** (Redis, Memcached, default cache, etc) doe
  * Pagination and page reads
  * Brute-force rate limiting
  * Other database-heavy operations
  * Reduces database hits until cache expires or updates are made.
* Built-in **logger configuration** which can be imported into settings or merged with an existing logger.
* **Email sending capabilities** via `EmailSender` library.
* **Email logging** via `EmailSenderLogger` library.
* **Maximum login attempt control** with a brute-force rate limiter:

  * Configurable penalty wait times that increase if a user retries during the wait window.
* **Brute-force rate limiter** for code generation:

  * Prevents spam and imposes a penalty if the user attempts regeneration too soon.
* Generate **codes that expire** or have no expiry.
* Allow users to **download or email codes** (one per batch).
* **Invalidate, delete a single code or an entire batch** easily.
* Users can **view batch details**, e.g., number of codes generated, emailed, or downloaded.

* **Configurable flags for developer**
#### Configuration flags settings for the Django Auth Recovery code
```python
* DJANGO_AUTH_RECOVERY_CODE_ADMIN_EMAIL
* DJANGO_AUTH_RECOVERY_CODE_ADMIN_EMAIL_HOST_USER
* DJANGO_AUTH_RECOVERY_CODE_ADMIN_USERNAME
* DJANGO_AUTH_RECOVERY_CODE_AUDIT_ENABLE_AUTO_CLEANUP
* DJANGO_AUTH_RECOVERY_CODE_AUDIT_RETENTION_DAYS
* DJANGO_AUTH_RECOVERY_CODE_MAX_VISIBLE
* DJANGO_AUTH_RECOVERY_CODE_PER_PAGE
* DJANGO_AUTH_RECOVERY_CODE_PURGE_DELETE_RETENTION_DAYS
* DJANGO_AUTH_RECOVERY_CODE_PURGE_DELETE_SCHEDULER_USE_LOGGER
* DJANGO_AUTH_RECOVERY_CODE_REDIRECT_VIEW
* DJANGO_AUTH_RECOVERY_CODE_STORE_EMAIL_LOG
* DJANGO_AUTH_RECOVERY_CODES_AUTH_RATE_LIMITER_USE_CACHE
* DJANGO_AUTH_RECOVERY_CODES_BASE_COOLDOWN
* DJANGO_AUTH_RECOVERY_CODES_BATCH_DELETE_SIZE
* DJANGO_AUTH_RECOVERY_CODES_CACHE_MAX
* DJANGO_AUTH_RECOVERY_CODES_CACHE_MIN
* DJANGO_AUTH_RECOVERY_CODES_CACHE_TTL
* DJANGO_AUTH_RECOVERY_CODES_COOLDOWN_CUTOFF_POINT
* DJANGO_AUTH_RECOVERY_CODES_COOLDOWN_MULTIPLIER
* DJANGO_AUTH_RECOVERY_CODES_DEFAULT_FILE_NAME
* DJANGO_AUTH_RECOVERY_CODES_MAX_LOGIN_ATTEMPTS
* DJANGO_AUTH_RECOVERY_KEY

                  
```


## Django 2FA Recovery Code Generator

### **Security Overview**

These 2FA recovery codes generated are designed to be **extremely secure** and practically impossible to guess. Protects against Brute force, Rainbow attacks and timed attacks

### **Code Format**

```
XXXXXX-XXXXXX-XXXXXX-XXXXXX-XXXXXX-XXXXXX
```

* **6 groups** of **6 characters** each (36 characters)
* **Alphabet:** 60 characters (`A–Z`, `a–z`, `2–9`), the app avoiding confusing characters like `0` vs `O` and `1` vs `l`
* **Cryptographically secure randomness** ensures codes are unpredictable

---

### **Entropy**

Entropy measures how unpredictable a code is, the higher the entropy, the harder it is to guess.

* **Entropy per character:**

$$
\log_2(60) \approx 5.91 \text{ bits}
$$

* **Entropy per group (6 characters):**

$$
6 \times 5.91 \approx 35.5 \text{ bits}
$$

* **Total entropy for the full 36-character code:**

$$
36 \times 5.91 \approx 213 \text{ bits}
$$

> For comparison, AES-128 encryption has 128 bits of entropy. These recovery codes are **much stronger** in terms of guessing resistance.

---

### **Total Combinations**

With 36 characters chosen from 60 possibilities each:

$$
60^{36} \approx 2 \times 10^{63} \text{ unique codes}
$$

This astronomical number of possibilities ensures that **guessing a valid code is virtually impossible**.

---

### **Brute-Force Resistance**

Even with a supercomputer that tests codes extremely quickly, brute-forcing a valid recovery code is **completely impractical**:

| Attack Speed              | Seconds   | Years     |
| ------------------------- | --------- | --------- |
| 1 billion/sec (10^9)      | 2 × 10^54 | 6 × 10^46 |
| 1 trillion/sec (10^12)    | 2 × 10^51 | 6 × 10^43 |
| 1 quintillion/sec (10^18) | 2 × 10^45 | 6 × 10^37 |

> **For comparison:** the age of the universe is only \~1.4 × 10^10 years. Even a computer testing a **quintillion codes per second** would need far longer than the universe has existed to find a valid code.

---



### What this means?

* Each character is chosen randomly from 60 possibilities.
* With 36 characters, the number of possible codes is **more than 2 followed by 63 zeros**.
* Each recovery code has **≈213 bits of entropy**, making it **extremely resistant to guessing or brute-force attacks**.
* That’s **so many possibilities** that even the fastest computers would take **longer than the age of the universe** to try them all.
* The vast number of possible codes ensures that **every code is unique and unpredictable**.
* This makes guessing a valid code virtually impossible and this is without brute rate limiter, with a rate limiter (which this app uses it is virtually impossible).

> In short: it’s **far stronger than standard encryption like AES-128**. 
> You can trust these recovery codes to keep your account safe even against attackers with enormous computational power.


---

#### Developer Appendix 🛠️

```python
import math

def brute_force_time(alphabet_size=52, chars_per_group=6, groups=6, guesses_per_second=10**9):
    total_combinations = alphabet_size ** (chars_per_group * groups)
    seconds = total_combinations / guesses_per_second
    years = seconds / (60 * 60 * 24 * 365)
    return total_combinations, seconds, years

combos, seconds, years = brute_force_time()
print(f"Total combinations: {combos:e}")
print(f"Seconds to crack: {seconds:e}")
print(f"Years to crack: {years:e}")
```

**Example output:**

```
Total combinations: 3.292e+61
Seconds to crack: 3.292e+52
Years to crack: 1.043e+45
```

---

#### ✅ Summary

* **212.8 bits recovery codes** → astronomically secure
* **≈3.3 × 10^61 combinations** → impossible to brute-force
* Even with a supercomputer, cracking a single code would take **trillions of times longer than the age of the universe**
* With **rate limiting**, brute-force becomes completely infeasible

---

#### Use Cases

* Integrate with any existing 2FA system to provide a secure set of recovery codes.
* Large-scale systems where thousands of users might need recovery codes, ensuring database performance is not impacted.
* Admin-friendly management of recovery codes, including scheduling cleanups without developer intervention.
* Systems requiring secure, hashed storage of recovery codes while retaining full control over their lifecycle.

---

## Installation

```bash
pip install django-2fa-recovery-codes
```

```python
# settings.py
INSTALLED_APPS = [
    ...
    'django_2fa_recovery_codes',
]
```

---

## Quick Example

```python
from django_2fa_recovery_codes.models import RecoveryCodeBatch

# Create a batch of 10 recovery codes for a user
plain_codes, batch_instance = RecoveryCodeBatch.create_recovery_batch(user, days_to_expire=30)


```

---


## How to Use 2FA Recovery Codes

### Setting up the Cache or using the default cache

To use this application, you can either set up a permanent cache system in the backend or allow it to use the default cache.

### Why is a cache necessary for this app?

This application is designed to be scalable, meaning it can support anything from a few users to thousands without compromising performance or putting unnecessary load on the database. It relies heavily on caching: 

  - Everything from page reads
  - Pagination
  - Brute-force rate limiting, waiting time for failed login attempts to the cooling period for regenerating new codes is computed and cached. 
  - Database-heavy operations

The database is only accessed when the cache expires or an update is made e.g the user uses, deletes or invalidates a code.


#### Cache Expiry and TTL Settings

Cache entries have a configurable **Time-To-Live (TTL)**, which determines how long the data is stored before being refreshed. The following settings are used by default:

```python
DJANGO_AUTH_RECOVERY_CODES_CACHE_TTL = 300      # Default 5 minutes
DJANGO_AUTH_RECOVERY_CODES_CACHE_MIN = 60       # Minimum 1 minute
DJANGO_AUTH_RECOVERY_CODES_CACHE_MAX = 3600     # Maximum 1 hour


```

These settings **can be adjusted by the developer** in the Django settings to balance performance with data freshness. This ensures cache expiry times remain within safe and predictable bounds.

### How does the cache work?

The cache helps prevent issues such as **race conditions** and **stale data**.

#### What is a race condition?

A race condition occurs when two or more processes try to modify the same data at the same time, leading to unpredictable results.

**Example:**

Imagine two requests to generate a new 2FA recovery code arrive simultaneously for the same user. If both try to write to the cache at the same time, one could overwrite the other, resulting in lost data. To prevent this, the application ensures that only one process can write to a specific cache key at a time.

This mechanism guarantees that cache data remains consistent, preventing conflicts and ensuring that recovery codes are always valid and reliable.

---

### What cache should I use?

That depends entirely on you. The application is designed to **use caching**, but it’s backend-agnostic. It will work with any cache supported by Django (e.g. Redis, Memcached, or in-memory cache). It assumes no cache over the other and leaves it to the developer to decide which one to use under the hood.

This flexibility is possible because the application only interacts with **Django’s cache framework abstraction**. Under the hood, all cache operations (`cache.set`, `cache.get`, etc.) are handled by Django. The actual backend Redis, Memcached, or in-memory is just a plug-in configured in `settings.py`.

* **Redis** : A common choice for production, especially in distributed systems. It supports persistence, clustering, and advanced features like pub/sub.
* **Memcached** : Lightweight and very fast, best for simple key/value caching when persistence is not required.
* **In-memory cache** : Used by default if no backend is configured. Easiest to set up, but limited to a single process and **wipes entirely when the application restarts**, so best for development or small-scale setups.

#### Example configurations (Django)

```python
# settings.py

# Redis
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
    }
}

# Memcached
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.memcached.MemcachedCache",
        "LOCATION": "127.0.0.1:11211",
    }
}

# In-memory (local memory cache, default if none configured)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
    }
}
```

#### Example usage

```python
from django.core.cache import cache

# Store a value for 5 minutes
cache.set("greeting", "Hello, world!", timeout=300)

# Retrieve the value
message = cache.get("greeting")
print(message)  # "Hello, world!"
```

### Using Django Cache Without Configuring a Backend

Even if you don’t explicitly define a cache backend in `settings.py`, Django provides a **default in-memory cache (`LocMemCache`)** which the application uses by using the handlers `cache.get()` and `cache.set()` via a specifically designed cache functions:


Key points:

1. Django uses `LocMemCache` internally if `CACHES` is not defined.
2. If a in-memory cache is used (nothing added in the settings) when Django is restarted, the cache is automatically cleared by Django
3. Each worker process has its own separate cache.

---

In short: the app is **built to use caching by default**, but if no backend is configured it automatically falls back to an in-memory cache. However, because it is an in-memory when the Django sever restarts it **resets the cache**. For production, a persistent backend like Redis is recommended.




## Using and setting up Django-q

### What is Django-Q?

**Django-Q** is a task queue and asynchronous job manager for Django. It allows your application to run tasks **outside the normal request/response cycle**, this is useful for background processing, scheduling, or parallel execution.

### Key features include:

* Asynchronous Task Execution

Allows tasks to run in the background so users don’t have to wait for them to complete, for example:

* Sending emails
* Generating reports
* Processing files
* Performing API requests
* Deleting tasks

### Scheduled Tasks

Supports scheduling tasks similar to cron jobs:

* One-off tasks at a specific time
* Recurring tasks (daily, weekly, etc.)

### Multiple Brokers

Tasks can be stored in different backends (brokers):

* **Django ORM (default)**: stored in the database
* **Redis**: faster and suitable for high-performance needs
* Other databases (PostgreSQL, MySQL)

### Cluster Mode

Runs multiple worker processes in parallel for better performance and scalability.

### Result Storage

Stores task results so you can check completion status and retrieve outputs.

---

To run the worker cluster, use:

```bash
python manage.py qcluster
```

---

## Django-Q vs Celery and why Django Auth Recovery codes use Django-q


Both Django-Q and Celery are task queues, but they differ in complexity and use cases:

| Feature                   | Django-Q | Celery   |
| ------------------------- | -------- | -------- |
| Async tasks               | ✅        | ✅        |
| Scheduled tasks           | ✅        | ✅        |
| Periodic/recurring tasks  | ✅        | ✅        |
| Multiple brokers          | ✅        | ✅        |
| Result backend            | ✅        | ✅        |
| Retry/failure handling    | Basic    | Advanced |
| Task chaining & workflows | Limited  | ✅        |


**Key differences**:

* **Django-Q** is simpler, uses Django’s ORM as a broker by default, and is ideal for small to medium projects.
* **Celery** is more complex, requires an external broker like Redis or RabbitMQ, and is better suited for large-scale, high-load projects with advanced workflows.

---

## Why this application uses Django-Q

`django-2fa-recovery-codes` uses Django-Q to handle background tasks such as:

1. When the user email themselves a copy of their plaintext code
2. When the admin runs or sets up scheduler (once, daily, weekly, etc) to delete invalid or expired codes, a report is also generated and sent to the admin via email 


Without using Django-q whenever a user deletes their code or sends a copy of their plaintext code it will block normal request/response, and if multiple users are deleting their codes at the same time it can causes problems in the database by. With this it ensures that these tasks do not block normal request/response cycles and can run efficiently in the background without impacting the user experience.


---

### ⚠️ Note on Batch Deletion

Even though expired codes are deleted asynchronously, deleting **millions of codes at once** can still cause performance issues such as long transactions or database locks.

To avoid this, `django-2fa-recovery-codes` supports **batch deletion** via the configurable setting:

```python
# settings.py
Django Auth Recovery Codes_BATCH_DELETE_SIZE = 1000
```

* If set, expired codes will be deleted in **chunks of this size** (e.g. 1000 at a time).
* If not set, all expired codes are deleted in a single query.

---


### Using Django-Q with `django-2fa-recovery-codes`

Django Auth Recovery Codes provides a utility task to clean up expired recovery codes, but since this is a reusable app, the scheduling of this task is **left up to you**, depending on your project’s needs and dataset size.

---

####. Scheduling the Task with Django-Q via the admin interface `Recovery code batch scheduler`

You can schedule this cleanup task to run at whatever time that that suits via the admin. For example every date at a given time.

See the [Django-Q scheduling docs](https://django-q.readthedocs.io/en/latest/schedules.html) for more options.

---

---

### How does Django-Q delete codes if the user deletes them from the frontend?

`django-2fa-recovery-codes` does **not** immediately delete a code when the user deletes it from the frontend. Instead, it performs a **soft delete**, the code is marked as invalid and can no longer be used. From the user’s perspective, the code is “gone,” but the actual row still exists in the database until the cleanup task runs.

When the Django-Q scheduler task runs (either automatically or triggered by the admin), any codes marked for deletion are permanently removed in the background (in batches).

---

### Why not delete the code immediately?

Since this is a **reusable app** that can be plugged into Django projects of any size (small apps or large-scale environments), immediate deletion is avoided for two key reasons:

1. **Database contention**
   In environments with thousands of users, many codes could be deleted at the same time. Deleting them synchronously could lock rows or put heavy strain on the database.

2. **User experience**
   Immediate deletion happens in the request/response cycle. If many users delete codes at once, their requests would take longer, and the frontend might “freeze” while deletions are processed leading to a poor UX.

---

### Benefits of using Django-Q

By offloading deletion to Django-Q:

* Deletion is handled as a **background task**, so it doesn’t block the frontend.
* The database can process deletions more efficiently, especially when using **batch deletion**.
* Users get a smoother experience ,the code disappears instantly from their view, while the actual cleanup happens safely in the background.


### Deletion flow

<p align="center">
  <img src="/docs/images/deletion_flowchart.png" alt="Code deletion flowchart" width="500"/>
</p>
---

### Batch deletion configuration

For projects with very large datasets, batch deletion can be enabled via the `Django Auth Recovery Codes_BATCH_DELETE_SIZE` setting:

```python
# settings.py
Django Auth Recovery Codes_BATCH_DELETE_SIZE = 1000
```

* If set, expired or soft-deleted codes will be removed in chunks of this size.
* If not set, all deletions happen in a single query.

This approach provides flexibility,  small apps can use one-shot deletes, while larger systems can safely handle deletions in manageable batches.

---


## Setting up Django-Q

The `django-2fa-recovery-codes` library uses **Django-Q** internally. You don’t need to install it separately, but you must configure it in your Django project to ensure background tasks run properly.

---

### 1. Add Django-Q to Installed Apps

In your `settings.py`:

```python
INSTALLED_APPS = [
    ...
    'django_q',
]
```

---

### 2. Configure the Q\_CLUSTER

Example configuration:

```python
Q_CLUSTER = {
    'name': 'recovery_codes',
    'workers': 2,
    'timeout': 300,    # Maximum time (seconds) a task can run
    'retry': 600,      # Retry after 10 minutes if a task fails (retry must be greater than timeout)
    'recycle': 500,    # Recycle workers after this many tasks
    'compress': True,  # Compress data for storage
    'cpu_affinity': 1, # Assign workers to CPU cores
    'save_limit': 250, # Maximum number of task results to store
    'queue_limit': 500,# Maximum number of tasks in the queue
    'orm': 'default',  # Use the default database for task storage
}
```

For more configuration options, see the [official Django-Q documentation](https://django-q.readthedocs.io/en/latest/configure.html).

---

### 3. Running the Cluster

Don’t forget to start the Django-Q worker cluster so scheduled tasks actually run:

```bash
python manage.py qcluster
```

---

# Django Auth Recovery Settings

These environment variables configure the **Django Auth Recovery** system, controlling email notifications, audit logs, recovery code display, rate limiting, cooldowns, and code management.

---

### **📌 Cheat Sheet: Variable Categories**

| Icon | Category                  | Jump to Section                                        |
| ---- | ------------------------- | ------------------------------------------------------ |
| 📧   | Email & Admin Settings    | [Email & Admin Settings](#email--admin-settings)       |
| 📝   | Audit & Logging           | [Audit & Logging](#audit--logging)                     |
| 📄   | Code Display & Pagination | [Code Display & Pagination](#code-display--pagination) |
| ⚡    | Rate Limiting & Caching   | [Rate Limiting & Caching](#rate-limiting--caching)     |
| ⏱    | Cooldown Settings         | [Cooldown Settings](#cooldown-settings)                |
| 🗂   | Code Management & Limits  | [Code Management & Limits](#code-management--limits)   |

> Quick visual roadmap to jump to any section in the README.

---

### **🔍 Alphabetical Reference (Easy Copy & Paste)**

```
DJANGO_AUTH_RECOVERY_CODE_ADMIN_EMAIL=
DJANGO_AUTH_RECOVERY_CODE_ADMIN_EMAIL_HOST_USER=
DJANGO_AUTH_RECOVERY_CODE_ADMIN_USERNAME=
DJANGO_AUTH_RECOVERY_CODE_AUDIT_ENABLE_AUTO_CLEANUP=
DJANGO_AUTH_RECOVERY_CODE_AUDIT_RETENTION_DAYS=
DJANGO_AUTH_RECOVERY_CODE_MAX_VISIBLE=
DJANGO_AUTH_RECOVERY_CODE_PER_PAGE=
DJANGO_AUTH_RECOVERY_CODE_PURGE_DELETE_RETENTION_DAYS=
DJANGO_AUTH_RECOVERY_CODE_PURGE_DELETE_SCHEDULER_USE_LOGGER=
DJANGO_AUTH_RECOVERY_CODE_REDIRECT_VIEW=
DJANGO_AUTH_RECOVERY_CODE_STORE_EMAIL_LOG=
DJANGO_AUTH_RECOVERY_CODES_AUTH_RATE_LIMITER_USE_CACHE=
DJANGO_AUTH_RECOVERY_CODES_BASE_COOLDOWN=
DJANGO_AUTH_RECOVERY_CODES_BATCH_DELETE_SIZE=
DJANGO_AUTH_RECOVERY_CODES_CACHE_MAX=
DJANGO_AUTH_RECOVERY_CODES_CACHE_MIN=
DJANGO_AUTH_RECOVERY_CODES_CACHE_TTL=
DJANGO_AUTH_RECOVERY_CODES_COOLDOWN_CUTOFF_POINT=
DJANGO_AUTH_RECOVERY_CODES_COOLDOWN_MULTIPLIER=
DJANGO_AUTH_RECOVERY_CODES_DEFAULT_FILE_NAME=
DJANGO_AUTH_RECOVERY_CODES_DEFAULT_FORMAT=
DJANGO_AUTH_RECOVERY_CODES_MAX_LOGIN_ATTEMPTS=
DJANGO_AUTH_RECOVERY_KEY=
```

> Developers can **copy and paste** directly into a `.env` file or environment configuration.

---


### **🔍 Alphabetical Reference with defaults variables (Easy Copy & Paste) any thing not added is required **

```

DJANGO_AUTH_RECOVERY_CODE_AUDIT_ENABLE_AUTO_CLEANUP=True
DJANGO_AUTH_RECOVERY_CODE_AUDIT_RETENTION_DAYS=30
DJANGO_AUTH_RECOVERY_CODE_MAX_VISIBLE=20
DJANGO_AUTH_RECOVERY_CODE_PER_PAGE=5
DJANGO_AUTH_RECOVERY_CODE_PURGE_DELETE_RETENTION_DAYS=30
DJANGO_AUTH_RECOVERY_CODE_PURGE_DELETE_SCHEDULER_USE_LOGGER=True
DJANGO_AUTH_RECOVERY_CODE_REDIRECT_VIEW=recovery_dashboard
DJANGO_AUTH_RECOVERY_CODES_AUTH_RATE_LIMITER_USE_CACHE=True
DJANGO_AUTH_RECOVERY_CODES_BASE_COOLDOWN=2
DJANGO_AUTH_RECOVERY_CODES_BATCH_DELETE_SIZE=400
DJANGO_AUTH_RECOVERY_CODES_CACHE_MAX=3600
DJANGO_AUTH_RECOVERY_CODES_CACHE_MIN=0
DJANGO_AUTH_RECOVERY_CODES_CACHE_TTL=3600
DJANGO_AUTH_RECOVERY_CODES_COOLDOWN_CUTOFF_POINT=3600
DJANGO_AUTH_RECOVERY_CODES_COOLDOWN_MULTIPLIER=2
DJANGO_AUTH_RECOVERY_CODES_DEFAULT_FILE_NAME=recovery_codes
DJANGO_AUTH_RECOVERY_CODES_DEFAULT_FORMAT=txt
DJANGO_AUTH_RECOVERY_CODES_MAX_LOGIN_ATTEMPTS=5
```

> Developers can **copy and paste** directly into a `.env` file or environment configuration.


## Email & Admin Settings

| Variable                                          | Description                                     |
| ------------------------------------------------- | ----------------------------------------------- |
| `DJANGO_AUTH_RECOVERY_CODE_ADMIN_EMAIL`           | Email address used for sending recovery codes.  |
| `DJANGO_AUTH_RECOVERY_CODE_ADMIN_EMAIL_HOST_USER` | Host email account for sending recovery emails. |
| `DJANGO_AUTH_RECOVERY_CODE_ADMIN_USERNAME`        | Username associated with the admin account.     |

---

## Audit & Logging

| Variable                                                      | Description                                 |
| ------------------------------------------------------------- | ------------------------------------------- |
| `DJANGO_AUTH_RECOVERY_CODE_AUDIT_ENABLE_AUTO_CLEANUP`         | Enable automatic cleanup of audit logs.     |
| `DJANGO_AUTH_RECOVERY_CODE_AUDIT_RETENTION_DAYS`              | Number of days to retain audit logs.        |
| `DJANGO_AUTH_RECOVERY_CODE_PURGE_DELETE_SCHEDULER_USE_LOGGER` | Log scheduler operations during code purge. |
| `DJANGO_AUTH_RECOVERY_CODE_STORE_EMAIL_LOG`                   | Record activity of sent recovery emails.    |

---

## Code Display & Pagination


| Variable                                  | Description                                          |
| ----------------------------------------- | ---------------------------------------------------- |
| `DJANGO_AUTH_RECOVERY_CODE_MAX_VISIBLE`   | Maximum number of expired batches including the current active batch a user can view in their history section      |
| `DJANGO_AUTH_RECOVERY_CODE_PER_PAGE`      | Number of recovery codes per page (pagination).      |
| `DJANGO_AUTH_RECOVERY_CODE_REDIRECT_VIEW` | View users are redirected to after recovery actions. |

### Additional explanation for `DJANGO_AUTH_RECOVERY_CODE_MAX_VISIBILE` flag

The history section shows up to `DJANGO_AUTH_RECOVERY_CODE_MAX_VISIBLE` recovery code batches, regardless of how many exist in the database. For example, if a user has 100 codes but `DJANGO_AUTH_RECOVERY_CODE_MAX_VISIBLE`= 20, only 20 batches will appear (with pagination). To see what a single batch card contails [for what a batch contains see here](#example-a-single-recovery-code-batch-view).




---

## Rate Limiting & Caching

| Variable                                                 | Description                                         |
| -------------------------------------------------------- | --------------------------------------------------- |
| `DJANGO_AUTH_RECOVERY_CODES_AUTH_RATE_LIMITER_USE_CACHE` | Enable caching for rate limiting recovery attempts. |
| `DJANGO_AUTH_RECOVERY_CODES_CACHE_MAX`                   | Maximum cache value for rate limiter.               |
| `DJANGO_AUTH_RECOVERY_CODES_CACHE_MIN`                   | Minimum cache value for rate limiter.               |
| `DJANGO_AUTH_RECOVERY_CODES_CACHE_TTL`                   | Cache expiration time (seconds).                    |

---

## Cooldown Settings

| Variable                                           | Description                                          |
| -------------------------------------------------- | ---------------------------------------------------- |
| `DJANGO_AUTH_RECOVERY_CODES_BASE_COOLDOWN`         | Base interval for recovery code cooldown.            |
| `DJANGO_AUTH_RECOVERY_CODES_COOLDOWN_CUTOFF_POINT` | Maximum cooldown threshold.                          |
| `DJANGO_AUTH_RECOVERY_CODES_COOLDOWN_MULTIPLIER`   | Multiplier applied to cooldown on repeated attempts. |

---

## Code Management & Limits

| Variable                                                | Description                                                                   |
| ------------------------------------------------------- | ----------------------------------------------------------------------------- |
| `DJANGO_AUTH_RECOVERY_CODE_PURGE_DELETE_RETENTION_DAYS` | Number of days before expired recovery codes are deleted.                     |
| `DJANGO_AUTH_RECOVERY_CODES_BATCH_DELETE_SIZE`          | Number of codes to delete in a batch operation.                               |
| `DJANGO_AUTH_RECOVERY_CODES_DEFAULT_FILE_NAME`          | Default filename for exported recovery codes.                                 |
| `DJANGO_AUTH_RECOVERY_CODES_DEFAULT_FORMAT`             | Default export format for recovery codes. Options: `'txt'`, `'csv'`, `'pdf'`. |
| `DJANGO_AUTH_RECOVERY_CODES_MAX_LOGIN_ATTEMPTS`         | Maximum allowed login attempts with recovery codes.                           |
| `DJANGO_AUTH_RECOVERY_KEY`                              | Secret key used for recovery code validation.                                 |

---

## Example Usage

### .env file

```env
DJANGO_AUTH_RECOVERY_CODE_ADMIN_EMAIL=admin@example.com
DJANGO_AUTH_RECOVERY_CODE_ADMIN_EMAIL_HOST_USER=smtp@example.com
DJANGO_AUTH_RECOVERY_CODE_ADMIN_USERNAME=admin
DJANGO_AUTH_RECOVERY_CODE_AUDIT_ENABLE_AUTO_CLEANUP=True
DJANGO_AUTH_RECOVERY_CODE_AUDIT_RETENTION_DAYS=30
DJANGO_AUTH_RECOVERY_CODE_MAX_VISIBLE=20
DJANGO_AUTH_RECOVERY_CODE_PER_PAGE=10
DJANGO_AUTH_RECOVERY_CODE_PURGE_DELETE_RETENTION_DAYS=90
DJANGO_AUTH_RECOVERY_CODE_REDIRECT_VIEW=recovery_dashboard
DJANGO_AUTH_RECOVERY_CODES_AUTH_RATE_LIMITER_USE_CACHE=True
DJANGO_AUTH_RECOVERY_CODES_CACHE_TTL=3600
DJANGO_AUTH_RECOVERY_CODES_BASE_COOLDOWN=60
DJANGO_AUTH_RECOVERY_CODES_DEFAULT_FORMAT=txt
DJANGO_AUTH_RECOVERY_KEY=supersecretkey
```

### settings.py

```python
import os

ADMIN_EMAIL = os.getenv("DJANGO_AUTH_RECOVERY_CODE_ADMIN_EMAIL")
ADMIN_USERNAME = os.getenv("DJANGO_AUTH_RECOVERY_CODE_ADMIN_USERNAME")
AUDIT_RETENTION_DAYS = int(os.getenv("DJANGO_AUTH_RECOVERY_CODE_AUDIT_RETENTION_DAYS", 30))
MAX_VISIBLE = int(os.getenv("DJANGO_AUTH_RECOVERY_CODE_MAX_VISIBLE", 20))
COOLDOWN_BASE = int(os.getenv("DJANGO_AUTH_RECOVERY_CODES_BASE_COOLDOWN", 60))
EXPORT_FORMAT = os.getenv("DJANGO_AUTH_RECOVERY_CODES_DEFAULT_FORMAT", "txt")
SECRET_KEY = os.getenv("DJANGO_AUTH_RECOVERY_KEY")
```

---

## Best Practices for Managing Environment Variables

1. **Use a `.env` file for local development**  Keep secret keys and credentials out of source control.

---

## Default Values & Required Variables

| Variable                                                      | Required | Default Value        | Notes                                                                            |
| ------------------------------------------------------------- | -------- | -------------------- | -------------------------------------------------------------------------------- |
| `DJANGO_AUTH_RECOVERY_CODE_ADMIN_EMAIL`                       | ✅ Yes    | –                    | Email used to send recovery codes. Must be valid.                                |
| `DJANGO_AUTH_RECOVERY_CODE_ADMIN_EMAIL_HOST_USER`             | ✅ Yes    | –                    | SMTP or host email account. Required for sending emails.                         |
| `DJANGO_AUTH_RECOVERY_CODE_ADMIN_USERNAME`                    | ✅ Yes    | –                    | Admin username associated with the email.                                        |
| `DJANGO_AUTH_RECOVERY_CODE_AUDIT_ENABLE_AUTO_CLEANUP`         | ❌ No     | `False`              | Automatically clean up audit logs if True.                                       |
| `DJANGO_AUTH_RECOVERY_CODE_AUDIT_RETENTION_DAYS`              | ❌ No     | `30`                 | Number of days to retain audit logs.                                             |
| `DJANGO_AUTH_RECOVERY_CODE_MAX_VISIBLE`                       | ❌ No     | `20`                  | Maximum number of expired batches plus the current active batch the user can view under their history section                                       |
| `DJANGO_AUTH_RECOVERY_CODE_PER_PAGE`                          | ❌ No     | `10`                 | Pagination setting for code lists.                                               |
| `DJANGO_AUTH_RECOVERY_CODE_PURGE_DELETE_RETENTION_DAYS`       | ❌ No     | `90`                 | Days before expired codes are deleted.                                           |
| `DJANGO_AUTH_RECOVERY_CODE_PURGE_DELETE_SCHEDULER_USE_LOGGER` | ❌ No     | `False`              | Enable scheduler logging for purge operations.                                   |
| `DJANGO_AUTH_RECOVERY_CODE_REDIRECT_VIEW`                     | ❌ No     | `/`                  | URL to redirect users after code actions.                                        |
| `DJANGO_AUTH_RECOVERY_CODE_STORE_EMAIL_LOG`                   | ❌ No     | `False`              | Log sent recovery emails.                                                        |
| `DJANGO_AUTH_RECOVERY_CODES_AUTH_RATE_LIMITER_USE_CACHE`      | ❌ No     | `True`               | Use cache for rate limiting.                                                     |
| `DJANGO_AUTH_RECOVERY_CODES_BASE_COOLDOWN`                    | ❌ No     | `60`                 | Base cooldown interval in seconds.                                               |
| `DJANGO_AUTH_RECOVERY_CODES_BATCH_DELETE_SIZE`                | ❌ No     | `50`                 | Number of codes deleted per batch.                                               |
| `DJANGO_AUTH_RECOVERY_CODES_CACHE_MAX`                        | ❌ No     | `1000`               | Maximum value for cache-based limiter.                                           |
| `DJANGO_AUTH_RECOVERY_CODES_CACHE_MIN`                        | ❌ No     | `0`                  | Minimum value for cache-based limiter.                                           |
| `DJANGO_AUTH_RECOVERY_CODES_CACHE_TTL`                        | ❌ No     | `3600`               | Cache expiration in seconds.                                                     |
| `DJANGO_AUTH_RECOVERY_CODES_COOLDOWN_CUTOFF_POINT`            | ❌ No     | `3600`               | Maximum cooldown threshold in seconds.                                           |
| `DJANGO_AUTH_RECOVERY_CODES_COOLDOWN_MULTIPLIER`              | ❌ No     | `2`                  | Multiplier for repeated attempts cooldown.                                       |
| `DJANGO_AUTH_RECOVERY_CODES_DEFAULT_FILE_NAME`                | ❌ No     | `recovery_codes` | Default file name for exported codes.                                            |
| `DJANGO_AUTH_RECOVERY_CODES_DEFAULT_FORMAT`                   | ❌ No     | `txt`                | Default format for exporting recovery codes. Options: `'txt'`, `'csv'`, `'pdf'`. |
| `DJANGO_AUTH_RECOVERY_CODES_MAX_LOGIN_ATTEMPTS`               | ❌ No     |   `5` | Maximum login attempts using recovery codes. |
| `DJANGO_AUTH_RECOVERY_KEY` | ✅ Yes | – | Secret key for recovery code validation. Must be kept safe. |

---



```markdown
To ensure that all configurations and flags are correct, run the following command before starting the application:
```

```python
python manage.py check
```

This command will raise an error if any configuration is incorrect.

If everything is fine, you can then run the server and the task queue:

```python
# Terminal 1
python manage.py runserver

# Terminal 2
python manage.py qcluster
```


## Sending Emails and Logging

Django Auth 2FA Recovery provides the ability to email yourself a copy of your raw recovery codes and can only be done once for a given batch, and only if you haven't logged out after generating the code. This is achieved using a lightweight yet powerful library called **`EmailSender`**, which is responsible for delivering the message.

In addition to sending, the process can be logged for developers through a companion model named **`EmailSenderLogger`**. Together, these ensure that not only are emails dispatched, but the details of each operation can also be recorded for auditing, debugging, or monitoring purposes. 

The application uses **SSE (Server-Sent Events)** to notify the user when an email has been sent.

### What is SSE?

SSE is a way for a **server to push real-time updates to a client** over HTTP. Unlike WebSockets, which allow **two-way communication**, SSE is **one-way**: the server sends messages to the client, but the client cannot send messages back over the same connection.

It’s commonly used for:

* Live notifications
* Stock tickers
* Chat message feeds
* Real-time monitoring dashboards

In this application, SSE is used for live notifications when an email is sent.

### Why is the app is using SSE?

The app uses SSE because emails are sent asynchronously using **Django-Q**. This ensures that sending an email does not block the request/response cycle which simply means the user's screen doesn't lock while the email is sending. Emails are placed in a task queue and may be sent immediately or after a short delay, depending on the queue load.

Without SSE, the user would have to constantly check their email inbox to know if the codes have been sent. With SSE, the user can continue using the app normally and receive a notification popup **as soon as the email is processed and sent**, providing a better real-time experience.


### Using async vs synchronous

The application supports both **asynchronous** and **synchronous** email sending for development and production.

In production, emails are sent **asynchronously** via **Django-Q**, which places the email in a task queue. Depending on the queue load, this may take a few seconds or minutes to process.

In development, you might want to send emails **synchronously** to see the results immediately and verify that everything is working correctly.

This behaviour is controlled by the `DEBUG` setting:

* When `DEBUG = True`, emails are sent **synchronously**.
* When `DEBUG = False`, emails are sent **asynchronously** via Django-Q.

This setup allows developers to test email functionality quickly in development but at the same time keep production efficient and non-blocking.


### Configuration

Whether emails are logged is determined by a configuration flag in your project’s `settings.py`.

```python
# settings.py

# Enable or disable logging of sent emails
DJANGO_AUTH_RECOVERY_CODES_EMAIL_SENDER_LOGGING = True  # Logs the email process
DJANGO_AUTH_RECOVERY_CODES_EMAIL_SENDER_LOGGING = False  # Disables logging
```

* **`True`**: The application records details of the email process via `EmailSenderLogger`.
* **`False`**: No logging takes place.


## Hang on a minute, why can I email myself the code only once, and only if I haven’t logged out after generating it?

The way **Django Auth Recovery Code** works is that it never stores the plain text recovery codes in the database. Instead, it stores only their **hash values**.  

A **hash** is a one-way function: it takes an input, applies a hashing algorithm, and produces an output that cannot be reversed to recover the original input. This is different from encryption/decryption, where data can be restored to its original form. Hashing is therefore safer for storing sensitive values such as recovery codes.  

### What does this mean for your codes?  

Since the generated codes are stored as hashes, the system cannot send you the hash (as it is meaningless to you) and it cannot retrieve the original plain text version (because it was never stored in the database).  

To work around this, the application temporarily stores a copy of the plain text codes in your **backend session** when they are first generated. This session is unique to your login and user account. Because it is session-based, the codes are removed once you log out.  

### What happens if I refresh the page, can I still email myself the code?  

Yes. Refreshing the page does not clear the backend session. However, for security reasons, the plain text codes will no longer be displayed in the frontend after the initial page load. As long as you remain logged in, you can still email yourself a copy of the codes.  

### But if I’m still logged in, why can I only email myself a single copy?  

This is a deliberate **security measure**. Allowing multiple emails of the same batch would unnecessarily increase the risk of exposure. Limiting it to a single email ensures you have one secure copy without duplicating it across your inbox.  

### Can I email myself a copy if I generate a new batch?  

Yes. Generating a new batch creates a new set of plain text codes, which are again stored in your backend session. You may therefore email yourself one copy of each new batch.  

---

## Using Logging with the Application  

`django-2fa-recovery-codes` includes a built-in logging configuration, so you do not need to create your own in `settings.py`. This reduces the risk of misconfiguration.  

Because the application uses `django-q` (an asynchronous task manager), the logger is already set up to work with it. Conveniently, everything is preconfigured for you. All you need to do is import the logging configuration and assign it to Django’s `LOGGING` variable.  

```python
# settings.py

from django_auth_recovery_codes.loggers.logger_config import DJANGO_AUTH_RECOVERY_CODES_LOGGING

LOGGING = DJANGO_AUTH_RECOVERY_CODES_LOGGING
```

The `LOGGING` variable is the standard Django setting for logging. Assigning the provided configuration ensures that log files are correctly created and stored in a dedicated folder.

---

## What if I don’t want to override my existing LOGGING configuration?

If you already have a logging configuration and prefer not to overwrite it, you can simply **merge** it with `DJANGO_AUTH_RECOVERY_CODES_LOGGING`. Since logging configurations are dictionaries, merging them is straightforward:

```python
# settings.py

LOGGING = {**LOGGING, **DJANGO_AUTH_RECOVERY_CODES_LOGGING}
```

This approach allows you to keep your existing logging settings intact but still allow you to add support for `django-2fa-recovery-codes`.


---

## Downloading Recovery Codes  

In addition to emailing your recovery codes, `django-2fa-recovery-codes` also allows you to **download them directly**. This gives you flexibility in how you choose to back up your codes.  

### How downloads work  

When recovery codes are generated, a plain text copy is stored temporarily in the `request.session`. This enables you to either:  

- **Email yourself a copy**, or  
- **Download a copy** in one of the following formats:  
  - Plain text (`.txt`)  
  - PDF (`.pdf`)  
  - CSV (`.csv`)  


The format in which the recovery codes are returned (TXT, PDF, or CSV) is determined by a settings flag. By default, the codes are returned as **TXT**, but this can be customised using the following setting:

```python
# Default download format
DJANGO_AUTH_RECOVERY_CODES_DEFAULT_FORMAT = 'txt'  # options: 'txt', 'csv', 'pdf'
```

By default, the downloaded file is named `recovery_codes` (plus the extension) used when using the default format. You can also change the file name using this setting:

```python
# Default download file name
DJANGO_AUTH_RECOVERY_CODES_DEFAULT_FILE_NAME = "recovery_codes"

```


Just like with emailing, once you log out, the session is cleared and the plain text codes are no longer available.  

### Important security notes  

- You may **only download a copy once** per batch of recovery codes.  
- The downloaded file contains the **exact same content** as the emailed version (the plain text recovery codes).  
- If you lose the downloaded file after logging out, you will not be able to retrieve it. You will need to generate a new batch of recovery codes.  

### Example usage  

When generating recovery codes in the application, you will be presented with options to:  

- **Email yourself a copy** (retrieves codes from `request.session`)  
- **Download a copy** (also retrieves codes from `request.session`)  

Both options use the same temporary storage mechanism, which ensures your plain text recovery codes are only ever available for the current session and cannot be recovered after logout.  

---







## Contributing



---

## License



---

