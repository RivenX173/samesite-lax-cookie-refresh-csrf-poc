# Chrome SameSite Lax Grace Period & Cookie Refresh CSRF PoC

A Proof of Concept (PoC) testing Chrome's Lax-by-default 2-minute grace period for cross-site POST requests, and investigating whether refreshing the cookie resets this security window.

## Background

This PoC was built after PortSwigger removed both a Web Security Academy lab and a theory section titled 'Bypassing SameSite Lax restrictions with newly issued cookies,' both of which covered this exact behavior. I wrote up the full investigation (and tested this across 8 versions of Chrome) on [Medium](https://rivenx173.medium.com/portswigger-said-chrome-closed-this-bypass-my-testing-says-it-didnt-1710c98263a6).

This PoC doesn't hardcode or check for any specific Chrome version; it simply tests the browser's live behavior at the time you run it. Feel free to run it against whatever version of Chrome you currently have installed.

This environment specifically tests two scenarios:

1. **The 2-Minute Grace Period:** Testing if a cross-site POST request is permitted within the first 120 seconds of a cookie's creation, when SameSite is defaulted to `Lax` by Chrome.
2. **The Cookie Refresh Hypothesis:** Testing if issuing a new value for the same cookie (refreshing it) resets the 2-minute grace period timer, or if the browser tracks the absolute creation time of the initial cookie.

## Architecture

The PoC consists of two separate lightweight Python HTTP servers, each serving a small interactive UI with multiple buttons and a "Real World Scenario Mode" toggle to simulate different attack flows:

- **Site A (`site_a.py`):** The "Attacker" site that simulates a malicious cross-site POST request.
- **Site B (`site_b.py`):** The "Target" site that issues and owns the cookie, and receives the POST request.

Both sites are designed to run locally to test Cross-Site Request Forgery (CSRF) mechanics.

## Requirements

- Python 3.x
- No external dependencies (standard library only)

## How to Run the Test

Open two separate terminal windows, then run one script in each _(use `python` or `python3` depending on your environment)_:

1. **Terminal 1 (Attacker):**

```bash
python site_a.py
```

2. **Terminal 2 (Target):**

```bash
python site_b.py
```

3. Open **Site A** in your browser at `http://127.0.0.1:8000`
4. Open **Site B** in another tab at `http://localhost:9000`
5. Start the test.

For a detailed walkthrough of every scenario and what each result means, see the full write-up on [Medium](https://rivenx173.medium.com/portswigger-said-chrome-closed-this-bypass-my-testing-says-it-didnt-1710c98263a6).

- *Note: Chrome treats `http://localhost:9000` and `http://127.0.0.1:8000` as entirely different origins, so the test isn't affected by this in any case.*
## Disclaimer

> This project is created for educational and security research purposes only.
>
> PoC by [RivenX173](https://github.com/RivenX173).
