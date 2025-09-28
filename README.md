![Made with Python](https://img.shields.io/badge/Made%20with-Python-blue?logo=python)
![Security](https://img.shields.io/badge/Security-213--bit-brightgreen)
![Brute Force](https://img.shields.io/badge/Brute--force-Impractical-red)
![License](https://img.shields.io/badge/License-MIT-yellow)


## 🔐 Django 2FA Recovery Codes

The premises of this resuable application, is that it takes any Django application and extends that application so that it can now use the 2FA recovery codes as a backup login should you lose access.

`django-2fa-recovery-codes` is a Django app that provides a robust system for generating, storing, and managing **2FA recovery codes**. Unlike a full two-factor authentication apps, this package focuses solely on **recovery codes**, although this is a lightweight application it is a very powerful tool, offering fine-grained control and asynchronous management for better UX and performance.

## Table of Contents
* [Requirements & Key Technologies](#requirements--key-technologies)
* [Key Features](#key-features)
* [How it Differs From A Full Two-Factor Authentication Apps](#how-it-differs-from-a-full-two-factor-authentication-apps)
  * [User Interface](#user-ui-interface)
  * [Asynchronous usage](#asynchronous-usage)
  * [Admin interface](#admin-interface)
  * [Flag configuration](#flag-configuration)
  * [Caching](#caching)
  * [Email and Logging capabilities](#email-and-logging-capabilities)
  * [Rate limiter](#rate-limiter)
  * [Code generation attribrutes](#code-generation-attribrutes)
    * [Cleanup Configuration Examples](#cleanup-configuration-examples)
    * [Large app (millions of codes)](#large-app-millions-of-codes)
    * [Cleanup Process Visualised](#cleanup-process-visualised)
    * [Recommended Settings by Scale](#recommended-settings-by-scale)
    * [How Cleanup Works Internally](#how-cleanup-works-internally)
    * [FAQ Frequently Asked Questions](#faq--frequently-asked-questions)
  * [Configurable flags for developer](#configurable-flags-for-developer)
* [2FA Recovery Code Generator](#django-2fa-recovery-code-generator)
  * [Security overview](#security-overview)
  * [Entropy](#entropy)
  * [Total Combinations](#total-combinations)
  * [Brute-Force Resistance](#brute-force-resistance)
  * [Perspective](#prespective)
  * [Developer Appendix 🛠️](#developer-appendix)
  * [Summary](#summary)
  * [Use Cases](#use-cases)
* [Installation](#installation)
* [Quick Example](#quick-example) 
* [How to Use 2FA Recovery Codes](#how-to-use-2fa-recovery-codes)
  * [Setting up the Cache or using the default cache](#setting-up-the-cache-or-using-the-default-cache)
  * [How does the cache work?](#how-does-the-cache-work)
  * [Using Pagination and Caching](#using-pagination-and-caching)
  * [What cache should I use?](#what-cache-should-i-use)
  * [Using Django Cache Without Configuring a Backend](#using-django-cache-without-configuring-a-backend)
  * [Django-Q vs Celery and why Django Auth Recovery codes use Django-q](#django-q-vs-celery-and-why-django-auth-recovery-codes-use-django-q)
  * [Why this application uses Django-Q](#why-this-application-uses-django-q)
  * [Using Django-Q with `django-2fa-recovery-codes`](#using-django-q-with-django-2fa-recovery-codes)
  * [Benefits of using Django-Q](#benefits-of-using-django-q)
  * [Setting up Django-q](#setting-up-django-q)
* [Django Auth Recovery Settings](#django-auth-recovery-settings)  
* [Using and setting up Django-q](#using-and-setting-up-django-q)
* [Django Auth Recovery flag settings](#django-auth-recovery-flag-settings)
  * [Alphabetical Reference (Easy Copy & Paste)](#alphabetical-reference-easy-copy--paste)
  * [Alphabetical Reference with defaults variables (Easy Copy & Paste) any thing not added is required](#alphabetical-reference-with-defaults-variables-easy-copy--paste-any-thing-not-added-is-required)
  * [Recovery Code Display Settings](#recovery-code-display-settings)
  * [Cooldown Settings Flags](#cooldown-settings-flags)
  * [Rate Limiting & Caching](#rate-limiting--caching)
  * [Audit & Logging Setting Flags](#audit--logging-setting-flags)
  * [Email & Admin Settings Flags](#email--admin-settings-flags)
  * [Code Management & Limits](#code-management--limits)
  * [Site Settings Flags](#site-settings-flags)
  * [Example Flag Usage](#example-flag-usage)
  * [Best Practices for Managing Environment Variables](#best-practices-for-managing-environment-variables)
  * [Default Values & Required Variables](#default-values--required-variables)
  * [Run checks to verify that flags are valid](#run-checks-to-verify-that-flags-are-valid)
* [Sending Emails and using Logging](#sending-emails-and-using-logging)
  * [What is SSE?](#what-is-sse)
  * [Why is the app is using SSE?](#why-is-the-app-is-using-sse)
  * [Using async vs synchronous](#using-async-vs-synchronous)
  * [Configuration settings](#configuration-settings)
  * [Hang on a minute, why can I email myself the code only once, and only if I haven’t logged out after generating it?](#hang-on-a-minute-why-can-i-email-myself-the-code-only-once-and-only-if-i-havent-logged-out-after-generating-it)
  * [What does this mean for your codes?](#what-does-this-mean-for-your-codes)
  * [What happens if I refresh the page, can I still email myself the code?](#what-happens-if-i-refresh-the-page-can-i-still-email-myself-the-code)
  * [But if I’m still logged in, why can I only email myself a single copy?](#but-if-im-still-logged-in-why-can-i-only-email-myself-a-single-copy)
  * [Can I email myself a copy if I generate a new batch?](#can-i-email-myself-a-copy-if-i-generate-a-new-batch)
* [Using Logging with the Application](#using-logging-with-the-application)
  * [What if I don’t want to override my existing LOGGING configuration?](#what-if-i-dont-want-to-override-my-existing-logging-configuration)
* [Downloading Recovery Codes](#downloading-recovery-codes)
  * [How downloads work](#how-downloads-work)
  * [Important security notes](#important-security-notes)
  * [Example usage](#example-usage)
* [Quickstart and Walkthrough](#quickstart-and-walkthrough)
  * [Setup](#setup)
  * [Installation (with Virtual Environment)](#installation-with-virtual-environment)
  * [3. Upgrade pip (optional but recommended)](#3-upgrade-pip-optional-but-recommended)
  * [4. Install Django (latest version)](#4-install-django-latest-version)
  * [5. Install the recovery codes package](#5-install-the-recovery-codes-package)
  * [6. Verify installation](#6-verify-installation)
  * [8. Run initial migrations](#8-run-initial-migrations)
  * [9. Create a Django superuser](#9-create-a-django-superuser)
  * [10. Start a new app called `home`](#10-start-a-new-app-called-home)
  * [12. Run the development server](#12-run-the-development-server)
  * [Configure URLs](#configure-urls)
  * [Configure your Settings.py file](#configure-your-settingspy-file)
  * [16. Set up the file-based email backend (for testing)](#16-set-up-the-file-based-email-backend-for-testing)
  * [17. Run the system checks](#17-run-the-system-checks)
  * [17a. Generate a recovery code](#17a-generate-a-recovery-code)
  * [Run Services](#run-services)
  * [Create a Home View](#create-a-home-view)
  * [Access the Admin](#access-the-admin)
  * [Access the Recovery Codes page dashboard](#access-the-recovery-codes-page-dashboard)
  * [Code Generation](#code-generation)
  * [Verifying Generated Codes](#verifying-generated-codes)
  * [Downloaded and Emailed Code](#downloaded-and-emailed-code)
  * [Invalidating or Deleting a Code](#invalidating-or-deleting-a-code)
  * [Viewing the Code Batch History](#viewing-the-code-batch-history)
  * [Logout of the application](#logout-of-the-application)
  * [Failed Attempts and Rate Limiting](#failed-attempts-and-rate-limiting)
  * [Successful Login](#successful-login)
  * [Existing Project Setup](#2-existing-project-setup)
  * [Scheduling a Code Removal Using Django-Q](#scheduling-a-code-removal-using-django-q)
* [Contributing](#contributing)
* [License](#license)
* [Support](#support)


---

## Requirements & Key Technologies

- **Python 3.10+**  
  This library uses [Structural Pattern Matching](https://docs.python.org/3/whatsnew/3.10.html#structural-pattern-matching), introduced in Python 3.10, via the `match`-`case` syntax.

- **Django 5.2+**  
  The project is built and tested using Django 5.2, which has Long-Term Support (LTS).  
  Using an earlier version, such as Django 4.1.x, may work in some cases but is **not guaranteed** and could potentially break the application, since it has only been tested with Django 5.2.

### Why Python 3.10?

The project relies on the `match`-`case` syntax, which provides a more readable and expressive way to handle complex conditional logic.

## Key Technologies and Libraries Used

- **EmailSender**: a lightweight but powerful library for sending chainable rich emails with templates. [Find out more](https://github.com/EgbieAndersonUku1/django-email-sender)
- **EmailSenderLogger**: a lightweight but powerful library for logging, emails sent by EmailSender. [Find out more](https://github.com/EgbieAndersonUku1/django-email-sender)
- **Django-q**: an asynchronous task manager used for processing background tasks, including using EmailSender to send emails.  
- **JavaScript (JS)**: for interactivity and fetch requests.  
- **HTML**: for structuring content.  
- **CSS**: for styling the user interface.

---

---


### Key Features

* Generate recovery codes in configurable batches.
* Track recovery codes individually:

  * Mark codes as used, inactive, or scheduled for deletion.
  * User the 2FA code to login which becomes invalid after a single use

* Batch management:

  * Track issued and removed codes per batch.
  * Statuses for active, invalidated, or deleted batches.

* Login
  
  * Login in using your 2FA Recovery Backup code

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

* ### User UI interface
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
* Built-in **logger configuration** which can be imported into settings or merged with an existing logger.

* ### Asynchronous Usage

  * Built with **asynchronous usage** using Django-Q:
  * Automatically deletes expired or invalid codes when uses with scheduler.
  * On a successful delete scheduler generates an audit report of the number of deleted codes and sends it to admin via email. The sending of the email is optional.
  * Email sending can be configured to run **asynchronous or synchronous** depending on your environment:
    * `DEBUG = True` : uses synchronous sending (easy for development or testing).  
    * `DEBUG = False` : uses asynchronous sending (recommended for production; doesn’t block the application while sending in the background).

* ### Admin interface
  * **Admin-friendly view interface code management**, including the ability to scheduler deletion for expired or invalid codes e.g (every 2 days, etc) or even the audit history.
* ### Code tracking
  * **Individual code tracking** with granular control over each code.
* ### Flag configuration
  * Optional configuration to  turn **logger** on or off to track the actions of users generating recovery codes, email sent, various aspect of the models, etc.
  * Optional **storage of user email** in the model for auditing purposes.
* ### Caching
  * Utilises **caching** (Redis, Memcached, default cache, etc) for
    * Pagination and page reads
    * Brute-force rate limiting
    * Other database-heavy operations
    * Reduces database hits until cache expires or updates are made.

* ### Email and logging capabilities
  * **Email sending capabilities** via `EmailSender` library.
  * **Email logging** via `EmailSenderLogger` library.

* ### Rate limiter
  * **Maximum login attempt control** with a brute-force rate limiter:  
    * Configurable penalty wait times that increase if a user retries during the wait window.
  * **Brute-force rate limiter** for code generation:
    * Prevents spam and imposes a penalty if the user attempts regeneration too soon.

* ### Code generation attribrutes
  * Generate **codes that expire** or have no expiry.
  * Allow users to **download or email codes** (one per batch).
  * **Invalidate, delete a single code or an entire batch** easily.
  * Users can **view batch details**, e.g., number of codes generated, emailed, or downloaded.

* ### Configurable flags for developer

     #### Configuration flags settings for the Django Auth Recovery code app

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
      * DJANGO_AUTH_RECOVERY_CODE_REDIRECT_VIEW_AFTER_LOGOUT
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
      * DJANGO_AUTH_RECOVERY_CODES_SITE_NAME
      * DJANGO_AUTH_RECOVERY_CODES_MAX_DELETIONS_PER_RUN              
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

### Prespective?

### What this means?

* Each character is chosen randomly from 60 possibilities.
* With 36 characters, the number of possible codes is **more than 2 followed by 63 zeros**.
* Each recovery code has **≈213 bits of entropy**, making it **extremely resistant to guessing or brute-force attacks**.
* That’s **so many possibilities** that even the fastest computers would take **longer than the age of the universe** to try them all.
* The vast number of possible codes ensures that **every code is unique and unpredictable**.
* This makes guessing a valid code virtually impossible and this is without brute rate limiter, with a rate limiter (which this app uses it is virtually impossible).

> In short: it’s **far stronger than standard encryption like AES-128**. 

<div align="center">
  <img src="django_auth_recovery_codes/docs/images/security-strength.png" alt="2FA login form" width="400">
</div>

> You can trust these recovery codes to keep your account safe even against attackers with enormous computational power.



---

### Developer Appendix

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

#### Summary

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


### Using Pagination and Caching

The application uses a **TTL cache** for paginated data. Without caching, every page refresh or navigation triggers a database query to fetch the relevant objects, which can be inefficient.

With the TTL cache (how long an data is cached is determined by the setting flags, default five minutes):

* Paginated query results (e.g., a history of recovery codes) are stored in memory for a set duration.
* While the cache is valid, page refreshes or navigation read from the cache instead of hitting the database.
* When underlying data changes, for example, a new batch of codes is generated, the database and the cache is updated, and the newly updated data from the cache is used. This ensures  that subsequent requests are up-to-date.


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

### How does Django-Q delete codes if the user deletes them from the frontend

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

<div align="center">

  <img src="django_auth_recovery_codes/docs/images/deletion_flowchart.png" alt="Code deletion flowchart" width="300">

</div>
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

For more configuration options, see the [official Django-Q documentation](https://django-q.readthedocs.io/en/latest/configure.html)

---

### 3. Running the Cluster

Don’t forget to start the Django-Q worker cluster so scheduled tasks actually run:

```bash
python manage.py qcluster
```

---

## Django Auth Recovery flag settings 

These environment variables configure the **Django Auth Recovery** system, controlling email notifications, audit logs, recovery code display, rate limiting, cooldowns, and code management.

---
### **📌 Cheat Sheet: Variable Categories**

| Icon | Category                  | Jump to Section                                        |
| ---- | ------------------------- | ------------------------------------------------------ |
| 📧   | Email & Admin Settings    | [Email & Admin Settings Flags](#email--admin-settings-flags)       |
| 📝   | Audit & Logging           | [Audit & Logging Setting Flags](#audit--logging-setting-flags)     |
| 📄   | Code Display & Pagination | [Recovery Code Display Settings](#recovery-code-display-settings) |
| ⚡    | Rate Limiting & Caching   | [Rate Limiting & Caching](#rate-limiting--caching)                   |
| ⏱    | Cooldown Settings         | [Cooldown Settings Flags](#cooldown-settings-flags)                  |
| 🗂   | Code Management & Limits  | [Code Management & Limits](#code-management--limits)                 |

> Quick visual roadmap to jump to any section in the README.

---

### **Alphabetical Reference (Easy Copy & Paste)**

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
DJANGO_AUTH_RECOVERY_CODE_REDIRECT_VIEW_AFTER_LOGOUT=
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
DJANGO_AUTH_RECOVERY_CODES_SITE_NAME=
DJANGO_AUTH_RECOVERY_CODES_MAX_DELETIONS_PER_RUN=

```

> Developers can **copy and paste** the flags directly into a `settings.py` file.
<br>
**Note**

Do not place the flags in the `.env` file if their values are not strings. This is because `.env` files cast all values to strings, which is fine for flags that are already strings. However, if a value is meant to be an int, it will raise an error because the system checks expect an integer.

Additionally, there is no need to place these values in an `.env` file since they are not sensitive. Only place sensitive information e.ge `DJANGO_AUTH_RECOVERY_KEY`



### **Alphabetical Reference with defaults variables (Easy Copy & Paste) any thing not added is required **

```

DJANGO_AUTH_RECOVERY_CODE_AUDIT_ENABLE_AUTO_CLEANUP=True
DJANGO_AUTH_RECOVERY_CODE_AUDIT_RETENTION_DAYS=30
DJANGO_AUTH_RECOVERY_CODE_MAX_VISIBLE=20
DJANGO_AUTH_RECOVERY_CODE_PER_PAGE=5
DJANGO_AUTH_RECOVERY_CODE_PURGE_DELETE_RETENTION_DAYS=30
DJANGO_AUTH_RECOVERY_CODE_PURGE_DELETE_SCHEDULER_USE_LOGGER=True
DJANGO_AUTH_RECOVERY_CODE_REDIRECT_VIEW_AFTER_LOGOUT=recovery_dashboard
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
DJANGO_AUTH_RECOVERY_CODES_SITE_NAME="2FA Recovery site"
DJANGO_AUTH_RECOVERY_CODES_MAX_DELETIONS_PER_RUN=0
```

> Developers can **copy and paste** directly into their `settings.py` file.


## Email & Admin Settings Flags

These settings control which email and admin accounts are used for recovery code notifications and scheduled operations.

| Variable                                          | Description                                                                 |
| ------------------------------------------------- | --------------------------------------------------------------------------- |
| `DJANGO_AUTH_RECOVERY_CODE_ADMIN_EMAIL`           | Admin email address used to receive generated reports after scheduled code deletions. |
| `DJANGO_AUTH_RECOVERY_CODE_ADMIN_EMAIL_HOST_USER` | The email address used by the application to send emails, typically the same as `EMAIL_HOST_USER` in your Django settings. |
| `DJANGO_AUTH_RECOVERY_CODE_ADMIN_USERNAME`        | Username associated with the admin account.                                  |

### Example Usage

Suppose the settings are:

- `DJANGO_AUTH_RECOVERY_CODE_ADMIN_EMAIL = admin@example.com`  
- `DJANGO_AUTH_RECOVERY_CODE_ADMIN_EMAIL_HOST_USER = noreply@example.com`  
- `DJANGO_AUTH_RECOVERY_CODE_ADMIN_USERNAME = admin`  

Then the system will:

1. Send generated reports of scheduled recovery code deletions to `admin@example.com`.  
2. Use `noreply@example.com` as the sender for all automated recovery code emails.  
3. Associate actions with the admin username for auditing purposes.


---

## Audit & Logging Setting Flags

These settings control the auditing, logging, and retention of recovery code activity to ensure traceability and compliance.

| Variable                                                      | Description                                 |
| ------------------------------------------------------------- | ------------------------------------------- |
| `DJANGO_AUTH_RECOVERY_CODE_AUDIT_ENABLE_AUTO_CLEANUP`         | Enable automatic cleanup of audit logs.     |
| `DJANGO_AUTH_RECOVERY_CODE_AUDIT_RETENTION_DAYS`              | Number of days to retain audit logs.        |
| `DJANGO_AUTH_RECOVERY_CODE_PURGE_DELETE_SCHEDULER_USE_LOGGER` | Log scheduler operations during code purge. |
| `DJANGO_AUTH_RECOVERY_CODE_STORE_EMAIL_LOG`                   | Record activity of sent recovery emails.    |

### Example Usage

Suppose the settings are:

- `DJANGO_AUTH_RECOVERY_CODE_AUDIT_ENABLE_AUTO_CLEANUP = True`  
- `DJANGO_AUTH_RECOVERY_CODE_AUDIT_RETENTION_DAYS = 90`  
- `DJANGO_AUTH_RECOVERY_CODE_PURGE_DELETE_SCHEDULER_USE_LOGGER = True`  
- `DJANGO_AUTH_RECOVERY_CODE_STORE_EMAIL_LOG = True`  

Then the system will:

1. Automatically remove audit logs older than 90 days.  
2. Record all recovery email activity in the logs.  
3. Log any operations performed by the purge scheduler for transparency.  

These flags help maintain a clean audit trail while ensuring important recovery-related actions are tracked.

---



## Recovery Code Display Settings

These settings control how recovery code batches are displayed in the user interface, including pagination and post-action redirection.

| Variable                                  | Description                                                                 |
| ----------------------------------------- | --------------------------------------------------------------------------- |
| `DJANGO_AUTH_RECOVERY_CODE_MAX_VISIBLE`   | Maximum number of expired batches, including the current active batch, that a user can view in their history section. |
| `DJANGO_AUTH_RECOVERY_CODE_PER_PAGE`      | Number of recovery codes per page (pagination).                             |
| `DJANGO_AUTH_RECOVERY_CODE_REDIRECT_VIEW_AFTER_LOGOUT` | View users are redirected to after recovery actions.                        |

### Additional Explanation for `DJANGO_AUTH_RECOVERY_CODE_MAX_VISIBLE`

This setting controls how many recovery code batches are displayed to the user, regardless of the total number stored in the database. Each batch contains multiple recovery codes.

#### Example

Suppose the settings are:

- `DJANGO_AUTH_RECOVERY_CODE_MAX_VISIBLE = 20`  
- `DJANGO_AUTH_RECOVERY_CODE_PER_PAGE = 5`  

Then:

1. If a user has 100 recovery codes, only 20 batches will be shown in the interface.  
2. With 5 batches per page, there will be 4 pages of recovery codes.  
3. Users can navigate through these pages to see all visible batches.  

For details on what a single batch includes, see [example: a single recovery code batch view](#example-a-single-recovery-code-batch-view).


---


## Rate Limiting & Caching

These settings control rate limiting for recovery code requests and how caching is used to improve performance and prevent abuse.  

| Variable                                                 | Description                                         |
| -------------------------------------------------------- | --------------------------------------------------- |
| `DJANGO_AUTH_RECOVERY_CODES_AUTH_RATE_LIMITER_USE_CACHE` | Enable caching for rate limiting recovery attempts. |
| `DJANGO_AUTH_RECOVERY_CODES_CACHE_MAX`                   | Maximum cache value for rate limiter.               |
| `DJANGO_AUTH_RECOVERY_CODES_CACHE_MIN`                   | Minimum cache value for rate limiter.               |
| `DJANGO_AUTH_RECOVERY_CODES_CACHE_TTL`                   | Cache expiration time (seconds).                    |

### Example

Suppose the settings are:

- `DJANGO_AUTH_RECOVERY_CODES_AUTH_RATE_LIMITER_USE_CACHE = True`  
- `DJANGO_AUTH_RECOVERY_CODES_CACHE_MIN = 1`  
- `DJANGO_AUTH_RECOVERY_CODES_CACHE_MAX = 5`  
- `DJANGO_AUTH_RECOVERY_CODES_CACHE_TTL = 60`  

Then the system will:

1. Start counting recovery attempts from `CACHE_MIN = 1`.  
2. Increment the cached count with each recovery request, up to `CACHE_MAX = 5`.  
3. Reset the count automatically after `CACHE_TTL = 60` seconds.  
4. Use the cache to enforce rate limiting, preventing abuse and reducing database load.


## Cooldown Settings Flags

These settings control the cooldown period applied when users request recovery codes repeatedly. The cooldown helps prevent abuse by increasing the wait time between requests.

| Variable                                           | Description                                          |
| -------------------------------------------------- | ---------------------------------------------------- |
| `DJANGO_AUTH_RECOVERY_CODES_BASE_COOLDOWN`         | Base interval for recovery code cooldown (seconds). |
| `DJANGO_AUTH_RECOVERY_CODES_COOLDOWN_CUTOFF_POINT`| Maximum cooldown threshold (seconds).               |
| `DJANGO_AUTH_RECOVERY_CODES_COOLDOWN_MULTIPLIER`  | Multiplier applied to cooldown on repeated attempts.|

### Example

Suppose the settings are:

- `DJANGO_AUTH_RECOVERY_CODES_BASE_COOLDOWN = 30`  
- `DJANGO_AUTH_RECOVERY_CODES_COOLDOWN_MULTIPLIER = 2`  
- `DJANGO_AUTH_RECOVERY_CODES_COOLDOWN_CUTOFF_POINT = 300`  

Then the cooldown progression for repeated recovery code requests would be:

1. First attempt: 30 seconds  
2. Second attempt: 30 × 2 = 60 seconds  
3. Third attempt: 60 × 2 = 120 seconds  
4. Fourth attempt: 120 × 2 = 240 seconds  
5. Fifth attempt: 240 × 2 = 480 seconds → capped at 300 seconds (cutoff)  

This ensures the cooldown grows exponentially but never exceeds the defined maximum threshold.


---

## Code Management & Limits

These settings control how recovery codes are managed, including deletion, export, usage limits, and validation.

| Variable                                                       | Description                                                                 |
| -------------------------------------------------------------- | --------------------------------------------------------------------------- |
| `DJANGO_AUTH_RECOVERY_CODE_PURGE_DELETE_RETENTION_DAYS`        | Number of days before expired recovery codes are deleted.                    |
| `DJANGO_AUTH_RECOVERY_CODES_BATCH_DELETE_SIZE`                 | Number of codes to delete in a single batch operation.                       |
| `DJANGO_AUTH_RECOVERY_CODES_DEFAULT_FILE_NAME`                 | Default filename for exported recovery codes.                                |
| `DJANGO_AUTH_RECOVERY_CODES_DEFAULT_FORMAT`                    | Default export format for recovery codes. Options: `'txt'`, `'csv'`, `'pdf'`.|
| `DJANGO_AUTH_RECOVERY_CODES_MAX_LOGIN_ATTEMPTS`                | Maximum allowed login attempts using recovery codes.                         |
| `DJANGO_AUTH_RECOVERY_KEY`                                     | Secret key used for recovery code validation.                                |
| `DJANGO_AUTH_RECOVERY_CODES_PURGE_MAX_DELETIONS_PER_RUN`       | Maximum number of expired codes to delete in a single scheduler run.  If unset (`-1`), deletion is unlimited.  If set to `0`, no codes will be deleted (mainly for testing/debugging purposes). |




### Example Usage

Suppose the settings are:

- `DJANGO_AUTH_RECOVERY_CODE_PURGE_DELETE_RETENTION_DAYS = 90`  
- `DJANGO_AUTH_RECOVERY_CODES_BATCH_DELETE_SIZE = 50`  
- `DJANGO_AUTH_RECOVERY_CODES_DEFAULT_FILE_NAME = "recovery_codes"`  
- `DJANGO_AUTH_RECOVERY_CODES_DEFAULT_FORMAT = "txt"`  
- `DJANGO_AUTH_RECOVERY_CODES_MAX_LOGIN_ATTEMPTS = 5`  

Then the system will:

1. Delete expired recovery codes older than 90 days, in batches of 50.  
2. Export recovery codes using the default file name `recovery_codes` and format `txt`.  
3. Limit users to 5 login attempts using recovery codes before locking or enforcing cooldowns.  
4. Use `DJANGO_AUTH_RECOVERY_KEY` to validate recovery codes during login or verification.


### Cleanup Configuration Examples

The cleanup behaviour for expired recovery codes can be tuned using:

- `DJANGO_AUTH_RECOVERY_CODES_BATCH_DELETE_SIZE` → controls how many codes are deleted per database operation.
- `DJANGO_AUTH_RECOVERY_CODES_PURGE_MAX_DELETIONS_PER_RUN` → caps the maximum number of deletions in one scheduler run.

<br>

> **Note:** This setting works together with `DJANGO_AUTH_RECOVERY_CODES_BATCH_DELETE_SIZE`.  
> The scheduler will delete codes in batches until either the max deletions per run is reached or all expired codes are removed.  
> `None` means “delete everything in one run,” while an integer enforces a cap per run.

### Example setups

#### Small app / development
```env
DJANGO_AUTH_RECOVERY_CODES_BATCH_DELETE_SIZE=100
DJANGO_AUTH_RECOVERY_CODES_PURGE_MAX_DELETIONS_PER_RUN=
````

Deletes everything in one run, in small chunks of 100 to avoid heavy queries.

---

#### Medium app

```env
DJANGO_AUTH_RECOVERY_CODES_BATCH_DELETE_SIZE=500
DJANGO_AUTH_RECOVERY_CODES_PURGE_MAX_DELETIONS_PER_RUN=5000
```

Deletes up to 5,000 codes per scheduler run, in batches of 500.

---

#### Large app (millions of codes)

```env
DJANGO_AUTH_RECOVERY_CODES_BATCH_DELETE_SIZE=1000
DJANGO_AUTH_RECOVERY_CODES_PURGE_MAX_DELETIONS_PER_RUN=10000
```

Deletes up to 10,000 codes per run, in batches of 1,000. This spreads load across multiple scheduler runs while keeping each job predictable and efficient.



### Cleanup Process Visualised

The diagrams below illustrate how expired recovery codes are deleted.

### 1. Loop until finished
All expired codes are deleted in a single scheduler run, in batches.

```mermaid
flowchart TD
    A[Scheduler Run Starts] --> B{Expired codes exist?}
    B -->|Yes| C[Delete batch (size=N)]
    C --> D{Expired codes remain?}
    D -->|Yes| C
    D -->|No| E[Scheduler Run Ends]
    B -->|No| E
````

---

### 2. Hybrid: capped deletions per run

Deletes in batches, but stops once the maximum deletions per run is reached.
Remaining codes are cleaned in future runs.

```mermaid
flowchart TD
    A[Scheduler Run Starts] --> B{Expired codes exist?}
    B -->|Yes| C[Delete batch (size=N)]
    C --> D[Increase total deleted count]
    D --> E{Reached max deletions per run?}
    E -->|Yes| F[Stop, resume next run]
    E -->|No| G{Expired codes remain?}
    G -->|Yes| C
    G -->|No| H[Scheduler Run Ends]
    B -->|No| H
```


### Recommended Settings by Scale

| Scale        | `DJANGO_AUTH_RECOVERY_CODES_BATCH_DELETE_SIZE` | `DJANGO_AUTH_RECOVERY_CODES_PURGE_MAX_DELETIONS_PER_RUN` | Notes                                                                 |
|--------------|-----------------------------------------------|----------------------------------------------------------|-----------------------------------------------------------------------|
| Small (dev / hobby) | 100 | *-1* | Deletes all expired codes in one run, safe for small datasets. |
| Medium (tens of thousands) | 500 | 5000 | Balances DB load by capping deletions to 5k per scheduler run. |
| Large (millions) | 1000 | 10000 | Spreads cleanup across runs, keeps queries efficient and predictable. |

**Tip:** 

Always tune based on your database performance and scheduler frequency.  For example, if your scheduler runs every 5 minutes, lower values keep load smoother.  If it runs nightly, higher values may be better to catch up faster.

### How Cleanup Works Internally

When the scheduler runs, the app looks for expired or invalidated recovery codes and removes them according to your configuration.  

The process is:

1. **Batch deletion**  

   - Codes are deleted in small chunks (`DJANGO_AUTH_RECOVERY_CODES_BATCH_DELETE_SIZE`) instead of all at once.  
   - This prevents long-running SQL queries and reduces database locks.

2. **Optional cap per run**  

   - If you set `DJANGO_AUTH_RECOVERY_CODES_PURGE_MAX_DELETIONS_PER_RUN`, the scheduler will stop once that many codes have been deleted.  
   - Any remaining codes will be picked up in the next scheduler run.  
   - This spreads the load across multiple runs and avoids “big bang” deletes.
   - If the flag is set to None, it becomes unlimited meaning it will carry on looping until all codes are cleared

3. **Scheduler resumes automatically**  

   - On the next scheduled run, the same process repeats until all expired codes are gone.  
   - You don’t need to trigger anything manually.



✅ This design ensures a couple of things in regards to the cleanup is:

- **Safe** → avoids stressing the database.  
- **Scalable** → works for apps with thousands or millions of codes.  
- **Automatic** → no manual intervention needed.  


### FAQ — Frequently Asked Questions

### Q: What happens if the scheduler crashes during cleanup?  

A: The process is idempotent. If a run is interrupted, any remaining expired codes will be picked up on the next scheduled run.  
No data loss occurs beyond the intended deletions.

---

### Q: Can I disable automatic cleanup?  

A: Yes. Simply avoid scheduling the purge task in your task runner (e.g., Django-Q).  
You may then run `purge_expired_codes()` manually when required.  
This is useful for testing or environments with strict operational controls.

---

### Q: How do I know how many codes were deleted?  

A: Every purge operation is logged through `RecoveryCodeAudit` or inspect the email sent to admin after a schedule deletion has occurred.  
You can inspect these logs to see the number of codes deleted, who initiated the deletion, and the associated batch metadata.

---

### Q: Will cleanup affect active codes?  

A: No. Only codes that are expired or invalidated (based on retention days and status) are eligible for deletion.  
Valid codes remain untouched.

---

### Q: What if I have millions of expired codes?  

A: Configure both `DJANGO_AUTH_RECOVERY_CODES_BATCH_DELETE_SIZE` and  
`DJANGO_AUTH_RECOVERY_CODES_PURGE_MAX_DELETIONS_PER_RUN` appropriately.  
This ensures cleanup is spread across multiple runs, preventing excessive locking or transaction bloat.

---

### Q: Can I monitor cleanup performance?  

A: Yes, you can monitor through the Django-q admin interface.  
Because deletions are chunked, monitoring helps you fine-tune batch size and per-run caps for optimal efficiency.


---

## Site Settings Flags

| Variable                              | Description                                           |
| ------------------------------------- | ----------------------------------------------------- |
| `DJANGO_AUTH_RECOVERY_CODES_SITE_NAME`| The name of the site to use with the application .   |

### Example Usage

Suppose the setting is:

- `DJANGO_AUTH_RECOVERY_CODES_SITE_NAME = "My Awesome Site"`

Then recovery emails and notifications will display the site name "My Awesome Site" to the user, helping them identify the source of the email and also display on the site dashboard and login page.

--- 

## Example Flag Usage



```
DJANGO_AUTH_RECOVERY_CODE_ADMIN_EMAIL=admin@example.com
DJANGO_AUTH_RECOVERY_CODE_ADMIN_EMAIL_HOST_USER=smtp@example.com
DJANGO_AUTH_RECOVERY_CODE_ADMIN_USERNAME=admin
DJANGO_AUTH_RECOVERY_CODE_AUDIT_ENABLE_AUTO_CLEANUP=True
DJANGO_AUTH_RECOVERY_CODE_AUDIT_RETENTION_DAYS=30
DJANGO_AUTH_RECOVERY_CODE_MAX_VISIBLE=20
DJANGO_AUTH_RECOVERY_CODE_PER_PAGE=10
DJANGO_AUTH_RECOVERY_CODE_PURGE_DELETE_RETENTION_DAYS=90
DJANGO_AUTH_RECOVERY_CODE_REDIRECT_VIEW_AFTER_LOGOUT=recovery_dashboard
DJANGO_AUTH_RECOVERY_CODES_AUTH_RATE_LIMITER_USE_CACHE=True
DJANGO_AUTH_RECOVERY_CODES_CACHE_TTL=3600
DJANGO_AUTH_RECOVERY_CODES_BASE_COOLDOWN=60
DJANGO_AUTH_RECOVERY_CODES_DEFAULT_FORMAT=txt
DJANGO_AUTH_RECOVERY_KEY=supersecretkey
DJANGO_AUTH_RECOVERY_CODES_MAX_DELETIONS_PER_RUN=400
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
| `DJANGO_AUTH_RECOVERY_CODE_REDIRECT_VIEW_AFTER_LOGOUT`                     | ❌ No     | `/`                  | URL to redirect users after code actions.                                        |
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
| `DJANGO_AUTH_RECOVERY_CODES_PURGE_MAX_DELETIONS_PER_RUN`               | ❌ No     |   1000 | Caps the maximum number of deletions in one scheduler run. |
| `DJANGO_AUTH_RECOVERY_KEY` | ✅ Yes | – | Secret key for recovery code validation. Must be kept safe. |


---


## Run checks to verify that flags are valid

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


## Sending Emails and using Logging

Django Auth 2FA Recovery provides the ability to email yourself a copy of your raw recovery codes and can only be done once for a given batch, and only if you haven't logged out after generating the code. This is achieved using a lightweight yet powerful library called **`EmailSender`**, which is responsible for delivering the message.

In addition to sending, the process can be logged for developers through a companion model named **`EmailSenderLogger`**. Together, these ensure that not only are emails dispatched, but the details of each operation can also be recorded for auditing, debugging, or monitoring purposes. 

The application uses **SSE (Server-Sent Events)** to notify the user when an email has been sent.

### What is SSE?
---

SSE is a way for a **server to push real-time updates to a client** over HTTP. Unlike WebSockets, which allow **two-way communication**, SSE is **one-way**: the server sends messages to the client, but the client cannot send messages back over the same connection.

It’s commonly used for:

* Live notifications
* Stock tickers
* Chat message feeds
* Real-time monitoring dashboards

In this application, SSE is used for live notifications when an email is sent.

### Why is the app is using SSE?
---

The app uses SSE because emails are sent asynchronously using **Django-Q**. This ensures that sending an email does not block the request/response cycle which simply means the user's screen doesn't lock while the email is sending. Emails are placed in a task queue and may be sent immediately or after a short delay, depending on the queue load.

Without SSE, the user would have to constantly check their email inbox to know if the codes have been sent. With SSE, the user can continue using the app normally and receive a notification popup **as soon as the email is processed and sent**, providing a better real-time experience.


### Using async vs synchronous
---

The application supports both **asynchronous** and **synchronous** email sending for development and production.

In production, emails are sent **asynchronously** via **Django-Q**, which places the email in a task queue. Depending on the queue load, this may take a few seconds or minutes to process.

In development, you might want to send emails **synchronously** to see the results immediately and verify that everything is working correctly.

This behaviour is controlled by the `DEBUG` setting:

* When `DEBUG = True`, emails are sent **synchronously**.
* When `DEBUG = False`, emails are sent **asynchronously** via Django-Q.

This setup allows developers to test email functionality quickly in development but at the same time keep production efficient and non-blocking.


### Configuration settings
---

Whether emails are logged is determined by a configuration flag in your project’s `settings.py`.

```python
# settings.py

# Enable or disable logging of sent emails
DJANGO_AUTH_RECOVERY_CODES_EMAIL_SENDER_LOGGING = True  # Logs the email process
DJANGO_AUTH_RECOVERY_CODES_EMAIL_SENDER_LOGGING = False  # Disables logging
```

* **`True`**: The application records details of the email process via `EmailSenderLogger`.
* **`False`**: No logging takes place.


### Hang on a minute, why can I email myself the code only once, and only if I haven’t logged out after generating it?
---

The way **Django Auth Recovery Code** works is that it never stores the plain text recovery codes in the database. Instead, it stores only their **hash values**.  

A **hash** is a one-way function: it takes an input, applies a hashing algorithm, and produces an output that cannot be reversed to recover the original input. This is different from encryption/decryption, where data can be restored to its original form. Hashing is therefore safer for storing sensitive values such as recovery codes.  

### What does this mean for your codes?  
---

Since the generated codes are stored as hashes, the system cannot send you the hash (as it is meaningless to you) and it cannot retrieve the original plain text version (because it was never stored in the database).  

To work around this, the application temporarily stores a copy of the plain text codes in your **backend session** when they are first generated. This session is unique to your login and user account. Because it is session-based, the codes are removed once you log out.  

### What happens if I refresh the page, can I still email myself the code?  
---

Yes. Refreshing the page does not clear the backend session. However, for security reasons, the plain text codes will no longer be displayed in the frontend after the initial page load. As long as you remain logged in, you can still email yourself a copy of the codes.  

### But if I’m still logged in, why can I only email myself a single copy?  
---

This is a deliberate **security measure**. Allowing multiple emails of the same batch would unnecessarily increase the risk of exposure. Limiting it to a single email ensures you have one secure copy without duplicating it across your inbox.  

### Can I email myself a copy if I generate a new batch?  
---

Yes. Generating a new batch creates a new set of plain text codes, which are again stored in your backend session. You may therefore email yourself one copy of each new batch.  

---

### Using Logging with the Application  
---

`django-2fa-recovery-codes` includes a built-in logging configuration, so you do not need to create your own in `settings.py`. This reduces the risk of misconfiguration.  

Because the application uses `django-q` (an asynchronous task manager), the logger is already set up to work with it. Conveniently, everything is preconfigured for you. All you need to do is import the logging configuration and assign it to Django’s `LOGGING` variable.  

```python
# settings.py

from django_auth_recovery_codes.loggers.logger_config import DJANGO_AUTH_RECOVERY_CODES_LOGGING

LOGGING = DJANGO_AUTH_RECOVERY_CODES_LOGGING
```

The `LOGGING` variable is the standard Django setting for logging. Assigning the provided configuration ensures that log files are correctly created and stored in a dedicated folder.

---

### What if I don’t want to override my existing LOGGING configuration?
---

If you already have a logging configuration and prefer not to overwrite it, you can simply **merge** it with `DJANGO_AUTH_RECOVERY_CODES_LOGGING`. Since logging configurations are dictionaries, merging them is straightforward:

```python
# settings.py

LOGGING = {**LOGGING, **DJANGO_AUTH_RECOVERY_CODES_LOGGING}
```

This approach allows you to keep your existing logging settings intact but still allow you to add support for `django-2fa-recovery-codes`.


---

## Downloading Recovery Codes  
---

In addition to emailing your recovery codes, `django-2fa-recovery-codes` also allows you to **download them directly**. This gives you flexibility in how you choose to back up your codes.  

### How downloads work  
---

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
---

- You may **only download a copy once** per batch of recovery codes.  
- The downloaded file contains the **exact same content** as the emailed version (the plain text recovery codes).  
- If you lose the downloaded file after logging out, you will not be able to retrieve it. You will need to generate a new batch of recovery codes.  

### Example usage  

When generating recovery codes in the application, you will be presented with options to:  

- **Email yourself a copy** (retrieves codes from `request.session`)  
- **Download a copy** (also retrieves codes from `request.session`)  

Both options use the same temporary storage mechanism, which ensures your plain text recovery codes are only ever available for the current session and cannot be recovered after logout.  

---


## Quickstart and Walkthrough

### Setup
---

This guide shows you how to set up a fresh Django project and integrate **2FA Recovery Codes** using the `django_auth_recovery_codes` package.  

The walkthrough assumes you don’t already have a Django project, which is why we create a new one called `test_project`.  

If you already have an existing Django project, skip to Existing project :

- then follow the steps in this guide that apply to integration (skipping project creation).

---

### Installation (with Virtual Environment)

### 1. Create a virtual environment

```bash
python -m venv env
````

* `env` is the folder name for your virtual environment. You can name it anything.

### 2. Activate the virtual environment

* **Windows (PowerShell)**

  ```powershell
  .\env\Scripts\Activate.ps1
  ```
* **Windows (CMD)**

  ```cmd
  .\env\Scripts\activate.bat
  ```
* **macOS/Linux**

  ```bash
  source env/bin/activate
  ```

### 3. Upgrade pip (optional but recommended)

```bash
pip install --upgrade pip
```

### 4. Install Django (latest version)

```bash
pip install django
```

### 5. Install the recovery codes package

```bash
pip install django_auth_recovery_codes
```

### 6. Verify installation

```bash
python -m django --version
pip show django_auth_recovery_codes
```

---

## Project Setup

### 7. Create a new Django project

```bash
django-admin startproject test_project
cd test_project
```

### 8. Run initial migrations

```bash
python manage.py migrate
```

### 9. Create a Django superuser

```bash
python manage.py createsuperuser
```

* Follow the prompts to set username, email, and password.

### 10. Start a new app called `home`

```bash
python manage.py startapp home
```

### 11. Add `home`, `django_auth_recovery_codes`, and `django_q` to `INSTALLED_APPS`

Edit `test_project/settings.py`:

```python
INSTALLED_APPS = [
    ...,

    # third-party apps
    "django_auth_recovery_codes",
    "django_q",

    # your app
    "home",
]
```


### 12. Run the development server

```bash
python manage.py runserver
```

Open [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin) and log in with your superuser credentials.

---

## Configure URLs

### 13. In `home/urls.py`

Create the file if it doesn’t exist:

```python
from django.urls import path
from . import views

urlpatterns = [
    path("", view=views.home, name="home"),
]
```

### 14. In your **main** `urls.py` (same folder as `settings.py`)

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("django_auth_recovery_codes.urls")),  # recovery codes
    path("", include("home.urls")),  # home app
]
```

---

### Configure your Settings.py file

### 15. Add the recovery code settings flags in your `settings.py` file

```python

# Required values, customise for your project
DJANGO_AUTH_RECOVERY_CODE_ADMIN_EMAIL = "your-email-address"
DJANGO_AUTH_RECOVERY_CODE_ADMIN_EMAIL_HOST_USER = "main-smtp-email"
DJANGO_AUTH_RECOVERY_CODE_ADMIN_USERNAME = "username"
DJANGO_AUTH_RECOVERY_KEY = "add-some-key"
DJANGO_AUTH_RECOVERY_CODES_SITE_NAME="some site name"


# Default values (can be left as-is or overridden)
DJANGO_AUTH_RECOVERY_CODE_AUDIT_ENABLE_AUTO_CLEANUP = 30
DJANGO_AUTH_RECOVERY_CODE_AUDIT_RETENTION_DAYS = 30
DJANGO_AUTH_RECOVERY_CODE_MAX_VISIBLE = 20
DJANGO_AUTH_RECOVERY_CODE_PER_PAGE = 5
DJANGO_AUTH_RECOVERY_CODE_PURGE_DELETE_RETENTION_DAYS = 30
DJANGO_AUTH_RECOVERY_CODE_PURGE_DELETE_SCHEDULER_USE_LOGGER = True
DJANGO_AUTH_RECOVERY_CODE_REDIRECT_VIEW_AFTER_LOGOUT = "login_user"
DJANGO_AUTH_RECOVERY_CODE_STORE_EMAIL_LOG = True
DJANGO_AUTH_RECOVERY_CODES_AUTH_RATE_LIMITER_USE_CACHE = True
DJANGO_AUTH_RECOVERY_CODES_BASE_COOLDOWN = 3600
DJANGO_AUTH_RECOVERY_CODES_BATCH_DELETE_SIZE = 1000
DJANGO_AUTH_RECOVERY_CODES_CACHE_MAX = 3600
DJANGO_AUTH_RECOVERY_CODES_CACHE_MIN = 0
DJANGO_AUTH_RECOVERY_CODES_CACHE_TTL = 300
DJANGO_AUTH_RECOVERY_CODES_COOLDOWN_CUTOFF_POINT = 3600
DJANGO_AUTH_RECOVERY_CODES_COOLDOWN_MULTIPLIER = 2
DJANGO_AUTH_RECOVERY_CODES_DEFAULT_FILE_NAME = "recovery_codes"
DJANGO_AUTH_RECOVERY_CODES_DEFAULT_FORMAT = "txt"
DJANGO_AUTH_RECOVERY_CODES_MAX_LOGIN_ATTEMPTS = 3
DJANGO_AUTH_RECOVERY_CODES_MAX_DELETIONS_PER_RUN = -1
```

### Add a Q_CLUSTER 
See ![documentation for more details](https://deepwiki.com/django-q2/django-q2/5-configuration-options)

For now we use the default

```


Q_CLUSTER = {
    'name': 'recovery_codes',
    'workers': 2,
    'timeout': 300,   # 5 minutes max per task
    'retry': 600,     # retry after 10 minutes if task fails (retry must be greater than timeout)
    'recycle': 500,
    'compress': True,
    'cpu_affinity': 1,
    'save_limit': 250,
    'queue_limit': 500,
    'orm': 'default',
}

```


### 16.Set up the file-based email backend (for testing)

This will create a `sent_emails` folder where Django saves emails instead of sending them.

```python
EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
EMAIL_FILE_PATH = BASE_DIR / "sent_emails"
```

### 17. Run the system checks

Stop the server (`Ctrl+C`) if it’s running, then run:

```bash
python manage.py check
```

This will raise errors if any settings are misconfigured (e.g., wrong data types).

---

### 17a. Generate a recovery code 

Run the follwoing command, make sure your virtual environment is active.
This will drop you into shell but load all app modules

```python

python manage.py shell

```
Next run

```python

from django_auth_recovery_codes.utils.security.generator  import generate_secure_token

# This will generate a secure cryptographically key which can use for your recovery key in the settings flag
# code_length = 10, default this will generate a secret key that is 100 characters, adjust length as you see fit
generate_secure_token(code_length=10)

```

Copy the key into your recovery key

```
DJANGO_AUTH_RECOVERY_KEY = 

```



### Run Services

### 18. Open two terminals

**Terminal 1** – run the server:

```bash
python manage.py runserver
```

**Terminal 2** – run django-q cluster:

```bash
python manage.py qcluster
```

---
### Create a Home View

#### 19. In `home/views.py`

```python
from django.http import HttpResponse

def home(request):
    return HttpResponse("This is the home page")
```

---

### Verify the Home Page

Open your browser and go to:

```
http://127.0.0.1:8000/
```

You should see:
*"This is the home page"*

---

markdown
### Access the Admin

Since we don’t have a login portal yet, log in via the admin:

```

http://127.0.0.1:8000/admin/

```

* Enter the superuser credentials you created with `createsuperuser`.

---

### Access the Recovery Codes page dashboard

Once logged in, go to the dashboard via:

```

http://127.0.0.1:8000/auth/recovery-codes/dashboard/

```

---

### Code Generation

##### Choose whether the code should have an expiry date

<div align="center">
  <img src="django_auth_recovery_codes/docs/images/generate_code_form.png" alt="Generate code form" width="1000">
</div>

---

### Once the code is generated

* You should see something that looks like this:

<div align="center">
  <img src="django_auth_recovery_codes/docs/images/plaintext_generated_code.png" alt="Plaintext generated code" width="1000">
</div>

* From here, you can regenerate, email, download, or delete the code.

---


### Verifying Generated Codes

* Once the codes are generated, you have the option to verify if the setup is correct.  
* This is a one-time verification test, and the form will remain until it is verified.  
* Once verified, it will no longer appear, even on a new batch generation.  
* To use, simply select a code and enter it in the form.

<div align="center">
  <img src="django_auth_recovery_codes/docs/images/verify_code.png" alt="Verify code form" width="1000">
</div>

#### Failed Test

* A failed test will look like this:

<div align="center">
  <img src="django_auth_recovery_codes/docs/images/failed_test.png" alt="Failed code verification" width="1000">
</div>

#### Successful Test

* A successful test will look like this.  
* Once the test is successful, the form will no longer be visible.

<div align="center">
  <img src="django_auth_recovery_codes/docs/images/successful_test.png" alt="Successful code verification" width="1000">
</div>

---

### Downloaded and Emailed Code

* Once a code is downloaded or emailed, it cannot be used again for the same batch.

<div align="center">
  <img src="django_auth_recovery_codes/docs/images/email_and_downloaded_code.png" alt="Downloaded or emailed code" width="1000">
</div>

---

### Invalidating or Deleting a Code

* The application allows you to invalidate or delete a code.  
* Once a code has been invalidated or deleted, it cannot be used again.  

<div align="center">
  <img src="django_auth_recovery_codes/docs/images/invalidate_or_delete_code.png" alt="Invalidate or delete code" width="1000">
</div>

---

### Viewing the Code Batch History

* You can view your code history.  
* It contains information about the generated code batch, such as the number issued and whether the codes were downloaded or emailed.  

<div align="center">
  <img src="django_auth_recovery_codes/docs/images/code_batch_history.png" alt="Code batch history" width="1000">
</div>

---


### Logout of the application

Now click the `logout` but before you do make sure to download a copy of the recovery codes, you will need this to login.
Once you logout you be redirect to the default login page, see the flag settings to see how to redirect to another page .

* You will no longer be able to access the dashboard since it is login only
* You can verify this by going to the home page

```
http://127.0.0.1:8000

```

---

### Failed Attempts and Rate Limiting

**Login Form**

<div align="center">
  <img src="django_auth_recovery_codes/docs/images/login.png" alt="2FA login form" width="1000">
</div>

**Failed Attempt Example**

* Failed login attempts are limited by the flag `DJANGO_AUTH_RECOVERY_CODES_MAX_LOGIN_ATTEMPTS`.  
* In this example, it has been set to `5`.  
* This means that after 5 failed attempts, the rate limiter activates.  
* The cooldown starts at 1 minute and increases with each subsequent failed attempt.  
* It will not exceed the cooldown threshold period (e.g., if set to `3600`, that is 1 hour).  


<div align="center">
  <img src="django_auth_recovery_codes/docs/images/incorrect_login_attempts.png" alt="Incorrect login attempt" width="1000">
</div>

---

### Successful Login

* Enter the email address you used when creating your superuser.  
* Use one of the valid 2FA recovery codes from your downloaded codes.  
* Upon success, you will be redirected to the dashboard.  
* The code you used will automatically be marked as invalid.  


---


### 2. Existing Project Setup

If you already have a Django project running, integration is simple:

1. **Install the package**

   ```bash
   pip install django_auth_recovery_codes
   ```

2. **Update `INSTALLED_APPS` in `settings.py`**

   ```python
   INSTALLED_APPS = [
       ...,
       "django_auth_recovery_codes",
       "django_q",  # required for background jobs
   ]
   ```

3. **Add a recovery key and email backend (for testing)**

   ```python
   EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
   EMAIL_FILE_PATH = BASE_DIR / "sent_emails"

   DJANGO_AUTH_RECOVERY_KEY = "add-some-key"
   ```

4. **Include URLs in your main `urls.py`**

   ```python
   from django.urls import path, include

   urlpatterns = [
       ...,
       path("", include("django_auth_recovery_codes.urls")),
   ]
   ```

5. **Run migrations**

   ```bash
   python manage.py migrate
   ```

   > ⚠️ You don’t need to run `makemigrations` for this package because it already ships with its own migrations.
   > Just running `migrate` will apply them.

6. **Start services**

   ```bash
   # Terminal 1
   python manage.py runserver

   # Terminal 2
   python manage.py qcluster
   ```

---
## Scheduling a Code Removal Using Django-Q

In this section, we walk you through how to safely remove recovery codes using Django-Q. You will learn how to generate codes and schedule their deletion, ensuring they are managed automatically and securely. Make sure this running in a separate window

```
  python manage.py qcluster

```

### Generate and Delete Codes

1. Generate your recovery codes.
2. Click the **Delete Codes** button and confirm the action.

> Once confirmed, Django-Q will schedule the codes for deletion. This means the codes will be automatically removed according to the scheduled task, rather than immediately, providing a safe and managed cleanup process.

<div align="center">
  <img src="django_auth_recovery_codes/docs/images/delete_codes.png" alt="Delete codes form" width="1000">
</div>

---

### Managing Scheduled Deletion via the Admin

Since we are logged in through the admin, we already have administrator access.

1. Open a new tab and navigate to:

   ```
   http://127.0.0.1:8000/admin/
   ```

2. Once there, click on the **Recovery codes** link.

<div align="center">
  <img src="django_auth_recovery_codes/docs/images/admin.png" alt="Admin" width="1000">
</div>

You will then see the following view:

<div align="center">
  <img src="django_auth_recovery_codes/docs/images/admin-delete-codes.png" alt="Admin delete codes" width="1000">
</div>

Select **Recovery code cleanup schedulers**:

<div align="center">
  <img src="django_auth_recovery_codes/docs/images/admin-schedule-link.png" alt="Admin schedule link" width="300">
</div>

---

### Scheduling a Delete

<div align="center">
  <img src="django_auth_recovery_codes/docs/images/admin-schedule-delete.png" alt="Admin schedule delete" width="700">
</div>

#### Quick Explanation

* **Retention days**: The number of days an expired or invalid code remains in the database before being deleted. For example, if set to 30, a code will be deleted 30 days after it expires. The default is controlled via a settings flag but can be overridden in the admin interface.

  * For testing, set this to `0` to remove codes immediately.

* **Run at**: The time the scheduler should run.

* **Schedule type**: How frequently the scheduler should run (`Once`, `Hourly`, `Daily`, `Weekly`, `Monthly`, `Quarterly`, `Yearly`).

* **Use with logger**: Records the scheduled deletion in a log file.

* **Delete empty batch**: When set to `True`, the parent batch (model) is removed if no active codes remain. When `False`, the batch will be kept.

* **Name**: A descriptive name for the scheduler.

* **Next run**: The next time the scheduler should run. This must not be earlier than the **Run at** value. It can also be left blank.

  * Note: The scheduler is idempotent. Once configured, it will follow the set rules without needing to be triggered manually. The **Next run** option simply allows you to run an additional execution if required.


Save the scheduler


### View tasks

Once Django-q is running you can view failed, queued, tasks via this section

<div align="center">
  <img src="django_auth_recovery_codes/docs/images/view_tasks.png" alt="view taske" width="300">
</div>


### Summary

## Scheduling a Code Removal Using Django-Q

In this section, we walk you through how to safely remove recovery codes using Django-Q. You will learn how to generate codes and schedule their deletion, ensuring they are managed automatically and securely.  

---

### Generate and Delete Codes

1. Generate your recovery codes.  
2. Click the **Delete Codes** button and confirm the action.  

> Once confirmed, Django-Q will schedule the codes for deletion. This means the codes will be automatically removed according to the scheduled task, rather than immediately, providing a safe and managed cleanup process.  

<div align="center">
  <img src="django_auth_recovery_codes/docs/images/delete_codes.png" alt="Delete codes form" width="1000">
</div>

---

### Managing Scheduled Deletion via the Admin

Since we are logged in through the admin, we already have administrator access.  

1. Open a new tab and navigate to:  

```

[http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

```

2. Once there, click on the **Recovery codes** link.  

<div align="center">
<img src="django_auth_recovery_codes/docs/images/admin.png" alt="Admin" width="1000">
</div>

You will then see the following view:  

<div align="center">
<img src="django_auth_recovery_codes/docs/images/admin-delete-codes.png" alt="Admin delete codes" width="1000">
</div>

Select **Recovery code cleanup schedulers**:  

<div align="center">
<img src="django_auth_recovery_codes/docs/images/admin-schedule-link.png" alt="Admin schedule link" width="300">
</div>

---

### Scheduling a Delete  

<div align="center">
<img src="django_auth_recovery_codes/docs/images/admin-schedule-delete.png" alt="Admin schedule delete" width="700">
</div>

#### Quick Explanation  

- **Retention days**: The number of days an expired or invalid code remains in the database before being deleted.  
- Example: If set to 30, a code will be deleted 30 days after it expires.  
- Default is set in your Django settings but can be overridden in the admin interface.  
- For testing, set this to `0` to remove codes immediately.  

- **Run at**: The time the scheduler should run.  

- **Schedule type**: How frequently the scheduler should run (`Once`, `Hourly`, `Daily`, `Weekly`, `Monthly`, `Quarterly`, `Yearly`).  

- **Use with logger**: Records the scheduled deletion in a log file.  

- **Delete empty batch**:  
- `True`: Removes the parent batch if no active codes remain.  
- `False`: Keeps the batch even if it is empty.  

- **Name**: A descriptive name for the scheduler.  

- **Next run**: The next time the scheduler should run. This must not be earlier than **Run at**, but can be left blank.  
- Note: The scheduler is idempotent. Once configured, it will follow the set rules without needing to be triggered manually. The **Next run** option simply allows for an additional one-off execution.  

---

## Summary


1. Generate your recovery codes.  
2. Click **Delete Codes** → Django-Q schedules the deletion.  
3. In the **Admin**, open **Recovery code cleanup schedulers**.  
4. Configure:  
- **Retention days** → how long codes stay before deletion (set `0` for immediate removal).  
- **Schedule type** → how often deletion runs.  
- **Run at / Next run** → when to start.  
- **Delete empty batch** → remove batch if no codes remain.  

✅ That’s it. Django-Q will handle the cleanup automatically. Tasks are added to a queue and picked up by workers, so in most cases the cleanup will happen very quickly. Depending on your worker setup and workload, there may be a short delay, but it will always be processed.

---

### Visual Flow

```

Generate recovery codes
│
▼
Click **Delete Codes**
│
▼
Django-Q schedules deletion
│
▼
Go to **Admin → Recovery code cleanup schedulers**
│
▼
Configure scheduler:
• Retention days
• Run at / Next run
• Schedule type
• Delete empty batch
│
▼
✅ Codes are cleaned up automatically

```

You can also run a scheduler to remove the audit reports for `Recovery Code` by using `Recovery code audit schedulers`. The audits are store in the `Recovery code Audit` model. The steps are same as the above steps.



## License
 - This package is licensed under the MIT License. See the LICENSE file for details.

## Credits
 -This library was created and maintained by Egbie Uku a.k.a EgbieAndersonUku1.


---


## Support
If you find this project helpful, you can support it:  

[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-☕-ff813f?style=for-the-badge)](https://buymeacoffee.com/egbieu)


---

