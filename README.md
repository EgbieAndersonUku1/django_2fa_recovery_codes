![Made with Python](https://img.shields.io/badge/Made%20with-Python-blue?logo=python)
![Security](https://img.shields.io/badge/Security-180--bit-brightgreen)
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
  * DJANGO_AUTH_RECOVERY_CODES_DEFAULT_FILE_NAME                 
  * DJANGO_AUTH_RECOVERY_KEY                                    
  * DJANGO_AUTH_RECOVERY_CODE_AUDIT_RETENTION_DAYS                
  * DJANGO_AUTH_RECOVERY_CODE_AUDIT_ENABLE_AUTO_CLEANUP         
  * DJANGO_AUTH_RECOVERY_CODE_PURGE_DELETE_RETENTION_DAYS        
  * DJANGO_AUTH_RECOVERY_CODE_ADMIN_EMAIL_HOST_USER               
  * DJANGO_AUTH_RECOVERY_CODE_ADMIN_EMAIL                         
  * DJANGO_AUTH_RECOVERY_CODE_ADMIN_USERNAME                      
  * DJANGO_AUTH_RECOVERY_CODE_PURGE_DELETE_SCHEDULER_USE_LOGGER  
  * DJANGO_AUTH_RECOVERY_CODE_STORE_EMAIL_LOG                     
  * DJANGO_AUTH_RECOVERY_CODE_REDIRECT_VIEW                       
  * DJANGO_AUTH_RECOVERY_CODE_MAX_VISIBLE                         
  * DJANGO_AUTH_RECOVERY_CODE_PER_PAGE                           
  * DJANGO_AUTH_RECOVERY_CODES_MAX_LOGIN_ATTEMPTS                
  * DJANGO_AUTH_RECOVERY_CODES_AUTH_RATE_LIMITER_USE_CACHE        
  * DJANGO_AUTH_RECOVERY_CODES_CACHE_TTL                         
  * DJANGO_AUTH_RECOVERY_CODES_CACHE_MIN                         
  * DJANGO_AUTH_RECOVERY_CODES_CACHE_MAX                        
```


## 2FA Recovery Code Generator

This app generates **2FA recovery codes** that can be used if you lose access to your authenticator app.

Each code is generated using **cryptographically secure randomness** and avoids confusing characters (e.g., `0` vs `O`, `1` vs `l`).

### Code Format

Codes are generated in the following format:

```
XXXXXX-XXXXXX-XXXXXX-XXXXXX-XXXXXX-XXXXXX
```
---
* **6 groups**, each with **6 characters**
* **Alphabet size:** 60 characters (`A–Z`, `a–z`, `2–9`)
* **Cryptographic randomness** (not guessable, not sequential)
* **Entropy total:** 213 bits (≈5.91 bits per character × 36 characters)

---

### Why It’s Secure

#### Entropy

* Each character contributes **≈5.91 bits** (`log2(60) ≈ 5.91`) where the 60 is (`A–Z`, `a–z`, `2–9`)
* Each group has 6 characters → 6 × 5.91 ≈ **35.46 bits per group**
* 6 groups → 6 × 35.46 ≈ **212.8 bits total**

> With 60 characters and 36-character codes, entropy is significantly higher than AES-128 (128 bits), making brute-force attacks astronomically impractical.

#### Total Combinations

* **Number of unique codes:**

$$
60^{36} \approx 2.03 \times 10^{63}
$$

> This astronomical number of possible codes ensures that guessing a valid code is virtually impossible.


#### What this means?

* Each character is chosen randomly from 60 possibilities.
* With 36 characters, the number of possible codes is **more than 2 followed by 63 zeros**.
* That’s **so many possibilities** that even the fastest computers would take **longer than the age of the universe** to try them all.
* This makes guessing a valid code virtually impossible and this is without brute rate limiter.

> In short: it’s **far stronger than standard encryption like AES-128**. You can trust these codes to be safe.


---

#### Brute-Force Resistance

Assuming a supercomputer that tests **10^9 codes per second** with no rate limiting:

* **Seconds to brute-force:**

$$
3.3 \times 10^{61} ÷ 10^9 ≈ 3.3 × 10^{52} \text{ seconds}
$$

* **Convert to years:**

$$
≈ 1.05 × 10^{45} \text{ years}
$$

> Even a supercomputer cannot realistically brute-force a single code.

#### Time to Crack at Different Speeds

| Guesses per Second | Time to Crack (Years) |
| ------------------ | --------------------- |
| 1                  | 3.3 × 10^61           |
| 10^6 (1 million)   | 3.3 × 10^55           |
| 10^9 (1 billion)   | 1.05 × 10^45          |
| 10^18 (exascale)   | 1.05 × 10^36          |

* Age of the universe: ≈ 13.8 × 10^9 years
* Brute-force time: trillions of times longer than the universe's age

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

### Set up the Cache or using default cache

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

# Ensure cache TTL stays within safe bounds do not change this only modify the above flags
DJANGO_AUTH_RECOVERY_CODES_CACHE_TTL = max(
    DJANGO_AUTH_RECOVERY_CODES_CACHE_MIN,
    min(DJANGO_AUTH_RECOVERY_CODES_CACHE_TTL, DJANGO_AUTH_RECOVERY_CODES_CACHE_MAX)
)
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

`Django Auth Recovery Codes` uses Django-Q to handle background tasks such as:

1. When the user email themselves a copy of their plaintext code
2. When the admin runs or sets up scheduler (once, daily, weekly, etc) to delete invalid or expired codes, a report is also generated and sent to the admin via email 


Without using Django-q whenever a user deletes their code or sends a copy of their plaintext code it will block normal request/response, and if multiple users are deleting their codes at the same time it can causes problems in the database by. With this it ensures that these tasks do not block normal request/response cycles and can run efficiently in the background without impacting the user experience.


---

### ⚠️ Note on Batch Deletion

Even though expired codes are deleted asynchronously, deleting **millions of codes at once** can still cause performance issues such as long transactions or database locks.

To avoid this, `Django Auth Recovery Codes` supports **batch deletion** via the configurable setting:

```python
# settings.py
Django Auth Recovery Codes_BATCH_DELETE_SIZE = 1000
```

* If set, expired codes will be deleted in **chunks of this size** (e.g. 1000 at a time).
* If not set, all expired codes are deleted in a single query.

---


### Using Django-Q with `Django Auth Recovery Codes`

Django Auth Recovery Codes provides a utility task to clean up expired recovery codes, but since this is a reusable app, the scheduling of this task is **left up to you**, depending on your project’s needs and dataset size.

---

####. Scheduling the Task with Django-Q via the admin interface `Recovery code batch scheduler`

You can schedule this cleanup task to run at whatever time that that suits via the admin. For example every date at a given time.

See the [Django-Q scheduling docs](https://django-q.readthedocs.io/en/latest/schedules.html) for more options.

---

---

### How does Django-Q delete codes if the user deletes them from the frontend?

`Django Auth Recovery Codes` does **not** immediately delete a code when the user deletes it from the frontend. Instead, it performs a **soft delete**, the code is marked as invalid and can no longer be used. From the user’s perspective, the code is “gone,” but the actual row still exists in the database until the cleanup task runs.

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
  <img src="docs/images/deletion_flowchart.png" alt="Code deletion flowchart" width="500"/>
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

The `Django Auth Recovery Codes` library uses **Django-Q** internally. You don’t need to install it separately, but you must configure it in your Django project to ensure background tasks run properly.

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








## Contributing



---

## License



---

