![Made with Python](https://img.shields.io/badge/Made%20with-Python-blue?logo=python)
![Security](https://img.shields.io/badge/Security-180--bit-brightgreen)
![Brute Force](https://img.shields.io/badge/Brute--force-Impractical-red)
![License](https://img.shields.io/badge/License-MIT-yellow)

# 🔐 2FA Recovery Codes

The premises of this resuable application, is that it takes any Django application and extends that application so that it can now use the 2FA recovery codes as a backup login for that application.

`django-2fa-recovery-codes` is a Django app that provides a robust system for generating, storing, and managing **2FA recovery codes**. Unlike a full two-factor authentication apps, this package focuses solely on **recovery codes**, although this is a lightweight application it is a very powerful tool, offering fine-grained control and asynchronous management for better UX and performance.

## Table of Contents

* [Introduction](#introduction)
* [Features](#features)
* [How it differs from full two-factor-auth apps](#how-it-differs-from-full-two-factor-auth-apps)
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

## Features

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

## How it Differs from Full Two-Factor Authentication Apps?

`django-2fa-recovery-codes` is designed **solely for recovery codes**, offering fine-grained control, asynchronous management, and admin-friendly batch handling.

* User UI interface
   * Dedicated login interface page to enter your email and 2FA recovery code
   * Dashboard that allows the user to:
	* Generate a batch of 2FA recovery codes (default=10 generated, configurable via settings flags) with expiry date or doesn't expiry
        * Regenerate code (Uses brute force rate limiter with a penalty that increases wait time if codes is regenerated within that time window)
        * Email, Delete or Download entire codes via the buttons
        * Invalidate or delete a code via interactive form
        * view batch histories
	
          ### Example a single recovery code batch View

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

* Focuses **exclusively on recovery codes** rather than full 2FA flows.
* Built in **asynchronous usage**
        * Built-in **asynchronous cleanup scheduler** using Django-Q for expired or invalid code, audit report with option to send the report to admin after a successful scheduler delete.
        * Uses asynchronous to send emails with the optional to use synchronous for testing or when in development configurable in `DEBUG` settings. 
	  DEBUG = True
	     * Uses synchronous (easy for development or testing) to send emails
 	  DEBUG = False
	     * use asynchronous good for production, doesn't lock the application while sending in the background

* **Admin-friendly view interface code management**, including the ability to scheduler deletion for expired or invalid codes e.g (every 2 days, etc).
* **Individual code tracking** with granular control over each code.
* Optional **logger** to track the actions of users generating recovery codes, email sent, various aspect of the models, etc.
* Optional **storage of user email** in the model for auditing purposes.
* Utilises **caching** (Redis, Memcached, or any backend) 
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
## Example Configuration for settings
```python
  * DJANGO_AUTH_RECOVERY_CODES_DEFAULT_FILE_NAME                  = "recovery_codes"
  * DJANGO_AUTH_RECOVERY_KEY                                      = "recovery-key-to-create-the-hash-and-use-for-deterministic-lookup"
  * DJANGO_AUTH_RECOVERY_CODE_AUDIT_RETENTION_DAYS                = 0
  * DJANGO_AUTH_RECOVERY_CODE_AUDIT_ENABLE_AUTO_CLEANUP           = True
  * DJANGO_AUTH_RECOVERY_CODE_PURGE_DELETE_RETENTION_DAYS         = 30
  * DJANGO_AUTH_RECOVERY_CODE_ADMIN_EMAIL_HOST_USER               = "example_email@hotmail.com"
  * DJANGO_AUTH_RECOVERY_CODE_ADMIN_EMAIL                         = "example_admin_email@hotmail.com"
  * DJANGO_AUTH_RECOVERY_CODE_ADMIN_USERNAME                      = "egibe"
  * DJANGO_AUTH_RECOVERY_CODE_PURGE_DELETE_SCHEDULER_USE_LOGGER   = False
  * DJANGO_AUTH_RECOVERY_CODE_STORE_EMAIL_LOG                     = False
  * DJANGO_AUTH_RECOVERY_CODE_REDIRECT_VIEW                       = "app name"
  * DJANGO_AUTH_RECOVERY_CODE_MAX_VISIBLE                         = 20
  * DJANGO_AUTH_RECOVERY_CODE_PER_PAGE                            = 5
  * DJANGO_AUTH_RECOVERY_CODES_MAX_LOGIN_ATTEMPTS                 = 3
  * DJANGO_AUTH_RECOVERY_CODES_AUTH_RATE_LIMITER_USE_CACHE        = True
```


## 2FA Recovery Code Generator

This app generates **2FA recovery codes** that can be used if you lose access to your authenticator app.

Each code is generated using **cryptographically secure randomness** and avoids confusing characters (e.g., `0` vs `O`, `1` vs `l`).

### Code Format

Codes are generated in the following format:

```
XXXXXX-XXXXXX-XXXXXX-XXXXXX-XXXXXX-XXXXXX
```

* **6 groups**, each with **6 characters**
* **Alphabet size:** 52 characters (`A–Z`, `a–z`, `2–9`)
* **Cryptographic randomness** (not guessable, not sequential)
* **Entropy total:** 215 bits (5.71 bits per character × 36 characters)

---

## Why It’s Secure

### Entropy

* Each character contributes **5.71 bits** (`log2(52+8?) ≈ 5.71`)
* Each group has 6 characters → 6 × 5.71 ≈ **34.26 bits per group**
* 6 groups → 6 × 34.26 ≈ **205.56 bits total**

> With 52 characters and 36-character codes, entropy is higher than AES-128 (128 bits), making brute-force attacks astronomically impractical.

### Total Combinations

* **Number of unique codes:**

$$
52^{36} \approx 3.3 \times 10^{61}
$$

---

## Brute-Force Resistance

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

### Time to Crack at Different Speeds

| Guesses per Second | Time to Crack (Years) |
| ------------------ | --------------------- |
| 1                  | 3.3 × 10^61           |
| 10^6 (1 million)   | 3.3 × 10^55           |
| 10^9 (1 billion)   | 1.05 × 10^45          |
| 10^18 (exascale)   | 1.05 × 10^36          |

* Age of the universe: ≈ 13.8 × 10^9 years
* Brute-force time: trillions of times longer than the universe's age

---

## Developer Appendix 🛠️

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

## ✅ Summary

* **215-bit recovery codes** → astronomically secure
* **≈3.3 × 10^61 combinations** → impossible to brute-force
* Even with a supercomputer, cracking a single code would take **trillions of times longer than the age of the universe**
* With **rate limiting**, brute-force becomes completely infeasible

---

## Use Cases

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

## Contributing



---

## License



---

