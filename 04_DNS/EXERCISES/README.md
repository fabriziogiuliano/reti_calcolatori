# Exercise 04: who handles the mail of a domain?

**Goal:** use `dig` to find the mail servers and the name servers of a domain.

## Task

Choose a domain (for example `gmail.com`) and find:
1. its **mail servers**: which one is tried first?
2. its **authoritative name servers**: how many are there?

## What you need

- README, Section 4: `dig +short MX` and `dig +short NS`.
- The meaning of the number before an MX server (README, Section 4).

## Check

A list of mail servers, each with a number, and a list of name servers.

<details>
<summary>Solution</summary>

```bash
dig +short MX gmail.com
dig +short NS gmail.com
```
```
20 alt2.gmail-smtp-in.l.google.com.
30 alt3.gmail-smtp-in.l.google.com.
5 gmail-smtp-in.l.google.com.
10 alt1.gmail-smtp-in.l.google.com.
40 alt4.gmail-smtp-in.l.google.com.

ns1.google.com.
ns2.google.com.
ns4.google.com.
ns3.google.com.
```
1. Five mail servers: the first one tried is `gmail-smtp-in.l.google.com`, the one with the **lowest** number (5). The others are backups.
2. Four name servers: if one fails, the others answer.
</details>
